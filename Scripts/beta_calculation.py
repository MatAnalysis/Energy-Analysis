"""
TODO !!!!!
"""
#########################################################
# Imports
##########################################################

import yfinance as yf
import pandas as pd
import os

#########################################################
# Functions
##########################################################


# Clears the series index
def normalize_index(series):
    # changes the type of index to datetime
    idx = pd.to_datetime(series.index)
    # deletes UTC
    if hasattr(idx, "tz") and idx.tz is not None:
        idx = idx.tz_localize(None)
    # overrides the index
    series.index = idx
    # returns data
    return series


def get_returns_yfinance(ticker, start, end):
    """
     Function returns given data yahoo finance
     ticker - downloaded data for example E.ON Bond
     start - start date
     end - end date

    """
    # trying first method - using yf.Ticker
    try:
        tk = yf.Ticker(ticker)
        raw = tk.history(start=start, end=end, auto_adjust=True)

        # return data if its greater than 30 records
        if not raw.empty and len(raw) > 30:
            # normalization
            close = normalize_index(raw["Close"].squeeze())
            #  delete NaN and return close values
            return close.pct_change().dropna()
    except Exception:
        pass

    # second method - using yf.download
    try:
        raw = yf.download(ticker, start=start, end=end,
                          auto_adjust=True, progress=False)
        # return data if its greater than 30 records
        if not raw.empty:
            # for multiple columns
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            # normalization
            close = normalize_index(raw["Close"].squeeze())
            #  delete NaN and return close values
            return close.pct_change().dropna()
    except Exception:
        pass
    return pd.Series(dtype=float)


def get_returns_csv(filepath):
    """
    Loading data from a CSV file downloaded from Investing.com.
    Format: Date, Price, Open, High, Low, Vol., Change %
    """
    # checks if file exists
    if not os.path.exists(filepath):
        print(f" file does not exist: {os.path.abspath(filepath)}")
        # returns pd.Series if file doesnt exist
        return pd.Series(dtype=float)

    try:

        # reading the file
        df = pd.read_csv(filepath)
        # clearing string columns
        df.columns = df.columns.str.strip()
