#!/usr/bin/env python3
from datetime import datetime, date, timezone, timedelta
import logging
from typing import List, Tuple, Optional
import sqlite3
import requests
import random
import time
from json import loads
from pydantic import BaseModel, field_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceData(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int

    @field_validator('date')
    def validate_date(cls, value):
        if value > datetime.now(timezone.utc):
            raise ValueError('Date cannot be in the future')
        return value

from shared_config import DB_PATH

class PriceManager:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://finance.yahoo.com',
            'Origin': 'https://finance.yahoo.com',
        }

    def __del__(self):
        self.conn.close()

    def get_db_tickers(self) -> List[Tuple[int, str]]:
        """Get list of tickers from database"""
        try:
            self.cursor.execute("SELECT id, ticker FROM symbol")
            return [(row['id'], row['ticker']) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching tickers: {e}")
            raise

    def get_historical_data(self, ticker: str, start_date: Tuple[int, int, int] = (1900, 1, 1),
                          end_date: Tuple[int, int, int] = None) -> List[PriceData]:
        """Get historical data from Yahoo Finance"""
        if end_date is None:
            end_date = date.today().timetuple()[:3]
            
        try:
            ticker = ticker.replace('.', '-') if '.' in ticker else ticker

            print(f"Fetching data for {ticker}")
            params = {
                'events': 'capitalGain|div|split',
                'formatted': 'true',
                'includeAdjustedClose': 'true',
                'interval': '1d',
                'period1': str(int(datetime(*start_date, tzinfo=timezone.utc).timestamp())),
                'period2': str(int(datetime(*end_date, tzinfo=timezone.utc).timestamp())),
                'symbol': ticker,
                'userYfid': 'true',
                'lang': 'en-US',
                'region': 'US',
            }

            time.sleep(random.uniform(1.0, 3.0))

            response = requests.get(
                f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}',
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = loads(response.text)
            result = data['chart']['result'][0]
            quote = result['indicators']['quote'][0]
            
            prices = []
            timestamps = result['timestamp']
            opens = quote['open']
            highs = quote['high']
            lows = quote['low']
            closes = quote['close']
            volumes = quote['volume']
            adj_closes = result['indicators']['adjclose'][0]['adjclose']

            for i in range(len(timestamps)):
                # Skip if any required value is None
                if any(x[i] is None for x in [opens, highs, lows, closes, volumes, adj_closes]):
                    continue
                    
                prices.append(PriceData(
                    date=datetime.fromtimestamp(timestamps[i], tz=timezone.utc),
                    open=opens[i],
                    high=highs[i],
                    low=lows[i],
                    close=closes[i],
                    adj_close=adj_closes[i],
                    volume=int(volumes[i])
                ))
            return prices
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            raise

    def insert_prices(self, vendor_id: int, symbol_id: int, prices: List[PriceData]):
        """Insert or update prices in database"""
        try:
            # First, prepare the data
            now = datetime.now(timezone.utc)
            data_to_insert = [
                (
                    vendor_id, symbol_id, price.date, now, now,
                    price.open, price.high, price.low, price.close,
                    price.adj_close, price.volume
                )
                for price in prices
            ]
            
            # Use INSERT OR REPLACE (upsert) with a unique constraint on symbol_id and price_date
            upsert_sql = """
                INSERT OR REPLACE INTO daily_price 
                (data_vendor_id, symbol_id, price_date, created_date, last_updated_date,
                open_price, high_price, low_price, close_price, adj_close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Execute the upsert
            self.cursor.executemany(upsert_sql, data_to_insert)
            self.conn.commit()
            logger.info(f"Upserted {len(prices)} prices for symbol ID {symbol_id}")
            
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error upserting prices: {e}")
            raise

if __name__ == "__main__":
    try:
        manager = PriceManager()
        tickers = manager.get_db_tickers()
        
        for symbol_id, ticker in tickers:
            logger.info(f"Processing {ticker} (ID: {symbol_id})")
            start_date = datetime.now() - timedelta(days=1)
            prices = manager.get_historical_data(ticker, start_date=(start_date.year, start_date.month, start_date.day))
            manager.insert_prices(1, symbol_id, prices)
            
        logger.info("Price insertion completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        exit(1)