-- SQLite-compatible Securities Master Database Schema
-- Version 6.0
-- Final version with all improvements

-- Country Table
CREATE TABLE IF NOT EXISTS country (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,  -- Country name (e.g., "USA", "France")
    iso_code TEXT NOT NULL UNIQUE,  -- ISO 3166-1 alpha-2 code (e.g., "US", "FR")
    continent TEXT,  -- Added for geographical grouping
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Currency Table
CREATE TABLE IF NOT EXISTS currency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,  -- ISO 4217 code (e.g., "USD", "EUR")
    name TEXT NOT NULL,
    symbol TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Asset Type Table
CREATE TABLE IF NOT EXISTS asset_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,  -- Asset type name (e.g., "Equity", "Bond", "ETF")
    description TEXT,  -- Optional description of the asset type
    is_composite BOOLEAN DEFAULT FALSE,  -- Indicates if it can have components (like indices)
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Exchange Table
CREATE TABLE IF NOT EXISTS exchange (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abbrev TEXT NOT NULL UNIQUE,  -- Exchange abbreviation (e.g., "NYSE", "NASDAQ")
    name TEXT NOT NULL,  -- Full name of the exchange
    country_id INTEGER NOT NULL,  -- Reference to the country
    city TEXT,  -- City where the exchange is located
    timezone TEXT,  -- Timezone of the exchange
    operating_mic TEXT,  -- Market Identifier Code
    is_active BOOLEAN DEFAULT TRUE,
    website TEXT,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(country_id) REFERENCES country(id) ON DELETE RESTRICT
);

-- Exchange Asset Types (Junction Table)
CREATE TABLE IF NOT EXISTS exchange_asset_types (
    exchange_id INTEGER NOT NULL,
    asset_type_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (exchange_id, asset_type_id),
    FOREIGN KEY(exchange_id) REFERENCES exchange(id) ON DELETE CASCADE,
    FOREIGN KEY(asset_type_id) REFERENCES asset_type(id) ON DELETE CASCADE
);

-- Base Symbol Table
CREATE TABLE IF NOT EXISTS symbol (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange_id INTEGER NOT NULL,
    asset_type_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,  -- Ticker symbol (e.g., "AAPL")
    name TEXT,  -- Full name of the asset
    isin TEXT,  -- International Securities Identification Number
    currency_id INTEGER NOT NULL,  -- Reference to the currency
    is_active BOOLEAN DEFAULT TRUE,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, exchange_id),  -- Ensure unique ticker per exchange
    FOREIGN KEY(exchange_id) REFERENCES exchange(id) ON DELETE RESTRICT,
    FOREIGN KEY(asset_type_id) REFERENCES asset_type(id) ON DELETE RESTRICT,
    FOREIGN KEY(currency_id) REFERENCES currency(id) ON DELETE RESTRICT
);

-- Equity Table (extends symbol)
CREATE TABLE IF NOT EXISTS equity (
    symbol_id INTEGER PRIMARY KEY,
    sector TEXT,  -- Sector classification (e.g., "Technology")
    industry TEXT,  -- Industry classification
    market_cap_category TEXT,  -- e.g., Large Cap, Mid Cap, Small Cap
    headquarters_country_id INTEGER,  -- Reference to the country
    cik TEXT,  -- Central Index Key (for US securities)
    incorporation_country_id INTEGER,  -- Reference to the country
    fiscal_year_end TEXT,  -- Fiscal year end date
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE,
    FOREIGN KEY(headquarters_country_id) REFERENCES country(id) ON DELETE RESTRICT,
    FOREIGN KEY(incorporation_country_id) REFERENCES country(id) ON DELETE RESTRICT
);

