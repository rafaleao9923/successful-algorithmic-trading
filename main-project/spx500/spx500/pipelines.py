import sqlite3
from itemadapter import ItemAdapter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SqlitePipeline:
    def __init__(self, db_path):
        self.db_path = db_path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_path=crawler.settings.get('SQLITE_DB_PATH', 'securities_master.db')
        )

    def open_spider(self, spider):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        if spider.name == 'spx500_symbols':
            self._process_symbol(adapter)
        elif spider.name == 'spx500_prices':
            self._process_price(adapter)
            
        return item

    def _process_symbol(self, adapter):
        try:
            # Check if symbol exists
            self.cursor.execute(
                "SELECT id FROM symbol WHERE ticker = ? AND exchange_id = ?",
                (adapter['ticker'], adapter['exchange_id'])
            )
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing symbol
                update_sql = """
                    UPDATE symbol 
                    SET name = ?, sector = ?, sub_industry = ?, 
                        headquarter = ?, date_added = ?, cik = ?,
                        founded = ?, currency = ?, last_updated_date = ?
                    WHERE ticker = ? AND exchange_id = ?
                """
                self.cursor.execute(update_sql, (
                    adapter['name'], adapter['sector'], adapter['sub_industry'],
                    adapter['headquarter'], adapter['date_added'], adapter['cik'],
                    adapter['founded'], adapter['currency'], datetime.now().isoformat(),
                    adapter['ticker'], adapter['exchange_id']
                ))
            else:
                # Insert new symbol
                insert_sql = """
                    INSERT INTO symbol 
                    (exchange_id, ticker, instrument, name, sector, sub_industry,
                    headquarter, date_added, cik, founded, currency,
                    created_date, last_updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                now = datetime.now().isoformat()
                self.cursor.execute(insert_sql, (
                    adapter['exchange_id'], adapter['ticker'], adapter['instrument'],
                    adapter['name'], adapter['sector'], adapter['sub_industry'],
                    adapter['headquarter'], adapter['date_added'], adapter['cik'],
                    adapter['founded'], adapter['currency'], now, now
                ))
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error processing symbol {adapter.get('ticker')}: {e}")
            raise

    def _process_price(self, adapter):
        try:
            # Use INSERT OR REPLACE for price data
            upsert_sql = """
                INSERT OR REPLACE INTO daily_price 
                (data_vendor_id, symbol_id, price_date, created_date,
                last_updated_date, open_price, high_price, low_price,
                close_price, adj_close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.cursor.execute(upsert_sql, (
                adapter['data_vendor_id'], adapter['symbol_id'],
                adapter['price_date'], adapter['created_date'],
                adapter['last_updated_date'], adapter['open_price'],
                adapter['high_price'], adapter['low_price'],
                adapter['close_price'], adapter['adj_close_price'],
                adapter['volume']
            ))
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error processing price for symbol_id {adapter.get('symbol_id')}: {e}")
            raise