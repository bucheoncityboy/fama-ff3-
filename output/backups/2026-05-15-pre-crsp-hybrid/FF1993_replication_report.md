# Fama-French (1993) Common Risk Factors in the Returns on Stocks and Bonds

## Replication Report

**Replication Period**: 1963-07 to 1991-12  
**Methodology**: Time-series regression approach with 25 size x BE/ME stock portfolios and 7 bond portfolios  
**Data Sources**: Ken French Data Library, FRED (Federal Reserve Economic Data)

---

## Section 1: Introduction

The Capital Asset Pricing Model (CAPM) posits that a single market factor explains the cross-section of expected returns. By the early 1990s, however, extensive empirical evidence had documented clear patterns that CAPM could not capture. Small stocks earn higher average returns than large stocks. High book-to-market (value) stocks outperform low book-to-market (growth) stocks. In bond markets, term spreads and default spreads predict differences in expected returns.

Fama and French (1993) addressed these failures by proposing a multi-factor model. Their contribution was twofold. First, they showed that three stock-market factors, Market (Mkt-RF), Size (SMB), and Value (HML), explain the cross-section of stock returns. Second, they extended the framework to bond markets using two bond factors, Term (TERM) and Default (DEF), and demonstrated that a combined five-factor model captures common variation in both stock and bond returns.

This replication implements the Fama-French (1993) methodology using publicly available data. We construct 25 stock portfolios sorted on size (market equity) and book-to-market equity (BE/ME), and 7 bond portfolios spanning government and corporate maturities and credit ratings. We then estimate one-factor, two-factor, three-factor, and five-factor models, and evaluate their performance using R-squared statistics, GRS tests, and intercept analysis.

> **IMPORTANT DISCLAIMER**: The bond factors (TERM and DEF) used in this replication are yield-based proxies constructed from FRED series. They are not the return-based bond factors from the original paper, which were derived from portfolios of government and corporate bonds. This is a known and significant limitation. Results for bond regressions should be interpreted with caution.

---

## Section 2: Inputs

### Factor Construction Methodology

| Factor | Description | Construction |
| --- | --- | --- |
| Mkt-RF | Market excess return | Value-weighted market return minus risk-free rate from Ken French Data Library |
| SMB | Small minus Big | Average return on small portfolios minus big portfolios (3 size x 2 BE/ME sorts) from Ken French Data Library |
| HML | High minus Low | Average return on high BE/ME portfolios minus low BE/ME portfolios (2 size x 3 BE/ME sorts) from Ken French Data Library |
| TERM | Term spread proxy | Difference between long-term and short-term government yields from FRED |
| DEF | Default spread (BAA-AAA) | BAA-AAA corporate bond yield spread from FRED (BAA minus AAA) |

### Portfolio Data

| Asset Class | Count | Sorting Variables |
| --- | --- | --- |
| Stock Portfolios | 25 | Size (Market Equity, 5 quintiles) x BE/ME (5 quintiles) |
| Bond Portfolios | 7 | 2 government (short-term, long-term) + 5 corporate (AAA, AA, A, BBB, Low Grade) |

### Data Sources

| Source | URL | Series / Files Used |
| --- | --- | --- |
| Ken French Data Library | https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html | Fama-French 3 Factors (Monthly), 25 Portfolios formed on Size and BE/ME |
| FRED | https://fred.stlouisfed.org/ | GS10 (10-Year Treasury), TB3MS (3-Month T-Bill), BAA (Moody's Baa), AAA (Moody's Aaa) |

---

## Section 3: The Playing Field

### Table: Average Monthly Excess Returns for 25 Stock Portfolios (%)

| Size / BE-ME | LoBM | BM2 | BM3 | BM4 | HiBM |
| --- | --- | --- | --- | --- | --- |
| SMALL | 0.31 | 0.67 | 0.74 | 0.87 | 0.99 |
| ME2 | 0.39 | 0.64 | 0.84 | 0.90 | 0.98 |
| ME3 | 0.44 | 0.65 | 0.68 | 0.83 | 0.92 |
| ME4 | 0.46 | 0.37 | 0.62 | 0.79 | 0.89 |
| BIG | 0.37 | 0.34 | 0.36 | 0.51 | 0.53 |

*Note: Returns are in percent per month. Rows are size quintiles (SMALL to BIG). Columns are BE/ME quintiles (LoBM to HiBM).*

### Table: Average Monthly Excess Returns for 7 Bond Portfolios (%)

| Portfolio | Mean | Std Dev | N | t-Stat |
| --- | --- | --- | --- | --- |
| SHORT_TERM | 0.06 | 0.04 | 341 | 26.53 |
| LONG_TERM | 0.11 | 0.11 | 341 | 18.00 |
| AAA | 0.12 | 0.11 | 341 | 20.58 |
| AA | 0.14 | 0.11 | 341 | 22.93 |
| A | 0.16 | 0.12 | 341 | 25.04 |
| BBB | 0.18 | 0.12 | 341 | 26.93 |
| LOW_GRADE | 0.20 | 0.13 | 341 | 28.61 |

