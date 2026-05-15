# Fama-French (1993) Replication — 주식과 채권 수익률의 공통 위험요인

본 프로젝트는 Fama & French (1993)의 논문 *"Common Risk Factors in the Returns on Stocks and Bonds"*을 Python으로 복제한 결과이다. 기존의 단일 요인 모델(CAPM)을 넘어, 시장 요인(Mkt-RF)에 규모(SMB), 가치(HML), 기간 스프레드(TERM), 부도 스프레드(DEF)를 추가한 5요인 모델을 재구성하고, 1963년 7월부터 1991년 12월까지 25개 주식 포트폴리오와 7개 채권 포트폴리오에 대한 설명력을 평가한다.

---

## 1. 소개

자본자산가격결정모형(CAPM)은 단일 시장 요인이 기대수익률의 횡단면을 설명한다고 주장한다. 그러나 1980년대와 1990년대 초반에 축적된 실증 연구 결과는 이 예측을 반복적으로 기각했다. 이에 Fama와 French(1993)은 시장 요인에 규모(SMB), 가치(HML), 그리고 두 개의 채권 요인(TERM과 DEF)을 추가한 다요인 모델을 제안했다.

### 복제 범위
- **분석 기간**: 1963-07 ~ 1991-12 (342개월)
- **5개 요인**: Mkt-RF, SMB, HML, TERM, DEF
- **검정 자산**: 25개 규모 × 장부가치/시장가치(BE/ME) 주식 포트폴리오 + 7개 채권 포트폴리오 프록시
- **데이터 출처**: Hybrid stock-side data (Ken French 1963-07~1968-06 + CRSP-derived 1968-07~1991-12) + FRED (채권 수익률 프록시)

> **채권 프록시 면책 조항**: 본 복제에서 사용된 채권 요인(TERM, DEF)은 FRED(GS10, TB3MS, BAA, AAA)에서 수집한 실제 시장 데이터(수익률 스프레드)이다. 다만 채권 포트폴리오는 실제 채권 포트폴리오 수익률이 아니라, 해당 수익률 기반 추정치(yield-based proxies)이다. 이는 원 논문에서 사용된 CRSP 채권 데이터에 접근할 수 없는 모든 복제 연구에 내재된 한계이다.

### 최근 업데이트 (Recent Updates)

- **2026-05-15 — CRSP hybrid stock-side data substitution**
  - `data/ff_factors.csv`, `data/ff_6_portfolios.csv`, `data/ff_25_portfolios.csv`를 342개월 hybrid 입력으로 교체
  - 1963-07~1968-06은 기존 프로젝트/Ken French 데이터 유지, 1968-07~1991-12는 `crsp/FF1993_results/data/crsp_*`의 CRSP-derived stock data 사용
  - 원본 입력과 기존 output은 `data/backups/2026-05-15-pre-crsp-hybrid/`, `output/backups/2026-05-15-pre-crsp-hybrid/`에 보존
  - 전체 분석 output 재생성 및 최종 보고서에 hybrid provenance 명시
  - 테스트 206개 전체 통과 (`python -m pytest -q`), 단 hybrid 데이터에서는 5요인 주식 모델의 평균 |alpha|가 1요인보다 높게 나타나며 3요인 주식 모델이 가장 낮은 stock |alpha|를 보임

- **2025-05-07 — DEF 버그 수정 및 코드 품질 개선**
  - `fred_bond_fetcher.py`: DEF를 BAA-AAA 회사채 수익률 스프레드로 재정의 (기존: 월간 수익률과 연간 수익률을 혼합하여 단위 불일치)
  - `regression_engine.py`: intercept 추출 로직 단순화(11줄 → 2줄), ridge 정규화 제거 후 `pinv` 기반으로 통일
  - `02b_section2_bond_portfolios.py`: FRED yield가 연간화되어 있으므로 `/12`로 월간 변환 추가
  - 채권 R² 인공적 1.0 문제 해결 (기존: 인위적 공선성으로 ≈1.000 → 수정 후: max 0.985)
  - 테스트 206개 전체 통과, `test_paper_comparison.py` 신규 추가 (논문 수치 비교)

---

## 2. 저장소 구조 및 파일 맵핑

각 Python 스크립트는 원 논문의 특정 섹션이나 표와 대응한다.

