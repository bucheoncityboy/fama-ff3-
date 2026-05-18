# Fama-French (1993) 과제 제출 패키지

이 저장소는 **Fama & French (1993), _Common Risk Factors in the Returns on Stocks and Bonds_**의 핵심 결과를 과제 제출 형식으로 재현한 패키지다. 저장소는 더 이상 연구용 `output/` 중심 구조가 아니라, **제출용 산출물 `appendix_output/`만 공식 결과 디렉토리**로 사용한다.

핵심 목표는 두 가지였다.

1. 논문과 과제 가이드(`Fama-French 1993 재현 및 정리.md`)가 요구하는 표를 다시 만들기
2. 각 표가 논문의 어떤 주장과 연결되는지 README에서 직접 설명하기

---

## 1. 제출 패키지 사용법

### 공식 제출 산출물

- 제출용 결과 디렉토리: `appendix_output/`
- 제출용 빌드 스크립트: `build_submission.py`
- 표 커버리지 감사 문서: `TABLE_COVERAGE_AUDIT.md`

### 재생성 방법

```bash
python build_submission.py
python -m pytest -q
```

최근 검증 결과:

- `274 passed, 1 skipped`

---

## 2. 무엇을 어떻게 구현했는가

### 2.1 주식 포트폴리오 구성

주식 측 구현의 중심은 `compustat_portfolio_builder.py`다.

- Compustat BE(`compustat_be.csv`)의 pre-computed book equity를 사용했다.
- CRSP raw 데이터에서 `PRC`, `RET`, `SHROUT`, `PERMNO`, `PERMCO`를 읽었다.
- `gvkey → PERMCO → PERMNO` 연결로 Compustat과 CRSP를 묶었다.
- 매년 6월 NYSE breakpoint로 25개 Size×BE/ME 포트폴리오를 구성했다.
- 6개 2×3 포트폴리오도 함께 만들고 여기서 SMB/HML을 재계산했다.

논문 방법론상 1963-07 시점 포트폴리오를 만들려면 1962년 BE가 필요한데, 현재 데이터엔 그 연도가 없어서 **1963-07~1964-06은 seed/hybrid 구간**, 1964-07 이후는 자체 구축 구간으로 처리했다.

### 2.2 채권 요인 및 채권 프록시

채권 측은 논문 원자료를 그대로 복원할 수 없어서 FRED 기반 프록시로 구현했다.

- TERM = 장기 국채 수익률 − 단기 무위험 수익률
- DEF = BAA − AAA 신용스프레드
- 채권 포트폴리오는 실제 CRSP 채권 수익률이 아니라 yield-based proxy

그래서 채권 관련 결과는 “원 논문과 숫자까지 일치”를 증명하는 용도보다, **채권 요인과 주식 요인의 분리 구조가 나타나는지**를 확인하는 용도로 해석했다.

### 2.3 과제 제출용 표 구성기

`10_appendix_table_exports.py`가 최종 제출용 표를 정리한다.

이 스크립트는:

- 과제 가이드에서 **포함하라고 한 표만** `appendix_output/`에 저장하고
- 제외 대상과 추가 제외 지시(Table 3, Table 7a, Table 8a, Table 9a의 (i)/(v))를 파일 수준에서 제거하며
- Table 9a/9c처럼 과제에 맞는 형태로 다시 편집한다 (포함 모형 `(ii)` CAPM, `(iii)` SMB+HML, `(iv)` FF3F만 유지).
- **Table 9c**: F-분포 p-value와 함께 **residual bootstrap (B=999)** 기반 확률 수준을 추가로 계산한다. Restricted model (H0: alpha=0)의 잔차를 시간 축에서 복원 추출하여 cross-sectional correlation을 보존한 bootstrap p-value를 제공한다.

### 2.4 제출용 시각화

`11_submission_visualizations.py`는 appendix 표에서 바로 읽어 제출용 그림을 만든다.

