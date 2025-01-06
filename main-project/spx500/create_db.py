import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database(db_path='securities_master.db'):
    """Initialize the SQLite database with the required schema"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create exchange table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                abbrev TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                city TEXT,
                country TEXT,
                currency TEXT NOT NULL DEFAULT 'USD',
                timezone_offset TEXT,
                created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create data_vendor table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_vendor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                website_url TEXT,
                support_email TEXT,
                created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create symbol table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbol (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange_id INTEGER,
                ticker TEXT NOT NULL,
                instrument TEXT NOT NULL,
                name TEXT,
                sector TEXT,
                sub_industry TEXT,
                headquarter TEXT,
                date_added TEXT,
                cik TEXT,
                founded TEXT,
                currency TEXT NOT NULL DEFAULT 'USD',
                created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, exchange_id),
                FOREIGN KEY(exchange_id) REFERENCES exchange(id) ON DELETE SET NULL
            )
        ''')

        # Create daily_price table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_vendor_id INTEGER NOT NULL,
                symbol_id INTEGER NOT NULL,
                price_date TEXT NOT NULL,
                created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                adj_close_price REAL,
                volume INTEGER,
                UNIQUE(symbol_id, price_date),
                FOREIGN KEY(data_vendor_id) REFERENCES data_vendor(id) ON DELETE CASCADE,
                FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
            )
        ''')

        # Create schema_version table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert initial data
        cursor.execute("SELECT COUNT(*) FROM data_vendor")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO data_vendor (id, name) VALUES (1, 'Yahoo Finance')"
            )

        cursor.execute("SELECT COUNT(*) FROM exchange")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO exchange (abbrev, name, city, country, currency) VALUES (?, ?, ?, ?, ?)",
                [
                    ('NYSE', 'New York Stock Exchange', 'New York', 'USA', 'USD'),
                    ('NASDAQ', 'NASDAQ Stock Market', 'New York', 'USA', 'USD'),
                    ('CBOE', 'Chicago Board Options Exchange', 'Chicago', 'USA', 'USD')
                ]
            )

        cursor.execute("SELECT COUNT(*) FROM schema_version")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES ('3.0')"
            )

        conn.commit()
        logger.info(f"Successfully created database at {db_path}")

    except sqlite3.Error as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = Path('securities_master.db')
    create_database(db_path)