| 논문 섹션 | 스크립트 | 설명 |
|-----------|----------|------|
| Section 2.1 (주식 요인) | `01_section2_factors.py` | 6개 포트폴리오로부터 SMB/HML 구성 |
| Section 2.1 (채권 요인) | `01b_section2_bond_factors.py` | TERM/DEF를 주식 요인과 병합 |
| Section 2.2 (주식 포트폴리오) | `02_section2_portfolios.py` | 25개 규모 × BE/ME 포트폴리오 불러오기 |
| Section 2.2 (채권 포트폴리오) | `02b_section2_bond_portfolios.py` | 7개 채권 포트폴리오 프록시 생성 |
| Section 3 (기술통계) | `03_section3_statistics.py` | Table 2 요약 통계량 |
| Section 4.1-4.3 (공통 변동) | `04_section4_regressions.py` | Tables 1, 3, 4 회귀분석 |
| Section 4.4 (5요인 모델) | `04b_section4_five_factor.py` | Table 5 통합 회귀분석 |
| Section 5 (GRS 검정) | `05_section5_grs_test.py` | GRS F-검정 구현 |
| Section 5 (절편 분석) | `05b_section5_intercepts.py` | 횡단면 절편 분석 |
| Section 6 (시각화) | `06_section6_visualizations.py` | 6개 학술 품질 Figure 생성 |
| Section 1+6 (보고서) | `06_section6_conclusions.py` | 최종 Markdown 보고서 생성 |
| 공유 인프라 | `regression_engine.py` | OLS 래퍼, 배치 회귀, GRS 공분산 |
| 데이터 파이프라인 | `download_data.py` | 데이터 자동 다운로드 |
| 파서 | `ken_french_parser.py` | Ken French CSV 파서 |
| 채권 수집기 | `fred_bond_fetcher.py` | FRED 채권 데이터 수집기 |
| 설정 | `config.py` | 프로젝트 설정 |

---

## 3. 실행 방법

### 사전 요건
- Python 3.10+
- `pip` 패키지 관리자