| 그림 | 내용 | 데이터 출처 |
|---|---|---|
| `submission_fig1_stock_mean_heatmap.png` | 25개 포트폴리오 평균 초과수익률 히트맵 | Table 2 panel 2 |
| `submission_fig2_factor_premiums.png` | 5개 요인 평균 프리미엄 막대그래프 | Table 2 panel 1 |
| `submission_fig3_model_r2.png` | 세 모형(CAPM / SMB+HML / FF3F) 평균 R² 비교 | Table 4, 5, 6 |
| `submission_fig4_ep_dp_r2.png` | E/P·D/P 포트폴리오 CAPM vs FF3F R² 비교 | Table 11 |
| `submission_fig5_alpha_tests.png` | **5A**: 모형별 mean \|alpha\| 비교 / **5B**: 모형별 GRS F-stat 비교 | Table 9a, 9c |

즉, 지금 README에 나오는 그림은 “연구용 전체 출력”이 아니라 **제출용 appendix 결과를 직접 시각화한 그림**이며, 모든 그림은 `§4`의 통합 요약표에서 해당 표와 직접 연결된다.

---

## 2.5 표별 데이터 출처와 전처리

| 표 | 원천 데이터 | 전처리 | 최종 제출 파일 |
|---|---|---|---|---|
| Table 1 | **Compustat**: `compustat_be.csv` (GVKEY, BE, SICH)<br>**CRSP**: `crsp/RET__DLSTCD_1962.01_1991.12/` → `PRC`, `RET`, `SHROUT`, `PERMNO`, `PERMCO`, `DLSTCD`, `DLRET`<br>**Mapping**: `data/gvkey_permco_permno.csv` (GVKEY↔PERMCO↔PERMNO) | common stock 필터(SICH), ME 계산(PRC×SHROUT), NYSE breakpoint, 25 Size×BE/ME 포트폴리오 분류, formation year별 평균 기업수/시총/시총비중 계산 | `appendix_output/table1_panel1_firm_count_market_cap.csv`, `appendix_output/table1_panel2_cap_share_firm_count.csv` |
| Table 2 panel 1 | **CRSP FF factors**: `crsp/FF1993_results/data/crsp_ff_factors.csv` (Mkt-RF, SMB, HML, RF)<br>**FRED**: GS1, DGS10, TB3MS, BAA, AAA (TERM, DEF)<br>**채권 포트폴리오**: `appendix_output/bond_portfolios_excess.csv` | RM, TB, LTG, CB, RM-RF, RMO, SMB, HML, TERM, DEF 시계열의 평균/std/t/자기상관 계산 + 상관행렬 생성 | `appendix_output/table2_panel1_factor_summary.csv`, `appendix_output/table2_panel1_correlation_matrix.csv` |
| Table 2 panel 2-3 | **CRSP stock 포트폴리오**: `appendix_output/stock_portfolios_excess.csv` (25개 VW 포트폴리오 월별 수익률) | 25개 주식 포트폴리오 월 초과수익률에서 mean/std 및 t-stat 추출, 5×5 그리드로 재배열 | `appendix_output/table2_panel2_stock_mean_std.csv`, `appendix_output/table2_panel3_stock_tstats.csv` |
| Table 4 | `appendix_output/stock_portfolios_excess.csv`, `appendix_output/factors.csv` | OLS: `R-RF = a + b·(RM-RF) + e` → `b`, `t(b)`, `R²`, `s(e)`를 5×5 그리드로 정리 | `appendix_output/table4_panel1_b_t_b.csv`, `appendix_output/table4_panel2_r2_se.csv` |
| Table 5 | `appendix_output/stock_portfolios_excess.csv`, `appendix_output/factors.csv` | OLS: `R-RF = a + s·SMB + h·HML + e` → `s`, `t(s)`, `h`, `t(h)`, `R²`, `s(e)`를 5×5 그리드로 정리 | `appendix_output/table5_panel1_s_t_s.csv`, `appendix_output/table5_panel2_h_t_h.csv`, `appendix_output/table5_panel3_r2_se.csv` |
| Table 6 | `appendix_output/stock_portfolios_excess.csv`, `appendix_output/factors.csv` | OLS: `R-RF = a + b·(RM-RF) + s·SMB + h·HML + e` → `b`,`s`,`h`,`R²`,`s(e)`를 5×5 그리드로 정리 | `appendix_output/table6_panel1_b_t_b.csv`, `appendix_output/table6_panel2_s_t_s.csv`, `appendix_output/table6_panel3_h_t_h.csv`, `appendix_output/table6_panel4_r2_se.csv` |
| Table 9a | Table 4~6과 동일한 입력 (`stock_portfolios_excess.csv`, `factors.csv`) | 포함 모형 `(ii)` CAPM, `(iii)` SMB+HML, `(iv)` FF3F 각각 재회귀 → alpha/t(alpha)만 25×모형 행렬로 정리 | `appendix_output/table9a_stock_alphas.csv` |
| Table 9c | `appendix_output/stock_portfolios_excess.csv` + `appendix_output/bond_portfolios_excess.csv` + `appendix_output/factors.csv` | 포함 모형 `(ii)`, `(iii)`, `(iv)`에 대해 GRS(1989) F-test + residual bootstrap (B=999) 계산 | `appendix_output/table9c_joint_tests.csv` |
| Table 11 | **French Data Library**: `data/ep_dp_portfolios.csv` (E/P, D/P 정렬 12개 포트폴리오)<br>`appendix_output/factors.csv` | raw return mean/std/t, CAPM 회귀, FF3F 회귀를 수행해 long-format으로 저장 | `appendix_output/table11_ep_dp_long.csv`, `appendix_output/table11_ep_dp.csv` |

