-- SQLite-compatible Securities Master Database Schema
-- Version 5.0
-- Enhanced to support multiple instrument types with clear distinctions

-- Country Table
CREATE TABLE IF NOT EXISTS country (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,  -- Country name (e.g., "USA", "France")
    iso_code TEXT NOT NULL UNIQUE,  -- ISO 3166-1 alpha-2 code (e.g., "US", "FR")
    currency TEXT NOT NULL DEFAULT 'USD',  -- Default currency for the country
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Asset Type Table
CREATE TABLE IF NOT EXISTS asset_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,  -- Asset type name (e.g., "Equity", "Bond", "ETF")
    description TEXT,  -- Optional description of the asset type
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Exchange Table
CREATE TABLE IF NOT EXISTS exchange (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abbrev TEXT NOT NULL UNIQUE,  -- Exchange abbreviation (e.g., "NYSE", "NASDAQ")
    name TEXT NOT NULL,  -- Full name of the exchange
    city TEXT,  -- City where the exchange is located
    country_id INTEGER NOT NULL,  -- Reference to the country
    timezone_offset TEXT,  -- Timezone offset (e.g., "-05:00" for EST)
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(country_id) REFERENCES country(id) ON DELETE CASCADE
);

-- Data Vendor Table (unchanged)
CREATE TABLE IF NOT EXISTS data_vendor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    website_url TEXT,
    support_email TEXT,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Base Symbol Table
CREATE TABLE IF NOT EXISTS symbol (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange_id INTEGER NOT NULL,
    asset_type_id INTEGER NOT NULL,  -- Reference to the asset type
    ticker TEXT NOT NULL,  -- Ticker symbol (e.g., "AAPL")
    name TEXT,  -- Full name of the asset
    isin TEXT,  -- International Securities Identification Number
    currency TEXT NOT NULL DEFAULT 'USD',
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, exchange_id),  -- Ensure unique ticker per exchange
    FOREIGN KEY(exchange_id) REFERENCES exchange(id) ON DELETE CASCADE,
    FOREIGN KEY(asset_type_id) REFERENCES asset_type(id) ON DELETE CASCADE
);

-- Stock Table (extends symbol)
CREATE TABLE IF NOT EXISTS stock (
    symbol_id INTEGER PRIMARY KEY,  -- Foreign key to symbol table
    sector TEXT,  -- Sector classification (e.g., "Technology")
    sub_industry TEXT,  -- Sub-industry classification
    headquarter TEXT,  -- Headquarters location
    date_added TEXT,  -- Date the stock was added to the exchange
    cik TEXT,  -- Central Index Key (for US securities)
    founded TEXT,  -- Year the company was founded
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Bond Table (extends symbol)
CREATE TABLE IF NOT EXISTS bond (
    symbol_id INTEGER PRIMARY KEY,  -- Foreign key to symbol table
    issuer TEXT,  -- Entity issuing the bond (e.g., "US Treasury")
    maturity_date TEXT,  -- Date the bond matures
    coupon_rate REAL,  -- Annual interest rate
    face_value REAL,  -- Face value of the bond
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- ETF Table (extends symbol)
CREATE TABLE IF NOT EXISTS etf (
    symbol_id INTEGER PRIMARY KEY,  -- Foreign key to symbol table
    issuer TEXT,  -- Entity managing the ETF (e.g., "Vanguard")
    expense_ratio REAL,  -- Annual management fee as a percentage
    holdings_count INTEGER,  -- Number of underlying holdings
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Fund Table (extends symbol)
CREATE TABLE IF NOT EXISTS fund (
    symbol_id INTEGER PRIMARY KEY,  -- Foreign key to symbol table
    fund_manager TEXT,  -- Entity managing the fund
    inception_date TEXT,  -- Date the fund was launched
    expense_ratio REAL,  -- Annual management fee as a percentage
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Index Table (extends symbol)
CREATE TABLE IF NOT EXISTS index (
    symbol_id INTEGER PRIMARY KEY,  -- Foreign key to symbol table
    provider TEXT,  -- Entity providing the index (e.g., "S&P Dow Jones Indices")
    methodology TEXT,  -- Methodology used to calculate the index
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Daily Price Table (unchanged)
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
    UNIQUE(symbol_id, price_date),  -- Ensure unique price per symbol per date
    FOREIGN KEY(data_vendor_id) REFERENCES data_vendor(id) ON DELETE CASCADE,
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Version Tracking Table (unchanged)
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial data
INSERT INTO country (name, iso_code, currency) VALUES
('United States of America', 'US', 'USD'),
('France', 'FR', 'EUR'),
('Germany', 'DE', 'EUR');

INSERT INTO asset_type (name, description) VALUES
('Equity', 'Common and preferred stocks'),
('Bond', 'Fixed-income securities'),
('ETF', 'Exchange-Traded Funds'),
('Fund', 'Mutual funds and other investment funds'),
('Warrant', 'Financial derivatives'),
('Certificate', 'Structured financial products'),
('Index', 'Market indices');

INSERT INTO exchange (abbrev, name, city, country_id) VALUES
('NYSE', 'New York Stock Exchange', 'New York', 1),
('NASDAQ', 'NASDAQ Stock Market', 'New York', 1),
('CBOE', 'Chicago Board Options Exchange', 'Chicago', 1),
('EURONEXT', 'Euronext', 'Paris', 2);

INSERT INTO data_vendor (id, name) VALUES (1, 'Yahoo Finance');

INSERT INTO schema_version (version) VALUES ('5.0');