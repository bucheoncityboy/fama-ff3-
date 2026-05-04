"""
fred_bond_fetcher.py

Fetch bond data from FRED and construct TERM and DEF factors.

CRITICAL DISCLAIMER:
TERM and DEF are yield-based proxies constructed from FRED data, not return-based
factors as in Fama-French (1993). Numerical results may differ from the original paper.
"""

import os
import hashlib

import numpy as np
import pandas as pd
from pandas_datareader.data import DataReader

import config

# Prominent disclaimer constant
DISCLAIMER = (
    "TERM and DEF are yield-based proxies constructed from FRED data, "
    "not return-based factors as in FF(1993). "
    "Numerical results may differ from the original paper."
)

# FRED series identifiers
SERIES = {
    'aaa_tr': 'BAMLCC0A1AAATRIV',   # BofA AAA Corporate Total Return Index
    'bbb_tr': 'BAMLCC0A4CBBBTRIV',  # BofA BBB Corporate Total Return Index
    'lt_yield': 'DGS10',            # 10-Year Treasury Constant Maturity Rate
    'rf_yield': 'TB3MS',            # 3-Month Treasury Bill Rate
}


def _validate_dates(start, end):
    """Validate and parse date strings."""
    try:
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
    except Exception as exc:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD. Error: {exc}")

    if start_dt > end_dt:
        raise ValueError(f"Start date ({start}) must be before end date ({end}).")

    return start_dt, end_dt


def _generate_synthetic_series(start, end, symbol, seed_offset=0):
    """
    Generate a synthetic monthly total-return index when FRED data is unavailable.

    The generated path is deterministic (seed derived from symbol name) so that
    repeated calls with the same parameters produce identical output.
    """
    print(
        "[SYNTHETIC DATA] Generating mock total-return index for '%s' "
        "from %s to %s. This data is for testing/development only."
        % (symbol, start, end)
    )

    # Deterministic seed from symbol name
    seed = int(hashlib.md5(symbol.encode()).hexdigest(), 16) % (2**31)
    seed += seed_offset
    rng = np.random.default_rng(seed)

    # Create month-end date range
    dates = pd.date_range(start=start, end=end, freq='ME')

    # Parameters for monthly log-returns (annualized ~5% mean, ~8% vol → monthly ≈ 0.004, 0.023)
    mu = 0.004    # monthly mean
    sigma = 0.023 # monthly std

    log_rets = rng.normal(loc=mu, scale=sigma, size=len(dates))
    prices = 100.0 * np.exp(np.cumsum(log_rets))

    df = pd.DataFrame({symbol: prices}, index=dates)
    df.index.name = 'DATE'
    return df


def _fetch_series(symbol, start, end, allow_synthetic=False):
    """Fetch a single series from FRED with informative error handling."""
    try:
        df = DataReader(symbol, 'fred', start, end)
    except Exception as exc:
        if allow_synthetic:
            print(
                "WARNING: FRED series '%s' fetch failed (%s). Falling back to synthetic data."
                % (symbol, type(exc).__name__)
            )
            return _generate_synthetic_series(start, end, symbol)
        raise ConnectionError(
            f"Failed to fetch FRED series '{symbol}' from {start} to {end}. "
            f"Check your internet connection and that the series exists. "
            f"Original error: {exc}"
        )

    if df is None or df.empty:
        if allow_synthetic:
            print(
                "WARNING: FRED series '%s' returned no data for %s to %s. "
                "Falling back to synthetic data."
                % (symbol, start, end)
            )
            return _generate_synthetic_series(start, end, symbol)
        raise ValueError(
            f"FRED series '{symbol}' returned no data for {start} to {end}. "
            f"The series may not cover this date range."
        )

    return df


def _compute_monthly_returns(index_series):
    """Compute monthly returns from a total-return index series."""
    monthly = index_series.resample('ME').last()
    returns = monthly.pct_change().dropna()
    return returns


def fetch_bond_data(start='1963-07-01', end='1991-12-31'):
    """
    Fetch bond data from FRED and construct TERM and DEF factors.

    Parameters
    ----------
    start : str
        Start date in YYYY-MM-DD format
    end : str
        End date in YYYY-MM-DD format

    Returns
    -------
    pd.DataFrame
        DataFrame with TERM and DEF columns, datetime index (monthly)
    """
    print(DISCLAIMER)

    start_dt, end_dt = _validate_dates(start, end)

    # ------------------------------------------------------------------
    # 1. Fetch raw data from FRED
    # ------------------------------------------------------------------
    print("Fetching FRED series: %s" % list(SERIES.values()))
    raw = {}
    for key, symbol in SERIES.items():
        # Corporate bond indices often lack historical data in FRED;
        # allow synthetic fallback for those two.
        allow_fallback = key in ('aaa_tr', 'bbb_tr')
        raw[key] = _fetch_series(symbol, start_dt, end_dt, allow_synthetic=allow_fallback)

    # ------------------------------------------------------------------
    # 2. Align all series to monthly frequency
    # ------------------------------------------------------------------
    # Total return indices -> month-end -> monthly returns
    aaa_ret = _compute_monthly_returns(raw['aaa_tr'][SERIES['aaa_tr']])
    bbb_ret = _compute_monthly_returns(raw['bbb_tr'][SERIES['bbb_tr']])

    # Government yield (monthly) -> month-end value, converted to decimal
    lt_yield = raw['lt_yield'][SERIES['lt_yield']].resample('ME').last() / 100.0

    # Risk-free yield (already monthly from FRED), converted to decimal
    rf_yield = raw['rf_yield'][SERIES['rf_yield']].resample('ME').last() / 100.0

    # ------------------------------------------------------------------
    # 3. Construct factor proxies
    # ------------------------------------------------------------------
    # Corporate bond market return = average of AAA and BBB returns
    corp_ret = pd.concat([aaa_ret, bbb_ret], axis=1).mean(axis=1)

    # TERM = long-term government yield proxy - risk-free rate proxy
    term = lt_yield - rf_yield

    # DEF = corporate bond return - long-term government yield proxy
    def_ = corp_ret - lt_yield

    # ------------------------------------------------------------------
    # 4. Assemble output
    # ------------------------------------------------------------------
    df = pd.DataFrame({
        'TERM': term,
        'DEF': def_,
    })

    # Drop rows where either factor is missing
    df = df.dropna()

    if df.empty:
        raise ValueError(
            "No overlapping monthly data available for the requested date range. "
            "Some FRED series may not start until later than the start date."
        )

    # Ensure index name
    df.index.name = 'Date'

    # ------------------------------------------------------------------
    # 5. Filter to requested range
    # ------------------------------------------------------------------
    df = df[(df.index >= start_dt) & (df.index <= end_dt)]

    # ------------------------------------------------------------------
    # 6. Save to CSV
    # ------------------------------------------------------------------
    csv_path = os.path.join(config.DATA_DIR, 'bond_factors.csv')
    df.to_csv(csv_path)
    print("Saved bond factors to %s" % csv_path)

    return df


if __name__ == '__main__':
    print(DISCLAIMER)
    df = fetch_bond_data()
    print(df.head())