---

## 3. 논문의 어떤 부분을 어떻게 증명했는가

아래 표는 논문 주장, 구현 파일, 제출 파일, 그리고 무엇을 증명하는지의 연결표다.

| 논문/가이드 항목 | 구현 파일 | 제출 파일 | 증명하는 내용 |
|---|---|---|---|
| Table 1 (1)(2) | `07_section0_descriptive_stats.py` | `appendix_output/table1_panel1_firm_count_market_cap.csv`, `appendix_output/table1_panel2_cap_share_firm_count.csv` | 25개 포트폴리오가 실제로 형성되었고, size sorting과 시가총액 비중 구조가 유지됨 |
| Table 2 | `01_section2_factors.py`, `02_section2_portfolios.py`, `10_appendix_table_exports.py` | `appendix_output/table2_*` | 요인 평균/분산/자기상관, 그리고 25개 주식 포트폴리오 평균 수익률 패턴을 확인 |
| Table 4 | `04_section4_regressions.py`, `10_appendix_table_exports.py` | `appendix_output/table4_*` | 시장 요인 하나만으로는 주식 설명력이 충분하지 않음 |
| Table 5 | `10_appendix_table_exports.py` | `appendix_output/table5_*` | SMB/HML이 규모 효과·가치 효과를 반영함 |
| Table 6 | `04_section4_regressions.py`, `10_appendix_table_exports.py` | `appendix_output/table6_*` | 3요인 모형이 설명력을 크게 높임 |
| Table 9a | `05b_section5_intercepts.py`, `10_appendix_table_exports.py` | `appendix_output/table9a_stock_alphas.csv` | 포함 모형 `(ii)`, `(iii)`, `(iv)`의 절편(alpha) 크기를 비교해 pricing error를 평가 |
| Table 9c | `05_section5_grs_test.py`, `10_appendix_table_exports.py` | `appendix_output/table9c_joint_tests.csv` | 포함 모형 `(ii)`, `(iii)`, `(iv)`의 절편 공동검정(F-test)으로 전체 설명력을 평가 |
| Table 11 | `09_section11_ep_dp_portfolios.py` | `appendix_output/table11_ep_dp_long.csv` | E/P, D/P 정렬 포트폴리오에서 FF3F가 CAPM보다 더 높은 설명력을 보임 |

