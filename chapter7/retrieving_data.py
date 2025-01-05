#!/usr/bin/env python3
import sys
import logging
import sqlite3
import pandas as pd
from typing import Optional  # Add this line
from pydantic import BaseModel, field_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from shared_config import DB_PATH

class DataRetriever:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_historical_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Retrieve historical data for a specific ticker"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT dp.price_date, dp.open_price, dp.high_price, dp.low_price, 
                           dp.close_price, dp.adj_close_price, dp.volume
                    FROM symbol AS sym
                    INNER JOIN daily_price AS dp
                    ON dp.symbol_id = sym.id
                    WHERE sym.ticker = ?
                    ORDER BY dp.price_date ASC;
                """
                return pd.read_sql_query(query, conn, params=(ticker,), index_col='price_date')
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving data for {ticker}: {e}")
            return None

class DataRequest(BaseModel):
    ticker: str
    
    @field_validator('ticker')
    def validate_ticker(cls, value):
        if not value.isalpha():
            raise ValueError('Ticker must contain only letters')
        return value.upper()

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print('Usage: python retrieving_data.py TICKER')
            sys.exit(1)
            
        request = DataRequest(ticker=sys.argv[1])
        retriever = DataRetriever()
        
        data = retriever.get_historical_data(request.ticker)
        if data is not None:
            print(data.tail())
            logger.info(f"Successfully retrieved data for {request.ticker}")
        else:
            logger.error(f"Failed to retrieve data for {request.ticker}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)