"""
tests/test_paper_comparison.py

Tolerance-based tests that compare replication results with paper expectations.
These are "sanity checks" against the FF(1993) findings.
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_def_mean_positive():
    """DEF should be positive (BAA > AAA)."""
    df = pd.read_csv(os.path.join(BASE_DIR, "data", "bond_factors.csv"), index_col=0)
    assert df.DEF.mean() > 0
    assert 0.005 < df.DEF.mean() < 0.03


def test_term_mean_reasonable():
    """TERM should be positive (GS10 > TB3MS)."""
    df = pd.read_csv(os.path.join(BASE_DIR, "data", "bond_factors.csv"), index_col=0)
    assert df.TERM.mean() > 0


def test_stock_3factor_r2_high():
    """Stock 3-factor model should explain >80% of variance on average."""
    df = pd.read_csv(os.path.join(BASE_DIR, "output", "table4_stock3f.csv"))
    stock_r2 = df[df["type"] == "stock"]["r_squared"]
    assert stock_r2.mean() > 0.80


def test_grs_statistics_valid():
    """GRS test should produce valid statistics (no NaN/inf)."""
    df = pd.read_csv(os.path.join(BASE_DIR, "output", "grs_test_results.csv"))
    assert df["F_stat"].notna().all()
    assert df["p_value"].notna().all()
    assert (df["p_value"] >= 0).all() and (df["p_value"] <= 1).all()