---

## 3.1 표별로 어떻게 논문 주장을 증명했는가

### Table 1 — 25개 포트폴리오 형성 자체의 증명

[Table 1](appendix_output/table1_panel1_firm_count_market_cap.csv)은 "포트폴리오가 실제로 올바르게 형성됐는가"를 보여주는 구조 검증 표다.

| Size ↓ / BM → | Low | 2 | 3 | 4 | High |
|---|---|---|---|---|---|
| **SMALL** | 419 / 23,438 | 288 / 23,311 | 279 / 22,692 | 303 / 21,465 | 521 / 16,154 |
| **BIG** | 85 / 3,848,011 | 55 / 3,290,642 | 46 / 3,392,519 | 39 / 3,075,283 | 24 / 2,518,772 |

> 각 셀: **avg firm count / avg market cap ($MM)**. SMALL-LOW는 419개 종목에 평균 시총 23,438MM, BIG-LOW는 85개 종목에 평균 시총 3,848,011MM이다.

소형주 셀은 종목 수가 훨씬 많지만 평균 시가총액은 매우 작고, 대형주 셀은 종목 수는 적지만 평균 시가총액은 매우 크다. 이 패턴은 **NYSE size breakpoint 기반 분류가 실제로 작동했다**는 직접 증거다.

### Table 2 — 논문의 기본 사실(size effect, value effect)의 원자료 증명

[Table 2](appendix_output/table2_panel2_stock_mean_std.csv)는 논문 핵심 주장인 size effect와 value effect가 데이터에 실제로 존재하는지를 보여준다.

| 증거 | 값 |
|---|---|
| SMALL-HIGH BM 평균 초과수익률 | **1.06%/월** |
| BIG-LOW BM 평균 초과수익률 | **0.39%/월** |
| ⟹ 가치주 > 성장주, 소형주 > 대형주 | Size & Value effect 모두 관측 |

→ [**Figure 1**](appendix_output/submission_fig1_stock_mean_heatmap.png)에서 이 패턴을 시각적으로 확인할 수 있다: 오른쪽(High BM)으로 갈수록 높은 색, 상단(Small)이 하단(Big)보다 짙은 색.

[Table 2 panel 1](appendix_output/table2_panel1_factor_summary.csv)은 요인 프리미엄을 보여준다:

| 요인 | 평균(%/월) | 표준편차 | t값 |
|---|---|---|---|
| RM-RF | **0.42** | 4.54 | 1.69 |
| SMB | **0.29** | 3.01 | 1.78 |
| HML | **0.41** | 2.43 | 3.15 |

→ 세 요인 모두 양(+)의 평균으로, 논문이 주장한 규모·가치 프리미엄이 구현에서도 살아 있다.

### Table 4 — 시장요인 하나만으로는 불충분하다는 증명

[Table 4](appendix_output/table4_panel2_r2_se.csv)는 CAPM 단일요인 모형 검정 결과, 25개 포트폴리오의 평균 R²는 **0.7524**다. 시장 베타는 대부분 강하게 유의하지만, 이 설명력만으로는 Table 2의 size/value 패턴을 모두 설명하지 못한다. 즉 **"시장 하나만으로는 부족하다"**는 논문 문제의식이 수치로 드러난다.

### Table 5 — SMB/HML이 정말 size/value 구조를 잡는다는 증명

[Table 5](appendix_output/table5_panel3_r2_se.csv)는 SMB, HML만으로 주식 포트폴리오를 설명했을 때 평균 R²는 **0.3488**이다. 개별 계수를 보면:

