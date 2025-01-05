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

    def get_exchange_id(self, exchange_abbrev: str) -> int:
        """Get exchange ID from abbreviation"""
        try:
            self.cursor.execute("SELECT id FROM exchange WHERE abbrev = ?", (exchange_abbrev,))
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting exchange ID: {e}")
            return None
        
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
                href = tds[0].select('a')[0].get('href', '')
                
                # Extract exchange from URL
                if 'nasdaq.com' in href.lower():
                    exchange = 'NASDAQ'
                elif 'cboe.com' in href.lower():
                    exchange = 'CBOE'
                elif 'nyse.com' in href.lower():
                    exchange = 'XNYS' if ':XNYS' in href else 'NYSE'
                else:
                    exchange = 'NYSE'  # Default
                    
                exchange_id = self.get_exchange_id(exchange)

                symbols.append((
                    exchange_id,
                    tds[0].select('a')[0].text.strip(),  # Ticker
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
    """Insert or update symbols in database"""
    try:
        now = datetime.now(timezone.utc)
        
        # Prepare SQL for checking existing records
        check_sql = """
            SELECT ticker, name, sector, sub_industry, headquarter, 
                   date_added, cik, founded, currency
            FROM symbol 
            WHERE ticker = ? AND exchange_id = ?
        """
        
        # Prepare update SQL
        update_sql = """
            UPDATE symbol 
            SET name = ?, 
                sector = ?, 
                sub_industry = ?, 
                headquarter = ?,
                date_added = ?,
                cik = ?,
                founded = ?,
                currency = ?,
                last_updated_date = ?
            WHERE ticker = ? AND exchange_id = ?
        """
        
        # Prepare insert SQL
        insert_sql = """
            INSERT INTO symbol 
            (exchange_id, ticker, instrument, name, sector, sub_industry, 
             headquarter, date_added, cik, founded, currency, created_date, last_updated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        updates = 0
        inserts = 0
        
        for symbol in symbols:
            exchange_id, ticker = symbol[0], symbol[1]
            
            # Check if symbol exists
            self.cursor.execute(check_sql, (ticker, exchange_id))
            existing = self.cursor.fetchone()
            
            if existing:
                # Compare relevant fields to see if an update is needed
                current_values = symbol[4:11]  # Slice of values to compare (name through currency)
                existing_values = tuple(existing)[0:7]  # Corresponding values from existing record
                
                if current_values != existing_values:
                    # Update if there are differences
                    update_values = list(symbol[4:11])  # name through currency
                    update_values.append(now)  # last_updated_date
                    update_values.extend([ticker, exchange_id])  # WHERE clause values
                    self.cursor.execute(update_sql, update_values)
                    updates += 1
            else:
                # Insert new record
                insert_values = list(symbol)
                insert_values.extend([now, now])  # created_date and last_updated_date
                self.cursor.execute(insert_sql, insert_values)
                inserts += 1
        
        self.conn.commit()
        logger.info(f"Symbols processed: {len(symbols)} - Updated: {updates}, Inserted: {inserts}")
        
    except sqlite3.Error as e:
        self.conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        self.conn.rollback()
        logger.error(f"Error processing symbols: {e}")
        raise

if __name__ == "__main__":
    try:
        manager = SymbolManager()
        symbols = manager.get_sp500_symbols()
        manager.insert_symbols(symbols)
    except Exception as e:
        logger.error(f"Script failed: {e}")
        exit(1)