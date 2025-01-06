# Successful Algorithmic Trading Project

This repository contains the code and resources for implementing various algorithmic trading strategies and analysis tools. The project is organized into chapters, each focusing on specific aspects of algorithmic trading.

## Project Setup and Execution with Docker

### 1. Prerequisites
- Docker installed and running
- Python 3.8 or higher (for running scripts outside container)
- Required Python packages:
  ```bash
  pip install requests beautifulsoup4 pandas pydantic
  ```

### 2. Database Setup
1. Copy the schema file to the container:
   ```bash
   docker cp chapter7/securities_master.sql sqlite3:/tmp/
   ```
2. Create the SQLite database and set permission:
   ```bash
   docker exec sqlite3 sh -c "sqlite3 /data/db/securities_master.db < /tmp/securities_master.sql"
   sudo chmod 666 {Docker_sqlite3}/sqlite3/database/securities_master.db
   ```

*Alternative approaches:*
- Using absolute path (if chapter7 is accessible):
  ```bash
  docker exec sqlite3 sh -c "sqlite3 /data/db/securities_master.db < /data/db/../chapter7/securities_master.sql"
  ```

3. Update new data if needed:
   ```bash
   docker exec -it sqlite3 sqlite3 /data/db/securities_master.db
   DELETE FROM symbol;
   ```

### 3. Running the Data Pipeline
1. Insert S&P500 symbols:
   ```bash
   python chapter7/insert_symbols.py
   ```
2. Insert price data:
   ```bash
   python chapter7/price_insert.py
   ```

### 4. Querying Data
1. Retrieve data for a specific ticker:
   ```bash
   python chapter7/retrieving_data.py AAPL
   ```

### 5. Verifying Results
1. Check the database contents:
   ```bash
   docker exec sqlite3 sqlite3 /data/db/securities_master.db
   ```
   Run SQL queries to verify data:
   ```sql
   .tables
   SELECT COUNT(*) FROM symbol;
   SELECT COUNT(*) FROM daily_price;
   ```

## Project Structure

### Chapter 7: Data Management
- `insert_symbols.py`: Insert S&P500 symbols into database
- `price_insert.py`: Insert historical price data
- `retrieving_data.py`: Query and retrieve data
- `securities_master.sql`: Database schema
- `changelog.md`: Version history and changes

### Chapter 8: Market Data Integration and Futures
- `cont_futures.py`: 
  - Implements continuous futures contract construction
  - Creates rollover weight matrices for transitioning between contracts
  - Handles contract expiration and rollover periods
  - Example implementation using WTI Crude futures
  - Supports customizable rollover days and contract transitions

- `iqfeed.py`:
  - Provides socket-based connection to IQFeed data service
  - Implements buffered data reading from socket connection
  - Handles historical data requests for multiple symbols
  - Supports customizable data formats and time periods
  - Saves downloaded data to CSV files

- `quandl_data.py`:
  - Downloads futures contract data from Quandl API
  - Constructs futures contract symbols for different timeframes
  - Supports bulk downloading of historical contracts
  - Includes data visualization capabilities
  - Handles contract code generation for various delivery months

## Testing Instructions
1. Verify symbol insertion:
   ```bash
   python chapter7/insert_symbols.py
   docker exec sqlite3 sqlite3 /data/db/securities_master.db "SELECT COUNT(*) FROM symbol;"
   ```
2. Verify price data insertion:
   ```bash
   python chapter7/price_insert.py
   docker exec sqlite3 sqlite3 /data/db/securities_master.db "SELECT COUNT(*) FROM daily_price;"
   ```
3. Test data retrieval:
   ```bash
   python chapter7/retrieving_data.py AAPL
   ```

## Troubleshooting
- If you encounter connection issues, ensure the Docker container is running
- Check logs for any errors during execution
- Verify internet connection for data downloads
- Ensure all required packages are installed

## Documentation
For more detailed information about specific components:
- Refer to the docstrings in each Python file
- Check the `sat-ebook-20150618.pdf` for theoretical background
- Review the `prompts.txt` for additional context