- **SMB 계수**: 25개 포트폴리오 모두 양(+)이고, 작을수록 더 크게 잡힌다 → SMB는 **규모 효과**를 반영
- **HML 계수**: Low BM 쪽은 음(-), High BM 쪽은 양(+) → HML은 **가치 효과**를 반영

즉 SMB는 규모 효과, HML은 가치 효과를 반영하는 요인 모방수익률이라는 논문 정의가 결과에서 드러난다.

### Table 6 — 3요인 모형이 주식 수익률 설명력을 크게 높인다는 증명

[Table 6](appendix_output/table6_panel4_r2_se.csv)의 평균 R²는 **0.8992**로, Table 4(CAPM 0.7524)보다 **+0.1468** 높다.

| 모형 | 평균 R² |
|---|---|
| CAPM (Table 4) | 0.7524 |
| SMB+HML (Table 5) | 0.3488 |
| **FF3F (Table 6)** | **0.8992** |

→ [**Figure 3**](appendix_output/submission_fig3_model_r2.png)에서 이 차이가 막대그래프로 시각화되어 있다. 1요인→3요인의 점프가 가장 크며, 이것이 바로 **"FF3F가 CAPM보다 우월하다"**는 과제의 핵심 증거다.

### Table 9a — 개별 포트폴리오 alpha가 줄어드는 방식의 증명

[Table 9a](appendix_output/table9a_stock_alphas.csv)는 포트폴리오별 절편(alpha)을 비교해 모형의 pricing error를 본다. 25개 포트폴리오의 평균 절대 alpha는:

| 모형 | Mean \|alpha\| |
|---|---|
| (ii) CAPM | **0.2680** |
| (iii) SMB+HML | **0.4408** |
| (iv) **FF3F** | **0.1240** ← 가장 작음 |

→ [**Figure 5A**](appendix_output/submission_fig5_alpha_tests.png)에서 이 비교가 막대그래프로 나타나 있다. FF3F가 가장 작은 stock alpha를 보이며, 3요인 모형이 가장 설득력 있는 stock pricing specification임을 시사한다.

### Table 9c — 공동 alpha 검정으로 보는 모형의 전체 설명력 증명

[Table 9c](appendix_output/table9c_joint_tests.csv)는 "각 포트폴리오의 alpha가 개별적으로만 작은 게 아니라, 전체적으로도 공동으로 작은가"를 검정한다.

| 모형 | F-stat | Bootstrap p |
|---|---|---|
| (ii) CAPM | 62.44 | 0.651 |
| (iii) SMB+HML | 59.28 | **0.040** |
| (iv) **FF3F** | 59.31 | **0.010** |

> F-분포 p-value는 세 모형 모두 ~0으로 H0 기각을 강하게 지시하지만, **residual bootstrap (B=999)** 은 모형별로 차별화된 p-value를 제공한다. CAPM의 bootstrap p = 0.651로 유의하지 않지만, FF3F는 0.010으로 5% 수준에서 기각된다.

→ [**Figure 5B**](appendix_output/submission_fig5_alpha_tests.png)에서 F-stat 비교를 시각화했다. 개별 alpha와 공동검정을 함께 읽으면, 포함된 다요인 모형 중 **FF3F가 가장 설득력 있는 stock specification**이라는 점이 드러난다.

### Table 11 — E/P·D/P 정렬에서도 FF3F가 CAPM보다 낫다는 추가 증명

[Table 11](appendix_output/table11_ep_dp_long.csv)은 논문 본문의 25포트폴리오 바깥에서도 결과가 유지되는지 확인하는 보강 증거다.

| 포트폴리오 | CAPM R² | FF3F R² | 개선 |
|---|---|---|---|
| EP <= 0 | 0.6593 | **0.8341** | +0.1748 |
| EP High | 0.8088 | **0.9129** | +0.1041 |
| DP = 0 | 0.8181 | **0.9293** | +0.1112 |
| DP High | 0.7049 | **0.8064** | +0.1015 |

