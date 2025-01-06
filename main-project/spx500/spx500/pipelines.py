import sqlite3
from itemadapter import ItemAdapter
from spx500.items import SymbolItem, PriceItem, ExchangeItem, DataVendorItem
from datetime import datetime

class SqlitePipeline:
    def __init__(self):
        self.conn = None
        
    def open_spider(self, spider):
        self.conn = sqlite3.connect('spx500.db')
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange
            (id INTEGER PRIMARY KEY AUTOINCREMENT, abbrev TEXT NOT NULL UNIQUE, 
            name TEXT NOT NULL, city TEXT, country TEXT, currency TEXT NOT NULL DEFAULT 'USD', 
            timezone_offset TEXT, created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, 
            last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_vendor
            (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, 
            website_url TEXT, support_email TEXT, 
            created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, 
            last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbol
            (id INTEGER PRIMARY KEY AUTOINCREMENT, exchange_id INTEGER, 
            ticker TEXT NOT NULL, instrument TEXT NOT NULL, name TEXT, 
            sector TEXT, sub_industry TEXT, headquarter TEXT, date_added TEXT, 
            cik TEXT, founded TEXT, currency TEXT NOT NULL DEFAULT 'USD', 
            created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, 
            last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, 
            UNIQUE(ticker, exchange_id), 
            FOREIGN KEY(exchange_id) REFERENCES exchange(id) ON DELETE SET NULL)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_price
            (id INTEGER PRIMARY KEY AUTOINCREMENT, data_vendor_id INTEGER NOT NULL, 
            symbol_id INTEGER NOT NULL, price_date TEXT NOT NULL, 
            created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, 
            last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, 
            open_price REAL, high_price REAL, low_price REAL, close_price REAL, 
            adj_close_price REAL, volume INTEGER, 
            UNIQUE(symbol_id, price_date), 
            FOREIGN KEY(data_vendor_id) REFERENCES data_vendor(id) ON DELETE CASCADE, 
            FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE)
        ''')
        
        # Reset sequence if symbol table is empty
        self.reset_symbol_sequence_if_empty()

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def reset_symbol_sequence_if_empty(self):
        """Reset the SQLite sequence for symbol table if it's empty"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM symbol")
            count = self.cursor.fetchone()[0]
            if count == 0:
                self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='symbol'")
                self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to reset sequence: {e}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        try:
            if isinstance(item, SymbolItem):
                self.handle_symbol_item(adapter)
            elif isinstance(item, PriceItem):
                self.handle_price_item(adapter)
            elif isinstance(item, ExchangeItem):
                self.handle_exchange_item(adapter)
            elif isinstance(item, DataVendorItem):
                self.handle_data_vendor_item(adapter)
                
            self.conn.commit()
            return item
            
        except sqlite3.Error as e:
            self.conn.rollback()
            raise Exception(f"Database error processing item: {e}")

    def handle_symbol_item(self, adapter):
        """Handle symbol items with duplicate checking"""
        # Check for existing symbol
        self.cursor.execute('''
            SELECT ticker, name, sector, sub_industry, headquarter, 
                date_added, cik, founded, currency
            FROM symbol 
            WHERE ticker = ? AND exchange_id = ?
        ''', (adapter['ticker'], adapter['exchange_id']))
        
        existing = self.cursor.fetchone()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing:
            # Compare current values with existing
            current_values = (
                adapter['name'],
                adapter['sector'],
                adapter['sub_industry'],
                adapter['headquarter'],
                adapter['date_added'],
                adapter['cik'],
                adapter['founded'],
                adapter['currency']
            )
            
            if current_values != existing[1:]:
                # Update if values differ
                self.cursor.execute('''
                    UPDATE symbol 
                    SET name = ?, sector = ?, sub_industry = ?, 
                        headquarter = ?, date_added = ?, cik = ?, 
                        founded = ?, currency = ?, last_updated_date = ?
                    WHERE ticker = ? AND exchange_id = ?
                ''', (
                    *current_values,
                    now,
                    adapter['ticker'],
                    adapter['exchange_id']
                ))
        else:
            # Insert new symbol
            self.cursor.execute('''
                INSERT INTO symbol (
                    exchange_id, ticker, instrument, name, sector, 
                    sub_industry, headquarter, date_added, cik, founded, 
                    currency, created_date, last_updated_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adapter['exchange_id'],
                adapter['ticker'],
                adapter['instrument'],
                adapter['name'],
                adapter['sector'],
                adapter['sub_industry'],
                adapter['headquarter'],
                adapter['date_added'],
                adapter['cik'],
                adapter['founded'],
                adapter['currency'],
                now,
                now
            ))

    def handle_price_item(self, adapter):
        """Handle price items with duplicate checking"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO daily_price (
                data_vendor_id, symbol_id, price_date, created_date, 
                last_updated_date, open_price, high_price, low_price, 
                close_price, adj_close_price, volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            adapter['data_vendor_id'],
            adapter['symbol_id'],
            adapter['price_date'],
            adapter['created_date'],
            adapter['last_updated_date'],
            adapter['open_price'],
            adapter['high_price'],
            adapter['low_price'],
            adapter['close_price'],
            adapter['adj_close_price'],
            adapter['volume']
        ))

    def handle_exchange_item(self, adapter):
        """Handle exchange items with duplicate checking"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO exchange (
                abbrev, name, city, country, currency, timezone_offset, 
                created_date, last_updated_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            adapter['abbrev'],
            adapter['name'],
            adapter['city'],
            adapter['country'],
            adapter['currency'],
            adapter['timezone_offset'],
            adapter['created_date'],
            adapter['last_updated_date']
        ))

    def handle_data_vendor_item(self, adapter):
        """Handle data vendor items with duplicate checking"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO data_vendor (
                name, website_url, support_email, created_date, last_updated_date
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            adapter['name'],
            adapter['website_url'],
            adapter['support_email'],
            adapter['created_date'],
            adapter['last_updated_date']
        ))