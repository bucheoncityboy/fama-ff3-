# Appendix Table Coverage Audit

Reference: `Fama-French 1993 재현 및 정리.md`

This file checks whether the repository implementation follows the appendix table focus, and whether explicitly excluded tables were actually left out.

## Summary

| Table | Appendix intent | Current repo status | Verdict |
|---|---|---|---|
| Table 1 (1)(2) | Include 25 stock portfolio descriptive cells | `07_section0_descriptive_stats.py` + `output/table0_descriptive_stats.csv` covers average firm count / market cap / cap share | Partial |
| Table 1 (3) | Include annual E/P and D/P by 25 size-BE/ME cells | Not implemented in appendix-table form | Missing |
| Table 2 (1) | Include factor summary + autocorrelation + correlation matrix | `03_section3_statistics.py` covers means/std/t-stats only; autocorrelation/correlation matrix not separately exported | Partial |
| Table 2 (2)(3) | Include 25 stock excess return mean/std/t-stat cells | Covered in `output/table2_summary.csv` and README summary | Partial |
| Table 3 stock block | Include 25 stock TERM/DEF regressions | `appendix_output/table3_*` stock-only panels exported | Covered |
| Table 3 bond block | Exclude | Omitted from `appendix_output/`; remains only in research/master output | Excluded |
| Table 4 stock block | Include 25 stock market-only regressions | `appendix_output/table4_*` stock-only panels exported | Covered |
| Table 4 bond block | Exclude | Omitted from `appendix_output/`; remains only in research/master output | Excluded |
| Table 5 stock block | Include 25 stock SMB/HML regressions | `appendix_output/table5_*` stock-only panels exported | Covered |
| Table 5 bond block | Exclude | Omitted from `appendix_output/`; remains only in research/master output | Excluded |
| Table 6 stock block | Include 25 stock FF3 regressions | `appendix_output/table6_*` stock-only panels exported | Covered |
| Table 6 bond block | Exclude | Omitted from `appendix_output/`; remains only in research/master output | Excluded |
| Table 7a | Include 25 stock FF5 regressions | `appendix_output/table7a_*` stock-only panels exported | Covered |
| Table 7b | Exclude | Omitted from `appendix_output/`; remains only in research/master output | Excluded |
| Table 8a | Include stock RMO regressions | `08_section8a_rmo_regressions.py` + `output/table8a_rmo.csv` | Covered |
| Table 8b | Exclude | No separate appendix-facing Table 8b output created | Excluded |
| Table 9a | Include stock alpha/t(alpha) across models | `appendix_output/table9a_stock_alphas.csv` exported in appendix matrix form | Covered |
| Table 9b | Exclude | Omitted from `appendix_output/`; remains only in research/master output | Excluded |
| Table 9c | Additional attempt | `appendix_output/table9c_joint_tests.csv` exported (F-distribution p-values; bootstrap column left blank) | Covered with note |
| Table 10 | Exclude | No implementation/output | Excluded |
| Table 11 | Additional attempt | `09_section11_ep_dp_portfolios.py` + `output/table11_ep_dp.csv` | Covered |

## What was clearly done around the requested table-focused scope

- Added `07_section0_descriptive_stats.py` for Appendix Table 1 style descriptive outputs.
- Added `08_section8a_rmo_regressions.py` for Appendix Table 8a.
- Added `09_section11_ep_dp_portfolios.py` for Appendix Table 11.
- Added `10_appendix_table_exports.py` and generated `appendix_output/` so included tables now have assignment-facing stock-only files.
- Updated `README.md` so GitHub points directly to the appendix-facing output directory.

## Important caveat

Several regression CSVs in `output/` are still **research/master outputs**, not strict appendix-facing exports. That means they include both:

1. the stock block that the appendix wants to keep, and
2. the bond block that the appendix explicitly marks as excluded.

This affects:

- `output/table3_bond.csv`
- `output/table1_market.csv`
- `output/table5_smbhml.csv`
- `output/table4_stock3f.csv`
- `output/table5_five_factor.csv`
- `output/intercept_analysis.csv`

The assignment-facing exports in `appendix_output/` solve that separation problem without deleting the research/master outputs.

## Bottom line

- **Yes**: the work did proceed table-first, especially for Table 8a and Table 11.
- **Yes**: appendix-facing stock-only files now exist for the major included regression tables.
- **Yes**: excluded bond subtables are omitted from `appendix_output/` and remain only in master research files.

Remaining note: Table 1 panel 3 is provided as a reference snapshot because firm-level 25-cell E/P and D/P construction inputs are not present in this repository.
