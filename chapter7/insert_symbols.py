#!/usr/bin/env python3
from typing import List, Tuple
from datetime import datetime, timezone
import logging
import sqlite3
from bs4 import BeautifulSoup
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from shared_config import DB_PATH

class SymbolManager:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def get_sp500_symbols(self) -> List[Tuple]:
        """Fetch and parse S&P 500 symbols from Wikipedia"""
        try:
            now = datetime.utcnow()
            response = requests.get(
                "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            symbolslist = soup.select('table.wikitable')[0].select('tr')[1:]
            
            symbols = []
            for symbol in symbolslist:
                tds = symbol.select('td')
                symbols.append((
                    tds[0].select('a')[0].text.strip(),  # Ticker
                    tds[0].select('a')[0].get('href', '').split('quote/')[1].split(':')[0],  # Ticker
                    'stock',
                    tds[1].select('a')[0].text.strip(),  # Name
                    tds[2].text.strip(),  # Sector
                    tds[3].text.strip(),  # Sub-Industry
                    tds[4].text.strip(),  # Headquaters
                    tds[5].text.strip(),  # Date added
                    tds[6].text.strip(),  # CIK
                    tds[7].text.strip(),  # Founded
                    'USD', now, now
                ))
            return symbols
        except Exception as e:
            logger.error(f"Error fetching S&P500 symbols: {e}")
            raise

    def insert_symbols(self, symbols: List[Tuple]):
        """Insert symbols into database"""
        try:
            # Add debug logging here
            for symbol in symbols:
                logger.info(f"Attempting to insert symbol: {symbol}")
                logger.info(f"Types of values: {[type(x) for x in symbol]}")

            insert_sql = """
                INSERT INTO symbol 
                (ticker, instrument, name, sector, currency, created_date, last_updated_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.executemany(insert_sql, symbols)
            self.conn.commit()
            logger.info(f"Successfully inserted {len(symbols)} symbols")
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting symbols: {e}")
            raise

if __name__ == "__main__":
    try:
        manager = SymbolManager()
        symbols = manager.get_sp500_symbols()
        manager.insert_symbols(symbols)
    except Exception as e:
        logger.error(f"Script failed: {e}")
        exit(1)