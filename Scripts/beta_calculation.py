"""
TODO !!!!!
"""
#########################################################
# Imports
##########################################################

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
EDF_CSV_PATH = "../Data/Electricite_de_France.csv"

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


#########################################################
# DATA SUMMARY
##########################################################

print("=" * 50)
print(f"{'Company':<12} {'Beta':>8}  {'Interpretation'}")
print("-" * 50)
for ticker, beta in results.items():
    if np.isnan(beta):
        print(f"{ticker:<12} {'n/d':>8}  No data")
        continue
    if beta < 0.6:   interp = "very defensive"
    elif beta < 0.9: interp = "defensive"
    elif beta < 1.1: interp = "neutral"
    else:            interp = "ogresive"
    print(f"{ticker:<12} {beta:8.4f}  {interp}")
print("=" * 50)
print(f"Benchmark: {BENCHMARK} (Euro Stoxx 50)")
print("Warining: EDF.PA – delisting 2023 (Nationalization)\n")


#########################################################
# PLOTTING THE DATA
##########################################################

available = {t: rb for t, rb in rolling_betas.items() if not rb.empty}

if not available:
    print("No Data available")
else:
    fig, ax = plt.subplots(figsize=(13, 6))

    # Grey background
    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#3a3a3a")

    # Plotting Rolling beta
    for ticker, rb in available.items():
        beta_label = f"{results[ticker]:.2f}" if not np.isnan(results[ticker]) else "n/d"
        ax.plot(
            rb.index, rb.values,
            label=f"{ticker}  (β total = {beta_label})",
            color=COLORS[ticker], linewidth=2
        )

    # lines at 1 and 0 as the reference lines
    ax.axhline(1.0, color="white", linestyle="--", linewidth=1, alpha=0.5)
    ax.axhline(0.0, color="white", linestyle=":", linewidth=1, alpha=0.3)

    # Highlight important periods
    ax.axvspan(pd.Timestamp("2020-02-01"), pd.Timestamp("2020-06-01"),
               alpha=0.08, color="orange", label="COVID-19 (02–06.2020)")
    ax.axvspan(pd.Timestamp("2021-10-01"), pd.Timestamp("2022-12-01"),
               alpha=0.06, color="red", label="Energy crisis (2021–22)")


    # Title
    ax.set_title(
        "Yearly rolling beta \n"
        "EDF.PA / RWE.DE / EOAN.DE  vs  Euro Stoxx 50",
        fontsize=14, fontweight="bold", color="white", pad=12
    )
    # axis titles
    ax.set_xlabel("Data", fontsize=11, color="white")
    ax.set_ylabel("Beta (β)", fontsize=11, color="white")

    # additional axis formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45, color="white")
    ax.tick_params(colors="white")

    # Chart frame
    for spine in ax.spines.values():
        spine.set_color("white")

    # grid
    ax.grid(True, color="white", alpha=0.15)

    # Legend formatting
    ax.legend(
        loc="upper right",
        fontsize=10,
        facecolor="#3a3a3a",
        edgecolor="white",
        labelcolor="white"
    )
    # adjusting layout
    fig.tight_layout()

    # saving to file
    fig_name = "rolling_beta.png"
    plt.savefig(fig_name, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Chart saved as: {fig_name}")

    plt.show()