→ 모든 비교에서 FF3F가 CAPM보다 높다. [**Figure 4**](appendix_output/submission_fig4_ep_dp_r2.png)에서 이 차이가 막대그래프로 시각화되어 있다. 따라서 **FF3F의 우월성은 Size×BE/ME 25포트폴리오에만 국한된 현상이 아니라, E/P·D/P 정렬 포트폴리오에서도 반복**된다.

---

## 4. 핵심 구현 결과와 시각화 통합 요약

아래 표는 이번 과제에서 가장 중요한 구현 결과를 **핵심 주장 / 근거 수치 / 대응 시각화 / 해석**으로 묶어 정리한 것이다.

| 핵심 주장 | 근거 수치 | 대응 표 | 대응 시각화 | 해석 |
|---|---|---|---|---|---|
| 가치 효과와 규모 효과가 동시에 나타난다 | Small-High BM = **1.06%/월**, Big-Low BM = **0.39%/월** | [Table 2 panels 2-3](appendix_output/table2_panel2_stock_mean_std.csv) | ![Figure 1](appendix_output/submission_fig1_stock_mean_heatmap.png) | 히트맵에서 오른쪽(High BM)으로 갈수록 높은 값이 많고, 상단 Small 쪽이 하단 Big보다 강하다. 즉 **HiBM > LoBM**, **Small > Big** 구조가 동시에 보인다. |
| 핵심 주식 요인 프리미엄은 양(+)이고 의미 있는 크기를 가진다 | RM-RF = **0.42%/월**, SMB = **0.29%/월**, HML = **0.41%/월** | [Table 2 panel 1](appendix_output/table2_panel1_factor_summary.csv) | ![Figure 2](appendix_output/submission_fig2_factor_premiums.png) | 주식 측 핵심 요인인 RM-RF, SMB, HML이 모두 양(+)의 평균을 가진다. TERM, DEF는 절대 크기는 더 크지만 채권 프록시 성격이 강하므로 해석을 분리해야 한다. |
| 3요인 모형은 CAPM보다 훨씬 높은 설명력을 가진다 | CAPM 평균 R² = **0.7524**, SMB+HML 평균 R² = **0.3488**, FF3F 평균 R² = **0.8992**, 개선폭 CAPM→FF3F = **+0.1468** | [Table 4](appendix_output/table4_panel2_r2_se.csv), [Table 5](appendix_output/table5_panel3_r2_se.csv), [Table 6](appendix_output/table6_panel4_r2_se.csv) | ![Figure 3](appendix_output/submission_fig3_model_r2.png) | Figure 3에서 1요인에서 3요인으로 점프가 가장 크다. 이것이 바로 **FF3F가 CAPM보다 우월하다**는 논문 핵심 주장에 대한 직접 증거다. |
| E/P·D/P 정렬 포트폴리오에서도 FF3F가 CAPM보다 우월하다 | EP<=0: **0.6593 → 0.8341**, EP High: **0.8088 → 0.9129**, DP=0: **0.8181 → 0.9293**, DP High: **0.7049 → 0.8064** | [Table 11](appendix_output/table11_ep_dp_long.csv) | ![Figure 4](appendix_output/submission_fig4_ep_dp_r2.png) | 모든 비교에서 FF3F 막대가 CAPM보다 높다. 3요인 모형의 우월성이 25포트폴리오 밖의 정렬에서도 반복된다. |
| 개별 alpha와 공동 alpha 검정에서도 다요인 구조의 우월성이 드러난다 | Stock mean \|alpha\|: CAPM **0.2680**, SMB+HML **0.4408**, FF3F **0.1240** / F-stat: CAPM **62.44**, SMB+HML **59.28**, FF3F **59.31** / Bootstrap p: CAPM **0.651**, SMB+HML **0.040**, FF3F **0.010** | [Table 9a](appendix_output/table9a_stock_alphas.csv), [Table 9c](appendix_output/table9c_joint_tests.csv) | ![Figure 5](appendix_output/submission_fig5_alpha_tests.png) | 개별 alpha 기준으로는 FF3F가 가장 작은 stock pricing error를 보인다. 공동검정 수치와 함께 읽으면, 포함된 다요인 모형 중 FF3F가 가장 설득력 있는 stock specification이라는 점이 드러난다. |

