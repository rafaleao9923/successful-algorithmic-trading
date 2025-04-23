#!/usr/bin/python
# -*- coding: utf-8 -*-

# quandl_data_yahoo.py

import sys
import requests
import pandas as pd
import datetime
import os


def construct_futures_symbols(symbol, start_year=2010, end_year=2014):
    """
    Constructs a list of futures contract codes 
    for a particular symbol and timeframe.
    """
    futures = []
    # March, June, September and 
    # December delivery codes
    months = 'HMUZ' 
    for y in range(start_year, end_year + 1):
        for m in months:
            futures.append("%s%s%s" % (symbol, m, y))
    return futures


def get_daily_historic_data_yahoo(ticker, start_date, end_date):
    """
    Obtains data from Yahoo Finance and returns a DataFrame.

    ticker: Yahoo Finance ticker symbol, e.g. "CL=F" for Crude Oil.
    start_date: Start date in (YYYY, M, D) format.
    end_date: End date in (YYYY, M, D) format.
    """
    ticker_tup = (
        ticker, start_date[1] - 1, start_date[2],
        start_date[0], end_date[1] - 1, end_date[2],
        end_date[0]
    )
    yahoo_url = "http://ichart.finance.yahoo.com/table.csv"
    yahoo_url += "?s=%s&a=%s&b=%s&c=%s&d=%s&e=%s&f=%s"
    yahoo_url = yahoo_url % ticker_tup

    try:
        yf_data = requests.get(yahoo_url).text.split("\n")[1:-1]
        prices = []
        for y in yf_data:
            p = y.strip().split(',')
            prices.append(
                (datetime.datetime.strptime(p[0], '%Y-%m-%d'),
                 p[1], p[2], p[3], p[4], p[5], p[6])
            )
        df = pd.DataFrame(prices, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'])
        df.set_index('Date', inplace=True)
        return df
    except Exception as e:
        print("Could not download Yahoo data: %s" % e)
        return pd.DataFrame()


def download_historical_contracts(symbol, dl_dir, start_year=2010, end_year=2014):
    """
    Downloads all futures contracts for a specified symbol
    between a start_year and an end_year.
    """
    contracts = construct_futures_symbols(symbol, start_year, end_year)
    for c in contracts:
        print("Downloading contract: %s" % c)
        data = get_daily_historic_data_yahoo(c, (start_year, 1, 1), (end_year, 12, 31))
        if not data.empty:
            # Ensure the directory exists
            os.makedirs(dl_dir, exist_ok=True)
            # Write the data to a CSV file
            data.to_csv(os.path.join(dl_dir, "%s.csv" % c))


if __name__ == "__main__":
    symbol = 'ES'

    # Make sure you've created this 
    # relative directory beforehand
    dl_dir = 'quandl/futures/ES'

    # Create the start and end years
    start_year = 2010
    end_year = 2014

    # Download the contracts into the directory
    download_historical_contracts(symbol, dl_dir, start_year, end_year)

    # Open up a single contract via read_csv 
    # and plot the settle price
    es = pd.read_csv(os.path.join(dl_dir, "ESH2010.csv"), index_col="Date")
    es["Close"].plot()
    import matplotlib.pyplot as plt
    plt.show()