### 설치

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 데이터 다운로드
python download_data.py
```

위 명령어는 Ken French Data Library와 FRED에서 필요한 모든 데이터를 가져와 `data/` 디렉토리에 저장한다.

### 전체 분석 순차 실행

```bash
# 3. 전체 분석 순차 실행
python 01_section2_factors.py
python 01b_section2_bond_factors.py
python 02_section2_portfolios.py
python 02b_section2_bond_portfolios.py
python 03_section3_statistics.py
python 04_section4_regressions.py
python 04b_section4_five_factor.py
python 05_section5_grs_test.py
python 05b_section5_intercepts.py
python 06_section6_visualizations.py
python 06_section6_conclusions.py
```

생성된 결과물(CSV 및 PNG 파일)은 `output/` 디렉토리에 저장된다.

### 테스트 실행

```bash
# 4. 테스트 실행
python -m pytest -q
```

---

## 4. 핵심 결과

### Table 1 — 시장 요인 단독
- **주식 포트폴리오**: R²는 0.60에서 0.90까지 분포하며, 평균 **0.753**이다. 시장 요인이 주식 수익률 변동의 상당 부분을 설명한다.
- **채권 포트폴리오**: 평균 R²는 **0.017**이다. 시장 요인은 채권 수익률 변동을 거의 설명하지 못한다.
- **결론**: 단일 시장 요인은 주식에는 적절하지만, 채권에는 전혀 부족하다.

### Table 3 — 채권 요인 단독
- **채권 포트폴리오**: 평균 R²는 **0.911**이다. TERM과 DEF가 채권 프록시 변동의 대부분을 설명하지만, 이는 yield-based proxy 구성과 기계적으로 연결된 측면이 있다.
- **주식 포트폴리오**: 채권 요인은 주식 수익률에 거의 설명력을 추가하지 못한다.
- **결론**: 채권 요인은 채권 변동을 포착하지만, 주식 변동을 설명하는 데는 실패한다.

### Table 4 — 3요인 주식 모델
- **주식 포트폴리오**: R²가 0.82~0.95로 향상되며, 평균 **0.899**이다.
- **SMB와 HML**: 두 요인 모두 거의 모든 포트폴리오에서 강하게 유의하다.
- **절편**: 평균 절대절편 |α| = **월 0.125%**로 0에 비교적 가깝다.
- **결론**: 3요인 모델은 주식 수익률을 훌륭하게 설명한다.

### Table 5 — 5요인 통합 모델
- **주식 포트폴리오**: 평균 R² = **0.900**이다. 3요인 모델 대비 R² 개선은 약 **0.07 percentage point**로 작다.
- **주식에 대한 채권 요인**: TERM과 DEF는 주식 수익률에 거의 설명력을 추가하지 못한다.
- **채권에 대한 주식 요인**: SMB와 HML은 채권 수익률에 거의 설명력을 추가하지 못한다. 채권 평균 R²는 **0.915**이다.
- **결론**: 요인 지배 패턴이 확인되었다. 주식 요인은 주식을 설명하고, 채권 요인은 채권을 설명하며, 자산 간 교차 효과는 제한적이다.

### GRS 검정 (Section 5)
- **3요인 주식 모델**: F = **1.4493**, p = **0.0792** — 10% 수준에서는 한계적으로 기각되나, 5% 수준에서는 기각되지 않는다.
- **5요인 주식 모델**: F = **1.7871**, p = **0.0131** — 5% 수준에서 기각된다.
- **2요인 채권 모델**: F = **1.7375**, p = **0.0994** — 5% 수준에서는 기각되지 않는다.
- **결론**: 3요인 모델은 주식에서 우수한 성능을 보인다. 5요인 모델은 과적합(overfitting)을 보인다. 2요인 채권 모델은 기각되지 않는다.

### 절편 분석 (Section 5)
- **3요인 주식 평균 |α|** = 0.1247%
- **5요인 주식 평균 |α|** = 0.3020%
- **1요인 주식 평균 |α|** = 0.2680%
- **2요인 채권 평균 |α|** = 0.0047%
- **해석**: Hybrid stock-side data에서는 채권 프록시를 추가한 5요인 주식 모델보다 3요인 주식 모델의 평균 |α|가 더 낮다.

### 시각화 결과

본 프로젝트는 **6개의 학술 품질 Figure**를 생성한다. 아래는 각 Figure에 대한 구체적인 분석과 논문의 핵심 인사이트를 시각적으로 확인한 결과이다.

---

#### Figure 1: Average Monthly Excess Returns Heatmap (Table 2)

![Figure 1](output/fig1_average_returns_heatmap.png)

**해석**: 25개 주식 포트폴리오의 평균 월간 초과수익률을 Size(세로) × BE/ME(가로) 히트맵으로 시각화했다. 원 논문의 대표적인 패턴이 확인된다:

- **규모 효과(Size effect)**: 같은 BE/ME 그룹 내에서 Small → Big로 갈수록 초과수익률이 감소한다 (왼쪽이 더 진한 초록색).
- **가치 효과(Value effect)**: 같은 Size 그룹 내에서 LoBM → HiBM로 갈수록 초과수익률이 증가한다 (아래쪽이 더 진한 초록색).
- **Small-Value anomaly**: Small & HiBM 셀에서 가장 높은 평균 초과수익률을 보인다. 이것이 Fama-French가 SMB와 HML 요인을 도입한 핵심 동기이다.

---

#### Figure 2: Cumulative Factor Returns (1963–1991)

![Figure 2](output/fig2_factor_cumulative_returns.png)

**해석**: 5개 요인(Mkt-RF, SMB, HML, TERM, DEF)의 누적 수익률 시계열이다. 각 패널은 해당 요인의 장기적 성과와 변동성 특성을 보여준다:

- **Mkt-RF**: 342개월 기간 동안 강한 상승 추세를 보이며, 주식 시장의 장기적 위험 프리미엄을 확인시켜준다.
- **SMB**: 소형주 프리미엄의 시계열 변동을 보여준다. 1980년대 초반과 후반에 상승 국면이 있다.
- **HML**: 가치주 프리미엄도 장기적으로 양수이나, SMB보다 변동성이 크다. 특정 기간(예: 1980년대 중반)에 급등하는 모습이 보인다.
- **TERM & DEF**: 채권 요인은 주식 요인 대비 평균이 낮고 변동성도 작다. 이는 채권 시장의 위험 프리미엄이 주식보다 작음을 반영한다.

---

#### Figure 3: Average R² Across Model Specifications

![Figure 3](output/fig3_r2_comparison.png)

**해석**: 주식 포트폴리오(파란색)와 채권 포트폴리오(주황색)에 대해 4가지 모델 사양의 평균 R²를 비교한 그래프이다. 이것이 논문의 가장 중요한 시각적 요약이다:

- **주식 포트폴리오**:
  - 시장 단독(1-Factor): 평균 R² ≈ 0.753
  - 3요인 모델: 평균 R² ≈ 0.899 (시장 단독 대비 +0.146)
  - 5요인 모델: 평균 R² ≈ 0.900 (3요인 대비 미미한 개선)
  - **인사이트**: SMB와 HML이 주식 변동의 상당 부분을 추가로 설명하지만, 채권 요인(TERM, DEF)은 주식에 거의 기여하지 않는다.

- **채권 포트폴리오**:
  - 시장 단독: R² ≈ 0 (시장 요인은 채권을 전혀 설명하지 못함)
  - 2요인(채권) 모델: R² ≈ 0.85 (TERM과 DEF가 채권 변동의 대부분을 설명)
  - 5요인 모델: R² ≈ 0.87 (주식 요인 추가는 미미)
  - **인사이트**: 요인 지배(dominated by own factors) 패턴이 명확히 드러난다.

---

#### Figure 4: Distribution of Alphas — Five-Factor Model

![Figure 4](output/fig4_alpha_distribution.png)

**해석**: 5요인 모델의 회귀 절편(α) 분포를 주식 포트폴리오(파란색)와 채권 포트폴리오(주황색)로 비교한 히스토그램이다:

- **주식 α**: 0을 중심으로 분포하나, 꼬리가 양쪽으로 퍼져 있다. Hybrid run의 5요인 주식 평균 절대절편은 ≈ 0.302%/월로, 0에 완벽히 집중되어 있지는 않다. 이는 5요인 모델이 주식의 횡단면을 완전히 설명하지 못함을 시사하며, GRS 검정에서도 기각되는 이유이다.
- **채권 α**: 0에 훨씬 더 밀집되어 있고 폭이 좁다. 평균 절대절편 ≈ 0.03%/월. 이는 2요인 채권 모델이 채권 수익률을 상대적으로 잘 설명함을 보여준다.
- **논문적 의미**: α가 0에 가까울수록 요인 모델이 자산의 평균 수익률 횡단면을 잘 설명한다는 의미이다. Hybrid 데이터에서는 주식 3요인 모델(α≈0.125%)이 5요인 모델(α≈0.302%)보다 더 나은 성능을 보인다.

---

#### Figure 5: Factor Loadings (Betas) — Five-Factor Model

![Figure 5](output/fig5_factor_loadings_heatmap.png)

**해석**: 32개 포트폴리오(상단 25개 주식, 하단 7개 채권)에 대한 5요인 모델의 β 계수 히트맵이다. 색상이 진할수록 부하량의 절대값이 크다:

- **주식 포트폴리오의 Mkt-RF 부하**: 모든 주식 포트폴리오에서 강하게 양수(진한 빨강). 시장 베타는 0.8~1.2 범위에 집중되어 있다.
- **SMB 부하**: Small 포트폴리오(상단)에서 양수, Big 포트폴리오(하단)에서 음수. 규모 요인이 포트폴리오 구성 방식과 정확히 일치함을 보여준다.
- **HML 부하**: HiBM(가치주)에서 양수, LoBM(성장주)에서 음수. 가치 요인의 구조적 패턴이 명확하다.
- **TERM/DEF 부하 (주식)**: 거의 0에 가까움(흰색). 채권 요인이 주식 수익률에 거의 영향을 주지 않음을 시각적으로 확인.
- **채권 포트폴리오**: TERM과 DEF에 강한 양수 부하를 보이며, 주식 요인(Mkt-RF, SMB, HML)에는 거의 부하가 없다.
- **요인 지배 패턴**: 주식 요인은 주식에, 채권 요인은 채권에 부하가 집중되는 대각선 구조가 뚜렷하다.

---

#### Figure 6: SMB vs HML Monthly Returns Scatter

![Figure 6](output/fig6_smb_hml_scatter.png)

**해석**: 342개월간 SMB와 HML의 월간 수익률 산점도이다. 색상은 시간 흐름에 따른 진행(1963 연한색 → 1991 진한색)을 나타낸다:

- **상관관계**: 회귀선 기울기 ≈ 0에 가까우며, SMB와 HML 간의 순수 상관관계는 낮다. 이는 두 요인이 서로 독립적인 정보를 담고 있음을 의미한다.
- **시간적 패턴**: 초기(1963-1970)와 후기(1980-1991)에 점들이 비슷하게 흩어져 있어, 두 요인의 공분산 구조가 샘플 기간 내내 비교적 안정적임을 시사한다.
- **이상치**: 1980년대 중반 HML이 급등하는 몇 개월(진한색 점들의 우측 꼬리)이 눈에 띈다. 이는 가치주 프리미엄의 단기적 급등을 반영한다.
- **다변량 정규성**: 대부분의 점이 원점 주변에 집중되어 있으나, 극단값이 존재한다. GRS 검정의 유효성을 평가할 때 잔차의 공분산 행렬 추정이 중요한 이유이다.

---

## 5. 한계점

1. **채권 요인은 실제 FRED 시장 데이터이다**: TERM은 GS10 yield에서 TB3MS yield를 뺀 기간 스프레드(term spread)이며, DEF는 BAA yield에서 AAA yield를 뺀 신용 스프레드(credit spread)이다. 둘 다 FRED에서 수집한 실제 시장 수익률(yield) 데이터이지만, 이는 월간 채권 포트폴리오 수익률(return)이 아니라 수익률 스프레드(yield spread)이다. 이는 원 논문 대비 가장 큰 차이점이다. (참고: 초기 버전의 DEF는 월간 수익률과 연간 수익률을 혼합하여 계산했던 단위 불일치 버그가 있었으나, 현재는 BAA-AAA yield spread로 수정되었다.)
2. **채권 포트폴리오는 수익률 기반 추정치이다**: 7개 채권 포트폴리오는 실제 yield 데이터를 기반으로 한 추정치(yield-based proxies)이며, FRED에서 직접 수집한 포트폴리오 수익률이 아니다. TERM/DEF에 회귀할 때 공선성이 높아 채권 R²가 높게 나타나는데, 이는 추정 방식의 고유한 한계이다. 수정 후에는 인위적으로 1.0에 가깝지는 않지만, 여전히 원 논문의 실제 채권 포트폴리오와는 다르다.
3. **Hybrid stock-side data**: 주식 factor 및 portfolio 입력은 1963-07~1968-06 기존 프로젝트/Ken French 데이터와 1968-07~1991-12 CRSP-derived stock data를 결합한 hybrid full-period 데이터이다. 이는 1963-07까지 거슬러 올라가는 full-period CRSP coverage를 의미하지 않는다.
4. **5요인 주식 절편이 높게 나타남**: Hybrid 데이터에서는 5요인 주식 모델의 평균 절대절편(0.3020%)이 1요인 주식 모델(0.2680%)보다 높다. 채권 프록시(TERM, DEF)가 주식 횡단면 pricing error를 줄이지 못하며, 3요인 주식 모델(0.1247%)이 더 우수하다.
5. **고정된 샘플 기간**: 본 복제는 원 논문의 기존 샘플(1963~1991)을 엄격히 따르며, 현대 데이터로 확장하지 않는다.
6. **인샘플(In-Sample) 검정만 수행**: 모든 회귀분석과 GRS 검정은 1963~1991년 전체 샘플 기간에 대해 인샘플로 수행되었다. 아웃오브샘플(OOS) 검정, 롤링 윈도우(rolling window) 분석, 교차검증(cross-validation) 등은 구현되지 않았다. 이는 원 논문의 방법론을 엄격히 복제한 결과이며, 향후 연구에서는 OOS 검정을 통해 모델의 예측력과 견고성을 추가로 평가할 필요가 있다. 특히 5요인 모델의 과적합 우려는 OOS 환경에서 더욱 명확히 드러날 수 있다.

---

## 6. 데이터 출처 (Data Sources)

### 6.1 주식 데이터: Hybrid Ken French + CRSP-derived stock-side data
- **Coverage**: 1963-07~1991-12, 342개월
- **Hybrid rule**:
  - 1963-07~1968-06: 기존 프로젝트/Ken French stock-side 데이터 유지
  - 1968-07~1991-12: `crsp/FF1993_results/data/crsp_*`의 CRSP-derived stock-side 데이터 사용
- **Final input files used by scripts**:
  - `data/ff_factors.csv`
  - `data/ff_6_portfolios.csv`
  - `data/ff_25_portfolios.csv`
- **CRSP-derived source files**:
  - `crsp/FF1993_results/data/crsp_ff_factors.csv`
  - `crsp/FF1993_results/data/crsp_6_portfolios.csv`
  - `crsp/FF1993_results/data/crsp_25_portfolios.csv`
- **Backups**:
  - Original project stock-side inputs: `data/backups/2026-05-15-pre-crsp-hybrid/`
  - Pre-hybrid outputs: `output/backups/2026-05-15-pre-crsp-hybrid/`
- **Important**: 이 접근은 full target period를 유지하기 위한 hybrid substitution이며, 1963-07~1968-06 구간의 CRSP-derived coverage를 주장하지 않는다.

#### Ken French source details
- **Base URL**: `https://mba.tuck.dartmouth.edu/pages/Faculty/ken.french/ftp/`
- **Download method**: `download_data.py` uses `urllib` to download ZIP files, then extracts CSVs
- **Files used**:
  1. **F-F_Research_Data_Factors_CSV.zip**
     - Contents: Fama-French 3 Factors (월간) + Risk-Free Rate
     - Columns: `Mkt-RF`, `SMB`, `HML`, `RF`
     - Format: CSV inside ZIP, skip first 3 rows (header rows)
     - Saved locally as: `data/ff_factors.csv`
  2. **6_Portfolios_2x3_CSV.zip**
     - Contents: 6 portfolios formed on Size and Book-to-Market (2×3)
     - Used for: constructing SMB and HML factors
     - Format: CSV inside ZIP, skip first 12 rows
     - Saved locally as: `data/ff_6_portfolios.csv`
  3. **25_Portfolios_5x5_CSV.zip**
     - Contents: 25 portfolios formed on Size and BE/ME (5×5)
     - Used for: regression test assets (Table 1-5)
     - Format: CSV inside ZIP, skip first 12 rows
     - Saved locally as: `data/ff_25_portfolios.csv`
