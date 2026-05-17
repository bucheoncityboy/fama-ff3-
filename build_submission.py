"""Build the assignment-submission package only."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "appendix_output"

SCRIPTS = [
    "01_section2_factors.py",
    "01b_section2_bond_factors.py",
    "02_section2_portfolios.py",
    "02b_section2_bond_portfolios.py",
    "07_section0_descriptive_stats.py",
    "08_section8a_rmo_regressions.py",
    "09_section11_ep_dp_portfolios.py",
    "10_appendix_table_exports.py",
]

LEGACY_RESEARCH_FILES = [
    "table1_market.csv",
    "table2_summary.csv",
    "table3_bond.csv",
    "table4_stock3f.csv",
    "table5_five_factor.csv",
    "table5_smbhml.csv",
    "grs_test_results.csv",
    "intercept_analysis.csv",
    "FF1993_replication_report.md",
    "fig1_average_returns_heatmap.png",
    "fig2_factor_cumulative_returns.png",
    "fig3_r2_comparison.png",
    "fig4_alpha_distribution.png",
    "fig5_factor_loadings_heatmap.png",
    "fig6_smb_hml_scatter.png",
]


def remove_legacy_outputs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for name in LEGACY_RESEARCH_FILES:
        path = OUTPUT_DIR / name
        if path.exists():
            path.unlink()


def main() -> None:
    remove_legacy_outputs()
    for script in SCRIPTS:
        print(f"Running {script}...")
        result = subprocess.run([sys.executable, script], cwd=ROOT)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    remove_legacy_outputs()
    print("Submission package build completed.")


if __name__ == "__main__":
    main()