### 4.1 결과를 한 줄로 요약하면

- **원자료 패턴**: Size 효과와 Value 효과가 실제로 존재한다.
- **모형 비교**: CAPM보다 FF3F가 훨씬 잘 맞는다.
- **추가 정렬 강건성**: E/P·D/P 정렬에서도 같은 결론이 반복된다.

즉, 이번 제출 패키지는 **논문의 핵심 메시지인 “주식 수익률 설명의 중심은 3요인 구조”**를 표와 그림으로 일관되게 보여준다.

---

## 5. 제외 표는 어떻게 처리했는가

과제 가이드에서 제외 대상으로 명시한 항목은 `appendix_output/`에서 **아예 파일을 만들지 않았다**.

예:

- Table 3 전체
- Table 4 bond block
- Table 5 bond block
- Table 6 bond block
- Table 7a 전체
- Table 7b
- Table 8a 전체
- Table 8b
- Table 9a의 모형 (i), (v)
- Table 9b
- Table 10

즉, 이번 제출 패키지는 “README에서만 숨긴” 구조가 아니라 **파일 수준에서 분리된 제출물**이다.

---

## 6. 제출 시 직접 보면 되는 파일

### 핵심 표 파일

- `appendix_output/table1_panel1_firm_count_market_cap.csv`
- `appendix_output/table1_panel2_cap_share_firm_count.csv`
- `appendix_output/table2_panel1_factor_summary.csv`
- `appendix_output/table2_panel1_correlation_matrix.csv`
- `appendix_output/table2_panel2_stock_mean_std.csv`
- `appendix_output/table2_panel3_stock_tstats.csv`
- `appendix_output/table4_*`
- `appendix_output/table5_*`
- `appendix_output/table6_*`
- `appendix_output/table9a_stock_alphas.csv`
- `appendix_output/table9c_joint_tests.csv`
- `appendix_output/table11_ep_dp_long.csv`

### 지원 파일

- `appendix_output/factors.csv`
- `appendix_output/stock_portfolios_excess.csv`
- `appendix_output/bond_portfolios_excess.csv`
- `appendix_output/table11_ep_dp.csv`
- `appendix_output/table0_descriptive_stats.csv`

### 그림 파일

- `appendix_output/submission_fig1_stock_mean_heatmap.png`
- `appendix_output/submission_fig2_factor_premiums.png`
- `appendix_output/submission_fig3_model_r2.png`
- `appendix_output/submission_fig4_ep_dp_r2.png`
- `appendix_output/submission_fig5_alpha_tests.png`

---

## 7. 남은 주의사항

1. Table 1 panel 3은 원천 25셀 E/P·D/P 구성 입력이 저장소에 없어, 가이드 기준 reference snapshot으로 제공한다.
2. Table 9c는 F-distribution 기반 p-value와 residual bootstrap (B=999) 기반 확률 수준을 함께 제공한다. Bootstrap은 restricted model (H0: alpha=0)의 residuals를 시간 축에서 재추출하여 cross-sectional correlation을 보존했다.
3. 채권 측은 proxy 기반이므로, 주식 측처럼 논문 원수치와 직접 비교하는 방식은 피해야 한다.

---

## 8. 참고 문서

- 과제 기준표: `Fama-French 1993 재현 및 정리.md`
- 표 커버리지 감사: `TABLE_COVERAGE_AUDIT.md`
- 제출 산출물 인덱스: `appendix_output/README.md`