- **Parser**: `ken_french_parser.py` handles value-weighted (`vw`) returns, skips header rows, parses dates

### 6.2 채권 요인 데이터: FRED (Federal Reserve Economic Data)
- **API**: `pandas_datareader.DataReader` with `data_source='fred'`
- **Series used**:
  1. **GS10** — 10-Year Treasury Constant Maturity Rate
     - Description: 미국 10년 만기 국채 변동수익률 (월간 평균)
     - Frequency: Monthly
     - Units: Percent (annualized)
     - Used for: TERM factor (long-term yield component)
  2. **TB3MS** — 3-Month Treasury Bill Secondary Market Rate
     - Description: 미국 3개월 만기 국채 수익률 (월간 평균)
     - Frequency: Monthly
     - Units: Percent (annualized)
     - Used for: TERM factor (short-term yield component) and risk-free rate proxy
  3. **BAA** — Moody's Seasoned Baa Corporate Bond Yield
     - Description: Moody's Baa 등급 회사채 수익률 (월간 평균)
     - Frequency: Monthly
     - Units: Percent (annualized)
     - Source period: 1919-01 to present
     - Used for: DEF factor (high-yield corporate component)
  4. **AAA** — Moody's Seasoned Aaa Corporate Bond Yield
     - Description: Moody's Aaa 등급 회사채 수익률 (월간 평균)
     - Frequency: Monthly
     - Units: Percent (annualized)
     - Source period: 1919-01 to present
     - Used for: DEF factor (investment-grade corporate component)