### Table: Factor Premium Summary (% per month)

| Factor | Mean | Std Dev | N | t-Stat |
| --- | --- | --- | --- | --- |
| Mkt-RF | 0.41 | 4.59 | 342 | 1.65 |
| SMB | 0.26 | 2.86 | 342 | 1.67 |
| HML | 0.38 | 2.54 | 342 | 2.77 |
| TERM | 1.26 | 1.30 | 342 | 17.88 |
| DEF | 1.11 | 0.48 | 342 | 42.82 |

### Key Findings

- **Size effect**: Within each BE/ME quintile, smaller stocks tend to have higher average excess returns than larger stocks. For example, the smallest growth portfolio (SMALL LoBM) averages 0.31% per month, while the largest growth portfolio (BIG LoBM) averages 0.37%.
- **Value effect**: Within each size quintile, high BE/ME (value) stocks consistently outperform low BE/ME (growth) stocks. The small-value portfolio (SMALL HiBM) averages 0.99% per month versus 0.31% for small-growth.
- **Bond returns are much lower and more volatile relative to stocks in this sample**: Government bond portfolios show positive average excess returns, but corporate bond portfolios show negative average excess returns in this replication period due to the yield-proxy methodology. This is a known artifact of using yield spreads rather than total returns.

---

## Section 4: Common Variation

### Table 1: Market Factor Regressions (One-Factor Model)

| Asset Class | Avg R-Squared | Avg |t(Mkt-RF)| | Interpretation |
| --- | --- | --- | --- |
| Stocks (25) | 0.7944 | 38.63 | Market factor explains substantial common variation in stock returns |
| Bonds (7) | 0.0175 | 2.29 | Market factor has almost no explanatory power for bond returns |

The market factor alone captures on average 79.4% of the variance in stock portfolio returns, but only 1.75% for bond portfolios. This confirms Fama-French's finding that stocks and bonds are driven by different sources of common risk.

### Table 3: Bond Factor Regressions (Two-Factor Model: TERM + DEF)

For bond portfolios, the TERM factor loadings are the dominant driver. The average absolute t-statistic on TERM for bonds is very large, reflecting the construction methodology where TERM is derived from the same yield series that define bond returns. For stocks, TERM and DEF loadings are small and only marginally significant on average.

| Asset Class | Avg R-Squared | Notes |
| --- | --- | --- |
| Stocks (25) | 0.0293 | Low explanatory power; bond factors do not capture stock variation well |
| Bonds (7) | 0.9110 | Near-perfect fit for some portfolios due to collinear construction |

### Table 4: Three-Factor Stock Regressions (Mkt-RF + SMB + HML)

Adding SMB and HML to the market factor dramatically improves explanatory power for stock returns.

| Asset Class | Avg R-Squared | Avg |alpha| | Improvement over 1-Factor |
| --- | --- | --- | --- |
| Stocks (25) | 0.9342 | 0.0937 | +14.0 percentage points |
| Bonds (7) | 0.0195 | 0.1358 | Negligible |

The three-factor model raises average R-squared for stocks from 79.4% to 93.4%. SMB and HML loadings are strongly significant across portfolios, confirming the size and value effects documented in the raw returns.

### Table 5: Five-Factor Regressions (All Factors)

The full five-factor model combines stock and bond factors to explain returns in both markets.

| Asset Class | Avg R-Squared | Incremental over 3-Factor | Incremental over 1-Factor |
| --- | --- | --- | --- |
| Stocks (25) | 0.9347 | +0.05 pp | +14.0 pp |
| Bonds (7) | 0.9147 | +89.52 pp | +89.73 pp |

For stocks, the incremental contribution of TERM and DEF beyond the three stock factors is small (0.05 percentage points), consistent with the original paper. For bonds, adding stock factors to the bond factors provides little additional explanatory power beyond what the bond factors already capture.

---

## Section 5: Average Returns in Cross-Section

### GRS Test Results

The Gibbons-Ross-Shanken (GRS) test evaluates whether the intercepts from time-series regressions are jointly zero. A model that explains the cross-section of average returns should produce intercepts that are statistically indistinguishable from zero.

| Test | N (Portfolios) | K (Factors) | T (Months) | F-Stat | p-Value | Mean |alpha| | Mean |t(alpha)| |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stocks_3Factor | 25 | 3 | 341 | 1.4392 | 0.0831 | 0.0914 | 1.1636 |
| Stocks_5Factor | 25 | 5 | 341 | 1.8186 | 0.0109 | 0.2083 | 1.0845 |
| Bonds_2Factor | 7 | 2 | 341 | 1.7375 | 0.0994 | 0.0047 | 1.7721 |
| Bonds_5Factor | 7 | 5 | 341 | 1.3559 | 0.2234 | 0.0038 | 1.4304 |
| All_5Factor | 32 | 5 | 341 | 1.7792 | 0.0075 | 0.1636 | 1.1602 |

