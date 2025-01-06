-- SQLite-compatible Securities Master Database Schema
-- Version 3.0
-- Simplified for SQLite compatibility
-- sqlite3 securities_master.db < securities_master.sql

-- Exchange Table
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
);

-- Data Vendor Table
CREATE TABLE IF NOT EXISTS data_vendor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    website_url TEXT,
    support_email TEXT,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Symbol Table
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
);

-- Daily Price Table
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
);

-- Version Tracking Table
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial data vendor
INSERT INTO data_vendor (id, name) VALUES (1, 'Yahoo Finance');

-- Insert exchange data
INSERT INTO exchange (abbrev, name, city, country, currency) VALUES
('NYSE', 'New York Stock Exchange', 'New York', 'USA', 'USD'),
('NASDAQ', 'NASDAQ Stock Market', 'New York', 'USA', 'USD'),
('CBOE', 'Chicago Board Options Exchange', 'Chicago', 'USA', 'USD');

-- Insert initial version
INSERT INTO schema_version (version) VALUES ('3.0');