- **Saved locally**: `data/bond_factors.csv` (columns: `Date`, `TERM`, `DEF`)
- **Computation**:
  - `TERM = GS10 - TB3MS` (term spread in decimal monthly terms)
  - `DEF = BAA - AAA` (credit spread in decimal monthly terms)

### 6.3 데이터 한계 및 대체
- **CRSP 채권 데이터 접근 불가**: 원 논문은 CRSP의 월간 채권 포트폴리오 수익률 데이터를 사용했으나, 이는 상용 라이선스가 필요하며 공개적으로 접근할 수 없다. 본 복제는 이를 FRED의 수익률(yield) 데이터로 대체하여 프록시를 구성한다.
- **Hybrid stock-side substitution**: 현재 `data/ff_*` 파일은 hybrid stock-side 입력이다. 기존 Ken French-only 입력은 backup 디렉토리에 보존되어 있다.
- **데이터 저장 위치**: 최종 분석 입력은 `data/` 디렉토리에 CSV 형태로 저장된다. CRSP-derived source CSV는 `crsp/FF1993_results/data/`에 둔다.

---

## 7. 인용

```bibtex
@article{fama1993common,
  title={Common risk factors in the returns on stocks and bonds},
  author={Fama, Eugene F and French, Kenneth R},
  journal={Journal of Financial Economics},
  volume={33},
  number={1},
  pages={3--56},
  year={1993},
  publisher={Elsevier}
}
```

---

## License

본 복제 자료는 학술 및 교육 목적으로 제공됩니다.
