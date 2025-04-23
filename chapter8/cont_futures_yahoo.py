#!/usr/bin/python
# -*- coding: utf-8 -*-

# cont_futures_yahoo.py

from __future__ import print_function

import datetime
import requests
import pandas as pd
import numpy as np


def futures_rollover_weights(start_date, expiry_dates, contracts, rollover_days=5):
    """This constructs a pandas DataFrame that contains weights (between 0.0 and 1.0)
    of contract positions to hold in order to carry out a rollover of rollover_days
    prior to the expiration of the earliest contract. The matrix can then be
    'multiplied' with another DataFrame containing the settle prices of each
    contract in order to produce a continuous time series futures contract."""

    # Construct a sequence of dates beginning from the earliest contract start
    # date to the end date of the final contract
    dates = pd.date_range(start_date, expiry_dates[-1], freq='B')

    # Create the 'roll weights' DataFrame that will store the multipliers for
    # each contract (between 0.0 and 1.0)
    roll_weights = pd.DataFrame(np.zeros((len(dates), len(contracts))),
                                index=dates, columns=contracts)
    prev_date = roll_weights.index[0]

    # Loop through each contract and create the specific weightings for
    # each contract depending upon the settlement date and rollover_days
    for i, (item, ex_date) in enumerate(expiry_dates.iteritems()):
        if i < len(expiry_dates) - 1:
            roll_weights.ix[prev_date:ex_date - pd.offsets.BDay(), item] = 1
            roll_rng = pd.date_range(end=ex_date - pd.offsets.BDay(),
                                     periods=rollover_days + 1, freq='B')

            # Create a sequence of roll weights (i.e. [0.0,0.2,...,0.8,1.0]
            # and use these to adjust the weightings of each future
            decay_weights = np.linspace(0, 1, rollover_days + 1)
            roll_weights.ix[roll_rng, item] = 1 - decay_weights
            roll_weights.ix[roll_rng, expiry_dates.index[i+1]] = decay_weights
        else:
            roll_weights.ix[prev_date:, item] = 1
        prev_date = ex_date
    return roll_weights


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


if __name__ == "__main__":
    # Define the tickers for the current Front and Back (near and far) futures contracts
    # for WTI Crude, traded on NYMEX. Adjust the tickers to reflect your current near/far contracts.
    wti_near_ticker = "CL=F"
    wti_far_ticker = "CL=F"

    # Define the start and end dates for the data retrieval
    start_date = (2013, 12, 19)
    end_date = (2014, 2, 21)

    # Download the futures data from Yahoo Finance
    wti_near = get_daily_historic_data_yahoo(wti_near_ticker, start_date, end_date)
    wti_far = get_daily_historic_data_yahoo(wti_far_ticker, start_date, end_date)

    # Create the DataFrame with the settle prices of each contract
    wti = pd.DataFrame({'CLF2014': wti_near['Close'],
                        'CLG2014': wti_far['Close']}, index=wti_far.index)

    # Create the dictionary of expiry dates for each contract
    expiry_dates = pd.Series({'CLF2014': datetime.datetime(2013, 12, 19),
                             'CLG2014': datetime.datetime(2014, 2, 21)}).sort_index()

    # Obtain the rollover weighting matrix/DataFrame
    weights = futures_rollover_weights(wti_near.index[0], expiry_dates, wti.columns)

    # Construct the continuous future of the WTI CL contracts
    wti_cts = (wti * weights).sum(1).dropna()

    # Output the merged series of contract settle prices
    print(wti_cts.tail(60))
