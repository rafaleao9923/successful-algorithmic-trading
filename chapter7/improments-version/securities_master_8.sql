-- SQLite-compatible Securities Master Database Schema
-- Version 8.0
-- Final version with all improvements and refinements

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

-- Industry Classification Table (New)
CREATE TABLE IF NOT EXISTS industry_classification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector TEXT NOT NULL,  -- Sector classification (e.g., "Technology")
    industry TEXT NOT NULL,  -- Industry classification (e.g., "Software")
    UNIQUE(sector, industry)  -- Ensure unique combinations of sector and industry
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
    sector_industry_id INTEGER,  -- Reference to the industry classification
    -- market_cap_category TEXT CHECK (market_cap_category IN ('Large Cap', 'Mid Cap', 'Small Cap', 'Micro Cap')),  -- Predefined categories
    headquarters_country_id INTEGER,  -- Reference to the country
    cik TEXT,  -- Central Index Key (for US securities)
    incorporation_country_id INTEGER,  -- Reference to the country
    fiscal_year_end TEXT,  -- Fiscal year end date
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE,
    FOREIGN KEY(sector_industry_id) REFERENCES industry_classification(id) ON DELETE RESTRICT,
    FOREIGN KEY(headquarters_country_id) REFERENCES country(id) ON DELETE RESTRICT,
    FOREIGN KEY(incorporation_country_id) REFERENCES country(id) ON DELETE RESTRICT
);

-- Bond Table (extends symbol)
CREATE TABLE IF NOT EXISTS bond (
    symbol_id INTEGER PRIMARY KEY,
    issuer TEXT,  -- Entity issuing the bond (e.g., "US Treasury")
    maturity_date TEXT,  -- Date the bond matures
    coupon_rate REAL CHECK (coupon_rate >= 0),  -- Annual interest rate
    face_value REAL CHECK (face_value > 0),  -- Face value of the bond
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- ETF Table (extends symbol)
CREATE TABLE IF NOT EXISTS etf (
    symbol_id INTEGER PRIMARY KEY,
    issuer TEXT,  -- Entity managing the ETF (e.g., "Vanguard")
    expense_ratio REAL CHECK (expense_ratio >= 0),  -- Annual management fee as a percentage
    holdings_count INTEGER CHECK (holdings_count >= 0),  -- Number of underlying holdings
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Fund Table (extends symbol)
CREATE TABLE IF NOT EXISTS fund (
    symbol_id INTEGER PRIMARY KEY,
    fund_manager TEXT,  -- Entity managing the fund
    inception_date TEXT,  -- Date the fund was launched
    expense_ratio REAL CHECK (expense_ratio >= 0),  -- Annual management fee as a percentage
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Index Table (extends symbol)
CREATE TABLE IF NOT EXISTS market_index (
    symbol_id INTEGER PRIMARY KEY,
    provider TEXT,  -- Entity providing the index (e.g., "S&P Dow Jones Indices")
    calculation_method TEXT,  -- Methodology used to calculate the index
    rebalance_frequency TEXT,  -- Frequency of rebalancing (e.g., "Quarterly")
    total_constituents INTEGER CHECK (total_constituents > 0),  -- Total number of constituents in the index
    is_price_return BOOLEAN,  -- Indicates if the index is price return
    is_total_return BOOLEAN,  -- Indicates if the index is total return
    base_value REAL CHECK (base_value > 0),  -- Base value of the index
    base_date TEXT,  -- Base date of the index
    CHECK (is_price_return = 1 OR is_total_return = 1),  -- At least one must be true
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE
);

-- Index Components Table
CREATE TABLE IF NOT EXISTS index_component (
    index_symbol_id INTEGER NOT NULL,
    component_symbol_id INTEGER NOT NULL,
    weight REAL CHECK (weight >= 0 AND weight <= 100),  -- Weight of the component in the index
    shares_outstanding INTEGER CHECK (shares_outstanding >= 0),  -- Number of shares outstanding
    free_float_factor REAL CHECK (free_float_factor >= 0 AND free_float_factor <= 1),  -- Free float factor
    is_active BOOLEAN DEFAULT TRUE,
    effective_date TEXT NOT NULL,  -- Date the component became active
    expiry_date TEXT,  -- Date the component expires
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (effective_date <= expiry_date OR expiry_date IS NULL),  -- Ensure effective_date <= expiry_date
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
    open_price REAL CHECK (open_price > 0),
    high_price REAL CHECK (high_price > 0),
    low_price REAL CHECK (low_price > 0),
    close_price REAL CHECK (close_price > 0),
    adj_close_price REAL CHECK (adj_close_price > 0),
    volume INTEGER CHECK (volume >= 0),
    turnover REAL CHECK (turnover >= 0),  -- Daily trading value
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol_id, price_date, data_vendor_id),
    FOREIGN KEY(symbol_id) REFERENCES symbol(id) ON DELETE CASCADE,
    FOREIGN KEY(data_vendor_id) REFERENCES data_vendor(id) ON DELETE RESTRICT
);

-- Audit Log Table (Enhanced)
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,  -- Name of the table being modified
    record_id INTEGER NOT NULL,  -- ID of the record being modified
    action TEXT NOT NULL,  -- Action performed (e.g., INSERT, UPDATE, DELETE)
    changed_by TEXT NOT NULL,  -- User or system that performed the action
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Timestamp of the change
    previous_value TEXT,  -- Previous value of the modified field(s)
    new_value TEXT  -- New value of the modified field(s)
);

-- Indexes for Performance Optimization
CREATE INDEX idx_daily_price_date ON daily_price(price_date);
CREATE INDEX idx_index_component_dates ON index_component(effective_date, expiry_date);

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

-- Insert initial industry classifications
INSERT INTO industry_classification (sector, industry) VALUES
('Technology', 'Software'),
('Technology', 'Hardware'),
('Financial Services', 'Banking'),
('Healthcare', 'Biotechnology');

INSERT INTO schema_version (version) VALUES ('8.0');