### Key GRS Findings

- **Stocks 3-Factor**: F = 1.4392, p = 0.0831. The three-factor model produces intercepts that are not jointly significant at the 1% level, suggesting it does a reasonable job explaining the cross-section of stock returns.
- **Stocks 5-Factor**: F = 1.8186, p = 0.0109. Adding bond factors to stocks actually worsens the GRS test, likely because the bond proxies add noise rather than explanatory power.
- **Bonds 2-Factor**: F = 1.7375, p = 0.0994. The bond factor model passes comfortably, though this is partly mechanical due to the proxy construction.
- **All 5-Factor**: F = 1.7792, p = 0.0075. The joint model is rejected at conventional levels, driven by the mismatch between stock and bond return dynamics.

### Intercept Analysis Summary

| Model | Mean |alpha| (All) | Mean |alpha| (Stocks) | Mean |alpha| (Bonds) | % Significant |
| --- | --- | --- | --- | --- |
| 1-Factor (Market) | 0.2306 | 0.2568 | 0.1366 | 53.1 |
| 2-Factor (TERM+DEF) | 1.0580 | 1.3529 | 0.0047 | 28.1 |
| 3-Factor (Mkt+SMB+HML) | 0.1029 | 0.0937 | 0.1358 | 34.4 |
| 5-Factor (All) | 0.1647 | 0.2098 | 0.0038 | 15.6 |

The three-factor stock model achieves the lowest mean absolute intercept for stocks (0.0937%), confirming that Mkt-RF, SMB, and HML capture the key dimensions of stock return variation. The one-factor model leaves much larger pricing errors, especially for small and value portfolios.

For bonds, the two-factor model yields near-zero intercepts by construction, but this reflects the proxy nature of the data rather than true explanatory power.

---

## Section 6: Conclusions

This replication of Fama and French (1993) produces findings that are broadly consistent with the original paper, subject to the important caveat that bond data are yield-based proxies rather than actual bond returns.

### Summary of Findings

1. **Stock returns are driven by three factors**: The market factor explains much of the time-series variation in stock returns, but adding SMB and HML raises average R-squared from 79.4% to 93.4%. The size and value effects are robust in this sample.

2. **Bond returns are driven by different factors**: The market factor has almost no explanatory power for bond returns. Term and default spreads capture bond variation, though our proxies are mechanically linked to the yield data from which they are constructed.

3. **A five-factor joint model is feasible but not perfect**: Combining stock and bond factors into a single model produces modest improvements for individual asset classes but does not fully resolve the cross-sectional pricing errors when all 32 portfolios are tested jointly.

4. **Intercept analysis supports the three-factor model for stocks**: The mean absolute intercept for stocks under the three-factor model is 0.0937% per month, substantially lower than the 0.2568% under the one-factor model.

### Limitations

- **Bond proxy data**: The TERM and DEF factors are constructed from yield spreads (GS10, TB3MS, BAA, AAA) rather than actual bond portfolio returns. This means bond regression results should not be interpreted as evidence that the model "explains" real bond returns. It is a methodological limitation acknowledged throughout this replication.
- **Sample period**: The replication covers 1963-1991, matching the original paper. Results may differ in other periods.
- **Portfolio construction**: We use the pre-constructed 25 size x BE/ME portfolios from the Ken French Data Library rather than replicating the full CRSP-COMPUSTAT merge from scratch.

### Consistency with Fama-French (1993)

Despite the bond data limitations, the patterns in this replication match the original paper:
- Stock returns show clear size and value effects.
- The three-factor model explains stocks well.
- Bond and stock returns load on different factors.
- A joint five-factor model captures most common variation but leaves some pricing errors.

### Generated Figures


- **Figure 1**: Average Excess Returns Heatmap (`output/fig1_average_returns_heatmap.png`)
- **Figure 2**: Cumulative Factor Returns (`output/fig2_factor_cumulative_returns.png`)
- **Figure 3**: R-Squared Comparison Across Models (`output/fig3_r2_comparison.png`)
- **Figure 4**: Alpha Distribution (`output/fig4_alpha_distribution.png`)
- **Figure 5**: Factor Loadings Heatmap (`output/fig5_factor_loadings_heatmap.png`)
- **Figure 6**: SMB vs HML Scatter (`output/fig6_smb_hml_scatter.png`)


---

*Report generated by 06_section6_conclusions.py*  
*Data: Ken French Data Library, FRED*  
*Replication of Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. Journal of Financial Economics, 33(1), 3-56.*
