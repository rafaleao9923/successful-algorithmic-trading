#!/usr/bin/python
# -*- coding: utf-8 -*-

# iqfeed_yahoo.py

import sys
import requests
import pandas as pd
import datetime


def get_daily_historic_data_yahoo(ticker, start_date, end_date):
    """
    Obtains data from Yahoo Finance and returns a DataFrame.

    ticker: Yahoo Finance ticker symbol, e.g. "SPY" for SPY.
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


if __name__ == "__main__":
    # Define the symbols to download
    syms = ["SPY", "IWM"]

    # Define the start and end dates for the data retrieval
    start_date = (2007, 1, 1)
    end_date = (2014, 1, 1)

    # Download each symbol to disk
    for sym in syms:
        print("Downloading symbol: %s..." % sym)

        # Download the data from Yahoo Finance
        data = get_daily_historic_data_yahoo(sym, start_date, end_date)

        # Write the data stream to disk
        data.to_csv("%s.csv" % sym)
