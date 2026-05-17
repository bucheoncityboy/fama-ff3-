"""
config.py
Fama-French (1993) replication project configuration
"""

import os

# ============================================================
# 경로 설정
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'appendix_output')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 분석 파라미터
# ============================================================
START_DATE = '1963-07'
END_DATE = '1991-12'
N_MONTHS = 342

# Ken French Data Library base URL
FF_DATA_URL = 'https://mba.tuck.dartmouth.edu/pages/Faculty/ken.french/ftp/'