-- Bond Table (extends symbol)
CREATE TABLE IF NOT EXISTS bond (
    symbol_id INTEGER PRIMARY KEY,
    issuer TEXT,  -- Entity issuing the bond (e.g., "US Treasury")
    maturity_date TEXT,  -- Date the bond matures
    coupon_rate REAL,  -- Annual interest rate
    face_value REAL,  -- Face value of the bond
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- ETF Table (extends symbol)
CREATE TABLE IF NOT EXISTS etf (
    symbol_id INTEGER PRIMARY KEY,
    issuer TEXT,  -- Entity managing the ETF (e.g., "Vanguard")
    expense_ratio REAL,  -- Annual management fee as a percentage
    holdings_count INTEGER,  -- Number of underlying holdings
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Fund Table (extends symbol)
CREATE TABLE IF NOT EXISTS fund (
    symbol_id INTEGER PRIMARY KEY,
    fund_manager TEXT,  -- Entity managing the fund
    inception_date TEXT,  -- Date the fund was launched
    expense_ratio REAL,  -- Annual management fee as a percentage
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Index Table (extends symbol)
CREATE TABLE IF NOT EXISTS market_index (
    symbol_id INTEGER PRIMARY KEY,
    provider TEXT,  -- Entity providing the index (e.g., "S&P Dow Jones Indices")
    calculation_method TEXT,  -- Methodology used to calculate the index
    rebalance_frequency TEXT,  -- Frequency of rebalancing (e.g., "Quarterly")
    total_constituents INTEGER,  -- Total number of constituents in the index
    is_price_return BOOLEAN,  -- Indicates if the index is price return
    is_total_return BOOLEAN,  -- Indicates if the index is total return
    base_value REAL,  -- Base value of the index
    base_date TEXT,  -- Base date of the index
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Index Components Table
CREATE TABLE IF NOT EXISTS index_component (
    index_symbol_id INTEGER NOT NULL,
    component_symbol_id INTEGER NOT NULL,
    weight REAL,  -- Weight of the component in the index
    shares_outstanding INTEGER,  -- Number of shares outstanding
    free_float_factor REAL,  -- Free float factor
    is_active BOOLEAN DEFAULT TRUE,
    effective_date TEXT NOT NULL,  -- Date the component became active
    expiry_date TEXT,  -- Date the component expires
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (index_symbol_id, component_symbol_id, effective_date),
    FOREIGN KEY(index_symbol_id) REFERENCES market_index(symbol_id) ON DELETE CASCADE,
    FOREIGN KEY(component_symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Daily Price Table
CREATE TABLE IF NOT EXISTS daily_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL,
    data_vendor_id INTEGER NOT NULL,
    price_date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    adj_close_price REAL,
    volume INTEGER,
    turnover REAL,  -- Daily trading value
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol_id, price_date, data_vendor_id),
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE,
    FOREIGN KEY(data_vendor_id) REFERENCES data_vendor(id) ON DELETE RESTRICT
);

-- Version Tracking Table
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial data
INSERT INTO country (name, iso_code, continent) VALUES
('United States of America', 'US', 'North America'),
('France', 'FR', 'Europe'),
('Germany', 'DE', 'Europe');

INSERT INTO currency (code, name, symbol) VALUES
('USD', 'US Dollar', '$'),
('EUR', 'Euro', '€'),
('GBP', 'British Pound', '£');

INSERT INTO asset_type (name, description, is_composite) VALUES
('Equity', 'Common and preferred stocks', FALSE),
('Bond', 'Fixed-income securities', FALSE),
('ETF', 'Exchange-Traded Funds', TRUE),
('Market Index', 'Market indices', TRUE),
('Fund', 'Mutual funds and other investment funds', TRUE);

INSERT INTO exchange (abbrev, name, country_id, city, timezone, operating_mic) VALUES
('NYSE', 'New York Stock Exchange', 1, 'New York', 'America/New_York', 'XNYS'),
('NASDAQ', 'NASDAQ Stock Market', 1, 'New York', 'America/New_York', 'XNAS'),
('EURONEXT', 'Euronext', 2, 'Paris', 'Europe/Paris', 'XPAR');

INSERT INTO exchange_asset_types (exchange_id, asset_type_id) VALUES
(1, 1),  -- NYSE supports equities
(1, 2),  -- NYSE supports bonds
(1, 3),  -- NYSE supports ETFs
(2, 1),  -- NASDAQ supports equities
(2, 3),  -- NASDAQ supports ETFs
(3, 1),  -- Euronext supports equities
(3, 2),  -- Euronext supports bonds
(3, 3),  -- Euronext supports ETFs
(3, 5);  -- Euronext supports funds

INSERT INTO schema_version (version) VALUES ('6.0');