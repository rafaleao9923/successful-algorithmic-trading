#!/usr/bin/env python3
from datetime import datetime, date
import logging
from typing import List, Tuple, Optional
import sqlite3
import requests
from pydantic import BaseModel, field_validator
from datetime import timezone

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
        if value > datetime.now():
            raise ValueError('Date cannot be in the future')
        return value

from shared_config import DB_PATH

class PriceManager:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

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

    def get_historical_data(self, ticker: str, start_date: Tuple[int, int, int] = (2000, 1, 1),
                          end_date: Tuple[int, int, int] = None) -> List[PriceData]:
        """Get historical data from Yahoo Finance"""
        if end_date is None:
            end_date = date.today().timetuple()[:3]
            
        try:
            url = self._build_yahoo_url(ticker, start_date, end_date)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            prices = []
            for line in response.text.splitlines()[1:]:
                if not line.strip():
                    continue
                parts = line.strip().split(',')
                prices.append(PriceData(
                    date=datetime.strptime(parts[0], '%Y-%m-%d'),
                    open=float(parts[1]),
                    high=float(parts[2]),
                    low=float(parts[3]),
                    close=float(parts[4]),
                    adj_close=float(parts[5]),
                    volume=int(parts[6])
                ))
            return prices
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            raise

    def _build_yahoo_url(self, ticker: str, start_date: Tuple[int, int, int],
                        end_date: Tuple[int, int, int]) -> str:
        """Build Yahoo Finance URL"""
        return (
            "https://query1.finance.yahoo.com/v7/finance/download/"
            f"{ticker}?period1={int(datetime(*start_date).timestamp())}"
            f"&period2={int(datetime(*end_date).timestamp())}"
            "&interval=1d&events=history&includeAdjustedClose=true"
        )

    def insert_prices(self, vendor_id: int, symbol_id: int, prices: List[PriceData]):
        """Insert prices into database"""
        try:
            insert_sql = """
                INSERT INTO daily_price 
                (data_vendor_id, symbol_id, price_date, created_date, last_updated_date,
                 open_price, high_price, low_price, close_price, adj_close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            now = datetime.utcnow()
            data_to_insert = [
                (
                    vendor_id, symbol_id, price.date, now, now,
                    price.open, price.high, price.low, price.close,
                    price.adj_close, price.volume
                )
                for price in prices
            ]
            self.cursor.executemany(insert_sql, data_to_insert)
            self.conn.commit()
            logger.info(f"Inserted {len(prices)} prices for symbol ID {symbol_id}")
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting prices: {e}")
            raise

if __name__ == "__main__":
    try:
        manager = PriceManager()
        tickers = manager.get_db_tickers()
        
        for symbol_id, ticker in tickers:
            logger.info(f"Processing {ticker} (ID: {symbol_id})")
            prices = manager.get_historical_data(ticker)
            manager.insert_prices(1, symbol_id, prices)
            
        logger.info("Price insertion completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        exit(1)