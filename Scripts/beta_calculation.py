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

        # get the price column
        price_col = next((c for c in ["Price", "Close", "close", "price"] if c in df.columns), None)
        if price_col is None:
            print(f"  Price column not found: {list(df.columns)}")
            return pd.Series(dtype=float)
        # get the date column
        date_col = next((c for c in ["Date", "date", "Data"] if c in df.columns), None)
        if date_col is None:
            print(f"  Date column not found: {list(df.columns)}")
            return pd.Series(dtype=float)

        # converting and setting up date column
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=False, errors="coerce")
        df = df.dropna(subset=[date_col, price_col])
        df = df.set_index(date_col).sort_index()

        # changing price type
        if df[price_col].dtype == object:
            df[price_col] = df[price_col].str.replace(",", "").astype(float)

        close = normalize_index(df[price_col].dropna())
        returns = close.pct_change().dropna()
        print(f" Loaded {len(returns)} observations "
              f"({close.index[0].date()} → {close.index[-1].date()})")
        return returns

    except Exception as e:
        print(f" CSV error: {e}")
        return pd.Series(dtype=float)


def calc_beta(stock_ret, bench_ret):
    # function to calculate beta
    df = pd.DataFrame({"stock": stock_ret, "bench": bench_ret}).dropna()
    if len(df) < 30:
        return float("nan"), 0
    beta = df["stock"].cov(df["bench"]) / df["bench"].var()
    return beta, len(df)


def rolling_beta(stock_ret, bench_ret, window=252):
    # rolling beta calculation for the window of 252
    df = pd.DataFrame({"stock": stock_ret, "bench": bench_ret}).dropna()
    betas, dates = [], []
    for i in range(window, len(df) + 1):
        chunk = df.iloc[i - window:i]
        b = chunk["stock"].cov(chunk["bench"]) / chunk["bench"].var()
        betas.append(b)
        dates.append(chunk.index[-1])
    return pd.Series(betas, index=dates, name="beta")


#########################################################
# VARIABLE DEFINITION
##########################################################

BENCHMARK = "^STOXX50E"
EDF_CSV_PATH = "Electricite_de_France.csv"

TICKERS = {
    "EDF.PA":  ("2013-01-01", "2023-06-01", "csv"),
    "RWE.DE":  ("2013-01-01", "2025-03-15", "yfinance"),
    "EOAN.DE": ("2013-01-01", "2025-03-15", "yfinance"),
}

COLORS = {
    "EDF.PA":  "#e74c3c",
    "RWE.DE":  "#2ecc71",
    "EOAN.DE": "#3498db",
}

#########################################################
# LOADING THE BENCHMARK
##########################################################

print("Downloading the benchmark data (Euro Stoxx 50)...")
bench_returns = get_returns_yfinance(BENCHMARK, "2013-01-01", "2025-03-15")

if bench_returns.empty:
    raise RuntimeError("Can not load the benchmark data.")

print(f"  Benchmark: {len(bench_returns)} observations\n")



#########################################################
# LOADING THE DATA
##########################################################
results = {}
rolling_betas = {}

for ticker, (start, end, source) in TICKERS.items():
    print(f"Load: {ticker} ({start} → {end})  [source: {source}]")

    stock_ret = get_returns_csv(EDF_CSV_PATH) if source == "csv" \
                else get_returns_yfinance(ticker, start, end)

    if stock_ret.empty:
        print(f"  No Data for ticker: {ticker}\n")
        results[ticker] = float("nan")
        continue

    bench_cut = bench_returns.reindex(stock_ret.index).dropna()
    beta_total, n_obs = calc_beta(stock_ret, bench_cut)
    results[ticker] = round(beta_total, 4) if not np.isnan(beta_total) else float("nan")

    rb = rolling_beta(stock_ret, bench_cut)
    rolling_betas[ticker] = rb

    print(f"  Found {ticker}: β = {beta_total:.4f}  (Observations: {n_obs})\n")

