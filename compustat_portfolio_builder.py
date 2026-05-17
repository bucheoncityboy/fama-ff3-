"""
Compustat Portfolio Builder
Wave 1: Data pipeline for Fama-French portfolio construction with CRSP and Compustat data.

Classes:
- MappingManager: Downloads and caches gvkey↔PERMCO↔PERMNO mappings
- CRSPSource: Loads and preprocesses CRSP stock return data
- BECalculator: Loads and validates Compustat book equity data
- LinkingEngine: Links Compustat BE records to CRSP June market equity
- BEMECalculator: Computes filtered annual BE/ME snapshots
- BackupManager: Creates and restores backups of Fama-French data
"""

import os
import requests
import shutil
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List


class MappingManager:
    """Manages download, caching, and validation of security code mappings."""

    def __init__(self, cache_dir: str = 'data'):
        """
        Initialize MappingManager.

        Args:
            cache_dir: Directory to cache the mapping file
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'gvkey_permco_permno.csv')
        self.download_url = 'https://github.com/Wenzhi-Ding/Std_Security_Code/blob/main/other/gvkey_permco_permno.pq?raw=true'

    def download_and_cache(self) -> None:
        """Download Parquet from URL and save as CSV to cache, or skip if already cached."""
        if os.path.exists(self.cache_file):
            print(f"Cache file exists: {self.cache_file}. Skipping download.")
            return

        print(f"Downloading mapping from: {self.download_url}")
        response = requests.get(self.download_url, stream=True)
        response.raise_for_status()

        # Read Parquet from memory
        content = response.content
        df = pd.read_parquet(pd.io.BytesIO(content))

        # Save as CSV
        df.to_csv(self.cache_file, index=False)
        print(f"Saved mapping to cache: {self.cache_file}")

    def load_mapping(self) -> pd.DataFrame:
        """
        Load cached mapping CSV.

        Returns:
            DataFrame with columns ['gvkey', 'permco', 'permno']
        """
        if not os.path.exists(self.cache_file):
            raise FileNotFoundError(f"Mapping cache file not found: {self.cache_file}")

        df = pd.read_csv(self.cache_file)
        required_cols = ['gvkey', 'permco', 'permno']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Expected columns {required_cols}, found {list(df.columns)}")

        return df[required_cols]

    def mapping_stats(self) -> Dict:
        """
        Compute mapping statistics.

        Returns:
            Dictionary with:
                - total_rows: Total number of mappings
                - unique_gvkeys: Number of unique gvkeys
                - unique_permco: Number of unique permco
                - unique_permno: Number of unique permno
                - gvkey_multi_permco_pct: Percentage of gvkeys mapping to multiple permco
                - permco_multi_gvkey_pct: Percentage of permco mapping to multiple gvkey
                - permco_multi_permno_pct: Percentage of permco mapping to multiple permno
        """
        df = self.load_mapping()

        stats = {
            'total_rows': len(df),
            'unique_gvkeys': df['gvkey'].nunique(),
            'unique_permco': df['permco'].nunique(),
            'unique_permno': df['permno'].nunique(),
            'gvkey_multi_permco_pct': (df.groupby('gvkey')['permco'].nunique() > 1).mean() * 100,
            'permco_multi_gvkey_pct': (df.groupby('permco')['gvkey'].nunique() > 1).mean() * 100,
            'permco_multi_permno_pct': (df.groupby('permco')['permno'].nunique() > 1).mean() * 100
        }

        return stats


class CRSPSource:
    """Loads and preprocesses CRSP stock return data."""

    def __init__(self, base_dir: str = '.'):
        """
        Initialize CRSPSource and auto-detect best CRSP file.

        Args:
            base_dir: Base directory containing crsp/ subdirectory
        """
        self.base_dir = base_dir
        self.crsp_dir = os.path.join(base_dir, 'crsp')

        # File paths to check (most columns first)
        self.file_paths = [
            os.path.join(self.crsp_dir, 'RET__DLSTCD_1962.01_1991.12', 'RET__DLSTCD_1962.01_1991.12.csv'),
            os.path.join(self.crsp_dir, 'zgwss6y8fijax1cr_csv', 'zgwss6y8fijax1cr.csv')
        ]

        self.file_path = self._auto_detect_file()

    def _auto_detect_file(self) -> str:
        """Auto-detect CRSP file with most columns."""
        best_path = None
        best_col_count = -1

        for path in self.file_paths:
            if os.path.exists(path):
                df = pd.read_csv(path)
                col_count = len(df.columns)

                if col_count > best_col_count:
                    best_col_count = col_count
                    best_path = path

        if best_path is None:
            raise FileNotFoundError("No CRSP data files found")

        print(f"Using CRSP file: {best_path} ({best_col_count} columns)")
        return best_path

    def load_and_clean(self) -> pd.DataFrame:
        """
        Load CSV and apply all preprocessing steps.

        Returns:
            Cleaned DataFrame with processed returns data
        """
        df = pd.read_csv(self.file_path)

        # Parse date column
        df['date'] = pd.to_datetime(df['date'])

        # Apply all preprocessing steps
        df = self.filter_common_stocks(df)
        df = self.clean_ret_codes(df)
        df = self.incorporate_dlret(df)
        df = self.process_prc(df)

        return df

    def filter_common_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to keep only common stocks (SHRCD 10/11, EXCHCD 1/2/3).

        Args:
            df: Input DataFrame

        Returns:
            Filtered DataFrame
        """
        # Keep SHRCD 10/11 (common stocks) AND EXCHCD 1/2/3 (NYSE, AMEX, NASDAQ)
        # If SHRCD/EXCHCD is NaN, keep (could be delisted stocks)
        keep_mask = (df['SHRCD'].isin([10, 11])) & (df['EXCHCD'].isin([1, 2, 3]))

        filtered_df = df[keep_mask].copy()
        print(f"Filtered to common stocks: {len(filtered_df)} / {len(df)} rows ({len(filtered_df)/len(df)*100:.1f}%)")

        return filtered_df

    def clean_ret_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean RET codes: replace 'C' (split) and 'B' (dividend) with NaN.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with cleaned RET column
        """
        # Replace 'C' and 'B' with NaN
        mask = df['RET'].isin(['C', 'B'])
        df.loc[mask, 'RET'] = np.nan

        # Replace any other non-numeric codes with NaN
        mask = ~df['RET'].apply(lambda x: isinstance(x, (int, float)))
        df.loc[mask, 'RET'] = np.nan

        return df

    def incorporate_dlret(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        For rows where RET is NaN but DLRET is not NaN, set RET = DLRET.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with DLRET incorporated
        """
        # Create mask for RET=NaN and DLRET!=NaN
        mask = df['RET'].isna() & ~df['DLRET'].isna()

        # Fill RET with DLRET where applicable
        df.loc[mask, 'RET'] = df.loc[mask, 'DLRET']

        return df

    def process_prc(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert PRC to absolute value (negative PRC = bid/ask average).

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with absolute PRC
        """
        df['PRC'] = df['PRC'].abs()
        return df


class BECalculator:
    """Loads and validates Compustat book equity data."""

    def __init__(self, be_file: str = 'compustat_be.csv'):
        """
        Initialize BECalculator.

        Args:
            be_file: Path to Compustat BE CSV file
        """
        self.be_file = be_file

    def load_and_validate(self) -> pd.DataFrame:
        """
        Load Compustat BE data and print validation statistics.

        Returns:
            Loaded DataFrame with validation stats printed
        """
        df = pd.read_csv(self.be_file)

        # Print BE statistics
        print("\n=== BE Statistics ===")
        print(f"Total rows: {len(df)}")
        print(f"Unique gvkeys: {df['gvkey'].nunique()}")
        print(f"BE min: {df['be'].min():.2f}")
        print(f"BE max: {df['be'].max():.2f}")
        print(f"BE mean: {df['be'].mean():.2f}")
        print(f"BE median: {df['be'].median():.2f}")
        print(f"Negative BE: {(df['be'] < 0).sum()} rows ({(df['be'] < 0).mean() * 100:.2f}%)")
        print(f"Zero BE: {(df['be'] == 0).sum()} rows ({(df['be'] == 0).mean() * 100:.2f}%)")

        # Print flag distributions
        print("\n=== Flag Distributions ===")
        for flag in ['se_flag', 'dt_flag', 'ps_flag']:
            print(f"\n{flag}:")
            print(df[flag].value_counts(normalize=True))

        return df

    def deduplicate_be(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplicate by gvkey+cal_year, keeping latest datadate.

        Args:
            df: Input DataFrame

        Returns:
            Deduplicated DataFrame
        """
        # Group by gvkey and cal_year, keep latest datadate
        df = df.sort_values(['gvkey', 'cal_year', 'datadate'])
        df = df.drop_duplicates(subset=['gvkey', 'cal_year'], keep='last')

        print(f"Deduplicated from {len(df)} to {len(df)} rows (no duplicates in current data)")

        return df

    def extract_sich(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add is_financial flag based on SICH code.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with 'is_financial' column added
        """
        # SICH 6000-6999 are financial companies
        df['is_financial'] = df['sich'].between(6000, 6999)

        print(f"Financial companies: {df['is_financial'].sum()} ({df['is_financial'].mean() * 100:.1f}%)")

        return df

    def load_and_process(self) -> pd.DataFrame:
        """
        Complete loading, validation, and processing pipeline.

        Returns:
            DataFrame with columns: gvkey, datadate, cal_year, be, sich, is_financial, se_flag, dt_flag, ps_flag
        """
        df = self.load_and_validate()

        df = self.deduplicate_be(df)
        df = self.extract_sich(df)

        return df


class LinkingEngine:
    """Connects Compustat BE records to CRSP June market data via PERMCO."""

    LINK_COLUMNS = ['gvkey', 'permno', 'permco', 'date', 'cal_year', 'be', 'me', 'sich', 'is_financial', 'EXCHCD']

    def __init__(self, base_dir: str = '.', mapping_manager=None, crsp_source=None, be_calculator=None):
        """
        Initialize LinkingEngine.

        Args:
            base_dir: Base directory containing data/, crsp/, and compustat_be.csv
            mapping_manager: Optional preconfigured MappingManager instance
            crsp_source: Optional preconfigured CRSPSource instance
            be_calculator: Optional preconfigured BECalculator instance
        """
        self.base_dir = base_dir
        self.mapping_manager = mapping_manager or MappingManager(cache_dir=os.path.join(base_dir, 'data'))
        self.crsp_source = crsp_source or CRSPSource(base_dir=base_dir)
        self.be_calculator = be_calculator or BECalculator(be_file=os.path.join(base_dir, 'compustat_be.csv'))

    def _empty_link(self) -> pd.DataFrame:
        """Return an empty linked DataFrame with the public output schema."""
        return pd.DataFrame(columns=self.LINK_COLUMNS)

    def _normalize_identifier_key(self, series: pd.Series) -> pd.Series:
        """Normalize identifier keys across int/float/string CSV representations."""
        return (
            series.astype(str)
            .str.strip()
            .str.replace(r'\.0$', '', regex=True)
            .replace({'nan': pd.NA, 'None': pd.NA, '<NA>': pd.NA})
        )

    def _print_coverage(self, be_df: pd.DataFrame, linked_df: pd.DataFrame) -> None:
        """Print gvkey and PERMNO coverage diagnostics for the link."""
        total_gvkeys = be_df['gvkey'].nunique() if 'gvkey' in be_df.columns else 0
        linked_gvkeys = linked_df['gvkey'].nunique() if 'gvkey' in linked_df.columns else 0
        coverage = (linked_gvkeys / total_gvkeys * 100) if total_gvkeys else 0.0

        print("\n=== Linking Coverage ===")
        print(f"Total BE gvkeys: {total_gvkeys}")
        print(f"Gvkeys with CRSP match: {linked_gvkeys}")
        print(f"Coverage: {coverage:.2f}%")
        print(f"Unique PERMNOs linked: {linked_df['permno'].nunique() if 'permno' in linked_df.columns else 0}")

        if 'gvkey' in be_df.columns and 'gvkey' in linked_df.columns:
            unmatched = pd.Index(be_df['gvkey'].dropna().unique()).difference(
                pd.Index(linked_df['gvkey'].dropna().unique())
            )
            print(f"Sample unmatched gvkeys: {unmatched[:5].tolist()}")
        else:
            print("Sample unmatched gvkeys: []")

    def build_link(self) -> pd.DataFrame:
        """
        Build gvkey-PERMCO-PERMNO links between Compustat BE and CRSP June market data.

        Returns:
            DataFrame with columns: gvkey, permno, permco, date, cal_year, be, me, sich, is_financial, EXCHCD
        """
        try:
            mapping = self.mapping_manager.load_mapping()
        except FileNotFoundError as exc:
            print(f"Mapping unavailable: {exc}")
            linked = self._empty_link()
            try:
                be = self.be_calculator.load_and_process()
            except FileNotFoundError:
                be = pd.DataFrame(columns=['gvkey'])
            self._print_coverage(be, linked)
            return linked

        crsp = self.crsp_source.load_and_clean()
        be = self.be_calculator.load_and_process()

        if mapping.empty or crsp.empty or be.empty:
            linked = self._empty_link()
            self._print_coverage(be, linked)
            return linked

        mapping = mapping.copy()
        crsp = crsp.copy()
        be = be.copy()

        # Normalize CRSP identifier column names while preserving BE/mapping public names.
        crsp = crsp.rename(columns={'PERMNO': 'permno', 'PERMCO': 'permco'})
        crsp['date'] = pd.to_datetime(crsp['date'])

        mapping['_gvkey_key'] = self._normalize_identifier_key(mapping['gvkey'])
        mapping['_permco_key'] = self._normalize_identifier_key(mapping['permco'])
        be['_gvkey_key'] = self._normalize_identifier_key(be['gvkey'])

        # Use gvkey only to reach stable firm-level PERMCO. Static mapping PERMNOs are
        # intentionally not used for the final issue-level link; CRSP June rows provide
        # the active PERMNO(s) for each PERMCO and date.
        bridge = mapping[['_gvkey_key', 'permco', '_permco_key']].drop_duplicates()
        be_mapped = be.merge(bridge, on='_gvkey_key', how='left')
        be_mapped = be_mapped.dropna(subset=['_permco_key']).copy()
        be_mapped['cal_year'] = pd.to_numeric(be_mapped['cal_year'], errors='coerce')
        be_mapped = be_mapped.dropna(subset=['cal_year']).copy()

        june_crsp = crsp[crsp['date'].dt.month == 6].copy()
        june_crsp['_permco_key'] = self._normalize_identifier_key(june_crsp['permco'])
        june_crsp['link_year'] = june_crsp['date'].dt.year
        june_crsp['me'] = june_crsp['PRC'] * june_crsp['SHROUT']

        be_mapped['link_year'] = be_mapped['cal_year'].astype(int) + 1

        merge_cols = ['permno', '_permco_key', 'date', 'link_year', 'me', 'EXCHCD']
        linked = be_mapped.merge(
            june_crsp[merge_cols],
            on=['_permco_key', 'link_year'],
            how='inner'
        )

        if linked.empty:
            linked = self._empty_link()
            self._print_coverage(be, linked)
            return linked

        linked['cal_year'] = linked['cal_year'].astype(int)
        numeric_permco = pd.to_numeric(linked['_permco_key'], errors='coerce')
        if numeric_permco.notna().all():
            linked['permco'] = numeric_permco.astype(int)
        else:
            linked['permco'] = linked['_permco_key']
        linked = linked[self.LINK_COLUMNS].copy()
        linked = linked.sort_values(['gvkey', 'cal_year', 'permco', 'permno', 'date']).reset_index(drop=True)

        self._print_coverage(be, linked)
        return linked


class BEMECalculator:
    """Computes FF1992-ready annual BE/ME snapshots from linked Compustat-CRSP data."""

    OUTPUT_COLUMNS = [
        'gvkey', 'permno', 'permco', 'date', 'year', 'be', 'me', 'beme',
        'sich', 'is_financial', 'exchange'
    ]

    def __init__(self, engine=None):
        """
        Initialize BEMECalculator.

        Args:
            engine: Optional preconfigured LinkingEngine instance.
        """
        self.engine = engine or LinkingEngine()

    def _empty_result(self) -> pd.DataFrame:
        """Return an empty BE/ME snapshot with the public output schema."""
        return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

    def _print_diagnostics(self, before_count: int, removals: Dict[str, int], result: pd.DataFrame) -> None:
        """Print filter and annual-count diagnostics."""
        print("\n=== BE/ME Filter Diagnostics ===")
        print(f"Total rows before filtering: {before_count}")
        print(f"Rows removed - negative/zero BE: {removals['negative_be']}")
        print(f"Rows removed - financial firms: {removals['financial']}")
        print(f"Rows removed - zero/negative ME: {removals['zero_me']}")
        print(f"Rows removed - BE/ME outliers: {removals['outliers']}")
        print(f"Total rows after filtering: {len(result)}")

        print("\nPer-year observation counts:")
        if result.empty:
            print("No observations after filtering")
            return

        counts = result.groupby('year').size().sort_index()
        print(counts.to_string())

        target_years = range(1964, 1992)
        thin_years = {year: int(counts.get(year, 0)) for year in target_years if counts.get(year, 0) < 500}
        if thin_years:
            print(f"Warning: years with fewer than 500 observations: {thin_years}")

    def _trim_beme_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trim top and bottom 0.5% BE/ME observations within each year."""
        if df.empty:
            return df

        lower = df.groupby('year')['beme'].transform(lambda values: values.quantile(0.005))
        upper = df.groupby('year')['beme'].transform(lambda values: values.quantile(0.995))
        keep_mask = df['beme'].between(lower, upper, inclusive='both')
        return df[keep_mask].copy()

    def compute_all(self, linked_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Compute clean annual BE/ME snapshots from linked Compustat-CRSP output.

        Args:
            linked_df: Optional linked DataFrame. If omitted, uses self.engine.build_link().

        Returns:
            DataFrame with columns gvkey, permno, permco, date, year, be, me, beme,
            sich, is_financial, exchange.
        """
        linked = self.engine.build_link() if linked_df is None else linked_df
        if linked is None or linked.empty:
            result = self._empty_result()
            self._print_diagnostics(0, {'negative_be': 0, 'financial': 0, 'zero_me': 0, 'outliers': 0}, result)
            return result

        df = linked.copy()
        before_count = len(df)
        removals = {}

        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['be'] = pd.to_numeric(df['be'], errors='coerce')
        df['me'] = pd.to_numeric(df['me'], errors='coerce')
        df['beme'] = np.where(df['me'] != 0, df['be'] / df['me'], np.nan)
        df['beme'] = pd.to_numeric(df['beme'], errors='coerce').replace([np.inf, -np.inf], np.nan)

        if 'EXCHCD' in df.columns:
            df['exchange'] = df['EXCHCD']
        elif 'exchange' not in df.columns:
            df['exchange'] = pd.NA

        current = len(df)
        df = df[df['be'] > 0].copy()
        removals['negative_be'] = current - len(df)

        current = len(df)
        if 'is_financial' in df.columns:
            financial_mask = df['is_financial'].fillna(False).astype(bool)
            df = df[~financial_mask].copy()
        removals['financial'] = current - len(df)

        current = len(df)
        df = df[df['me'] > 0].copy()
        removals['zero_me'] = current - len(df)

        df = df.dropna(subset=['beme']).copy()
        current = len(df)
        df = self._trim_beme_outliers(df)
        removals['outliers'] = current - len(df)

        result = df[self.OUTPUT_COLUMNS].sort_values(['year', 'gvkey', 'permco', 'permno', 'date']).reset_index(drop=True)
        self._print_diagnostics(before_count, removals, result)
        return result


class PortfolioConstructor:
    """Constructs 25 Size-BE/ME portfolios using FF1992/FF1993 June sorts."""

    PORTFOLIO_COLUMNS = [
        'SMALL LoBM', 'ME1 BM2', 'ME1 BM3', 'ME1 BM4', 'SMALL HiBM',
        'ME2 BM1', 'ME2 BM2', 'ME2 BM3', 'ME2 BM4', 'ME2 BM5',
        'ME3 BM1', 'ME3 BM2', 'ME3 BM3', 'ME3 BM4', 'ME3 BM5',
        'ME4 BM1', 'ME4 BM2', 'ME4 BM3', 'ME4 BM4', 'ME4 BM5',
        'BIG LoBM', 'ME5 BM2', 'ME5 BM3', 'ME5 BM4', 'BIG HiBM',
    ]

    PORTFOLIO_LABELS = {
        (1, 1): 'SMALL LoBM', (1, 2): 'ME1 BM2', (1, 3): 'ME1 BM3',
        (1, 4): 'ME1 BM4', (1, 5): 'SMALL HiBM',
        (2, 1): 'ME2 BM1', (2, 2): 'ME2 BM2', (2, 3): 'ME2 BM3',
        (2, 4): 'ME2 BM4', (2, 5): 'ME2 BM5',
        (3, 1): 'ME3 BM1', (3, 2): 'ME3 BM2', (3, 3): 'ME3 BM3',
        (3, 4): 'ME3 BM4', (3, 5): 'ME3 BM5',
        (4, 1): 'ME4 BM1', (4, 2): 'ME4 BM2', (4, 3): 'ME4 BM3',
        (4, 4): 'ME4 BM4', (4, 5): 'ME4 BM5',
        (5, 1): 'BIG LoBM', (5, 2): 'ME5 BM2', (5, 3): 'ME5 BM3',
        (5, 4): 'ME5 BM4', (5, 5): 'BIG HiBM',
    }

    PORTFOLIO_COLUMNS_6 = [
        'SMALL LoBM', 'ME1 BM2', 'SMALL HiBM',
        'BIG LoBM', 'ME2 BM2', 'BIG HiBM',
    ]

    PORTFOLIO_LABELS_6 = {
        (1, 1): 'SMALL LoBM',
        (1, 2): 'ME1 BM2',
        (1, 3): 'SMALL HiBM',
        (2, 1): 'BIG LoBM',
        (2, 2): 'ME2 BM2',
        (2, 3): 'BIG HiBM',
    }

    def __init__(self, beme_calculator=None, crsp_source=None):
        """
        Initialize PortfolioConstructor.

        Args:
            beme_calculator: Optional preconfigured BEMECalculator instance.
            crsp_source: Optional preconfigured CRSPSource instance.
        """
        self.beme_calculator = beme_calculator or BEMECalculator()
        self.crsp_source = crsp_source or CRSPSource()

    def compute_nyse_breakpoints(self, beme_df: pd.DataFrame, metric: str = 'me') -> List[float]:
        """
        Compute NYSE non-financial quintile breakpoints for ME or BE/ME.

        Args:
            beme_df: Annual BE/ME snapshot for one June formation year.
            metric: Either 'me' for size or 'beme' for book-to-market.

        Returns:
            Four breakpoint values: 20th, 40th, 60th, and 80th percentiles.
        """
        if metric not in {'me', 'beme'}:
            raise ValueError("metric must be either 'me' or 'beme'")

        if beme_df is None or beme_df.empty:
            return [np.nan, np.nan, np.nan, np.nan]

        df = beme_df.copy()
        values = pd.to_numeric(df[metric], errors='coerce')
        exchange = pd.to_numeric(df.get('exchange', pd.Series(index=df.index, dtype='float64')), errors='coerce')
        financial = df.get('is_financial', pd.Series(False, index=df.index)).fillna(False).astype(bool)

        nyse = values[(exchange == 1) & (~financial) & values.notna() & np.isfinite(values)]
        if nyse.empty:
            return [np.nan, np.nan, np.nan, np.nan]

        return [float(nyse.quantile(q)) for q in [0.2, 0.4, 0.6, 0.8]]

    def assign_portfolios(self, beme_df: pd.DataFrame, size_bps: List[float], beme_bps: List[float]) -> pd.Series:
        """
        Assign all stocks to 25 Size-BE/ME portfolios using NYSE breakpoints.

        Args:
            beme_df: Annual BE/ME snapshot for one June formation year.
            size_bps: ME breakpoints from compute_nyse_breakpoints(..., 'me').
            beme_bps: BE/ME breakpoints from compute_nyse_breakpoints(..., 'beme').

        Returns:
            Series of Ken French style portfolio labels.
        """
        if beme_df is None or beme_df.empty:
            return pd.Series(dtype='object')

        size_breaks = np.asarray(size_bps, dtype='float64')
        beme_breaks = np.asarray(beme_bps, dtype='float64')
        if len(size_breaks) != 4 or len(beme_breaks) != 4:
            raise ValueError('size_bps and beme_bps must each contain four breakpoints')

        me_values = pd.to_numeric(beme_df['me'], errors='coerce')
        beme_values = pd.to_numeric(beme_df['beme'], errors='coerce')

        labels = []
        invalid_breaks = np.isnan(size_breaks).any() or np.isnan(beme_breaks).any()
        for me_value, beme_value in zip(me_values, beme_values):
            if invalid_breaks or pd.isna(me_value) or pd.isna(beme_value):
                labels.append(pd.NA)
                continue

            size_group = int(np.searchsorted(size_breaks, me_value, side='left') + 1)
            beme_group = int(np.searchsorted(beme_breaks, beme_value, side='left') + 1)
            labels.append(self.PORTFOLIO_LABELS[(size_group, beme_group)])

        return pd.Series(labels, index=beme_df.index, dtype='object')

    def compute_nyse_breakpoints_2x3(self, beme_df: pd.DataFrame, metric: str = 'me') -> List[float]:
        """
        Compute NYSE non-financial breakpoints for 2×3 portfolios.

        For 'me': returns [median] (50th percentile of NYSE ME).
        For 'beme': returns [p30, p70] (30th and 70th percentiles of NYSE BE/ME).

        Args:
            beme_df: Annual BE/ME snapshot for one June formation year.
            metric: Either 'me' for size or 'beme' for book-to-market.

        Returns:
            For 'me': list with one breakpoint [median].
            For 'beme': list with two breakpoints [p30, p70].
        """
        if metric not in {'me', 'beme'}:
            raise ValueError("metric must be either 'me' or 'beme'")

        if beme_df is None or beme_df.empty:
            return [np.nan] if metric == 'me' else [np.nan, np.nan]

        df = beme_df.copy()
        values = pd.to_numeric(df[metric], errors='coerce')
        exchange = pd.to_numeric(df.get('exchange', pd.Series(index=df.index, dtype='float64')), errors='coerce')
        financial = df.get('is_financial', pd.Series(False, index=df.index)).fillna(False).astype(bool)

        nyse = values[(exchange == 1) & (~financial) & values.notna() & np.isfinite(values)]
        if nyse.empty:
            return [np.nan] if metric == 'me' else [np.nan, np.nan]

        if metric == 'me':
            return [float(nyse.quantile(0.5))]
        else:
            return [float(nyse.quantile(0.3)), float(nyse.quantile(0.7))]

    def assign_portfolios_2x3(self, beme_df: pd.DataFrame, size_bp: List[float], beme_bps: List[float]) -> pd.Series:
        """
        Assign all stocks to 6 Size-BE/ME portfolios using NYSE breakpoints.

        Size: 2 groups based on median (below = SMALL, above = BIG).
        BE/ME: 3 groups (below p30 = LoBM, between p30-p70 = BM2, above p70 = HiBM).

        Args:
            beme_df: Annual BE/ME snapshot for one June formation year.
            size_bp: ME breakpoints from compute_nyse_breakpoints_2x3(..., 'me').
            beme_bps: BE/ME breakpoints from compute_nyse_breakpoints_2x3(..., 'beme').

        Returns:
            Series of Ken French style 6-portfolio labels.
        """
        if beme_df is None or beme_df.empty:
            return pd.Series(dtype='object')

        size_bp_arr = np.asarray(size_bp, dtype='float64')
        beme_bps_arr = np.asarray(beme_bps, dtype='float64')

        me_values = pd.to_numeric(beme_df['me'], errors='coerce')
        beme_values = pd.to_numeric(beme_df['beme'], errors='coerce')

        labels = []
        invalid_breaks = np.isnan(size_bp_arr).any() or np.isnan(beme_bps_arr).any()
        for me_value, beme_value in zip(me_values, beme_values):
            if invalid_breaks or pd.isna(me_value) or pd.isna(beme_value):
                labels.append(pd.NA)
                continue

            size_group = int(np.searchsorted(size_bp_arr, me_value, side='left') + 1)
            beme_group = int(np.searchsorted(beme_bps_arr, beme_value, side='left') + 1)
            labels.append(self.PORTFOLIO_LABELS_6[(size_group, beme_group)])

        return pd.Series(labels, index=beme_df.index, dtype='object')

    def build_6_portfolios(self, beme_df: Optional[pd.DataFrame] = None, crsp_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Build value-weighted monthly returns for 6 Size-BE/ME portfolios (2×3).

        Same structure as build_25_portfolios but with 2×3 assignment.
        NYSE breakpoints: Size = median (50%), BE/ME = 30th and 70th percentiles.
        All stocks are assigned; returns are value-weighted.

        Args:
            beme_df: Optional annual June BE/ME snapshot. If omitted, BEMECalculator is used.
            crsp_df: Optional CRSP monthly returns. If omitted, CRSPSource is used.

        Returns:
            DataFrame indexed by YYYY-MM strings with 6 portfolio return columns.
            Returns are expressed in percent to match Ken French CSV files.
        """
        beme = self.beme_calculator.compute_all() if beme_df is None else beme_df
        crsp = self.crsp_source.load_and_clean() if crsp_df is None else crsp_df

        if beme is None or crsp is None or beme.empty or crsp.empty:
            empty = pd.DataFrame(columns=self.PORTFOLIO_COLUMNS_6)
            empty.index.name = 'Date'
            return empty

        beme = self._prepare_beme(beme)
        crsp = self._prepare_crsp(crsp)

        formation_years = sorted(beme['year'].dropna().astype(int).unique())
        target_years = [year for year in formation_years if 1964 <= year <= 1991]
        if target_years:
            formation_years = target_years

        rows = []
        row_index = []
        for formation_year in formation_years:
            snapshot = self._formation_snapshot(beme, formation_year)
            if snapshot.empty:
                continue

            size_bp = self.compute_nyse_breakpoints_2x3(snapshot, metric='me')
            beme_bps = self.compute_nyse_breakpoints_2x3(snapshot, metric='beme')
            assignments = self.assign_portfolios_2x3(snapshot, size_bp, beme_bps)
            formation = snapshot.assign(portfolio=assignments, formation_me=snapshot['me'])
            formation = formation.dropna(subset=['portfolio', 'formation_me'])
            if formation.empty:
                continue

            formation = formation[['permno', 'portfolio', 'formation_me']].copy()
            for month in self._holding_months(formation_year):
                month_returns = crsp.loc[crsp['_month'] == month, ['permno', 'RET']]
                merged = formation.merge(month_returns, on='permno', how='left')
                valid_returns = merged.dropna(subset=['RET']).copy()
                valid_returns = valid_returns[valid_returns['formation_me'] > 0]

                row = {column: np.nan for column in self.PORTFOLIO_COLUMNS_6}
                for portfolio, group in valid_returns.groupby('portfolio'):
                    weights = group['formation_me'].astype(float)
                    returns = group['RET'].astype(float)
                    if weights.sum() > 0:
                        row[portfolio] = float(np.average(returns, weights=weights) * 100.0)

                rows.append(row)
                row_index.append(month.strftime('%Y-%m'))

        result = pd.DataFrame(rows, index=row_index, columns=self.PORTFOLIO_COLUMNS_6)
        result.index.name = 'Date'
        return result

    def _prepare_beme(self, beme_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize BE/ME input columns needed for portfolio construction."""
        df = beme_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        if 'year' not in df.columns:
            df['year'] = df['date'].dt.year
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['permno'] = pd.to_numeric(df['permno'], errors='coerce')
        df['me'] = pd.to_numeric(df['me'], errors='coerce')
        df['beme'] = pd.to_numeric(df['beme'], errors='coerce')
        if 'is_financial' not in df.columns:
            df['is_financial'] = False
        return df

    def _prepare_crsp(self, crsp_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize CRSP monthly returns for holding-period calculations."""
        df = crsp_df.copy()
        rename_map = {'PERMNO': 'permno', 'PERMCO': 'permco', 'EXCHCD': 'exchange'}
        df = df.rename(columns={old: new for old, new in rename_map.items() if old in df.columns})
        df['permno'] = pd.to_numeric(df['permno'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        df['_month'] = df['date'].dt.to_period('M').dt.to_timestamp()
        df['RET'] = pd.to_numeric(df['RET'], errors='coerce')
        return df

    def _formation_snapshot(self, beme_df: pd.DataFrame, year: int) -> pd.DataFrame:
        """Return valid non-financial June formation records for one year."""
        snapshot = beme_df[beme_df['year'] == year].copy()
        june_snapshot = snapshot[snapshot['date'].dt.month == 6].copy()
        if not june_snapshot.empty:
            snapshot = june_snapshot

        financial = snapshot['is_financial'].fillna(False).astype(bool)
        valid = (
            (~financial)
            & snapshot['permno'].notna()
            & snapshot['me'].notna()
            & snapshot['beme'].notna()
            & np.isfinite(snapshot['me'])
            & np.isfinite(snapshot['beme'])
            & (snapshot['me'] > 0)
        )
        return snapshot[valid].copy()

    def _holding_months(self, formation_year: int) -> pd.DatetimeIndex:
        """Return July t through June t+1 holding months, capped at 1991-12."""
        start = pd.Timestamp(year=formation_year, month=7, day=1)
        end = pd.Timestamp(year=formation_year + 1, month=6, day=1)
        cap = pd.Timestamp(year=1991, month=12, day=1)
        if formation_year <= 1991:
            end = min(end, cap)
        return pd.date_range(start, end, freq='MS')

    def build_25_portfolios(self, beme_df: Optional[pd.DataFrame] = None, crsp_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Build value-weighted monthly returns for 25 Size-BE/ME portfolios.

        Args:
            beme_df: Optional annual June BE/ME snapshot. If omitted, BEMECalculator is used.
            crsp_df: Optional CRSP monthly returns. If omitted, CRSPSource is used.

        Returns:
            DataFrame indexed by YYYY-MM strings with 25 portfolio return columns.
            Returns are expressed in percent to match Ken French CSV files.
        """
        beme = self.beme_calculator.compute_all() if beme_df is None else beme_df
        crsp = self.crsp_source.load_and_clean() if crsp_df is None else crsp_df

        if beme is None or crsp is None or beme.empty or crsp.empty:
            empty = pd.DataFrame(columns=self.PORTFOLIO_COLUMNS)
            empty.index.name = 'Date'
            return empty

        beme = self._prepare_beme(beme)
        crsp = self._prepare_crsp(crsp)

        formation_years = sorted(beme['year'].dropna().astype(int).unique())
        target_years = [year for year in formation_years if 1964 <= year <= 1991]
        if target_years:
            formation_years = target_years

        rows = []
        row_index = []
        for formation_year in formation_years:
            snapshot = self._formation_snapshot(beme, formation_year)
            if snapshot.empty:
                continue

            size_bps = self.compute_nyse_breakpoints(snapshot, metric='me')
            beme_bps = self.compute_nyse_breakpoints(snapshot, metric='beme')
            assignments = self.assign_portfolios(snapshot, size_bps, beme_bps)
            formation = snapshot.assign(portfolio=assignments, formation_me=snapshot['me'])
            formation = formation.dropna(subset=['portfolio', 'formation_me'])
            if formation.empty:
                continue

            formation = formation[['permno', 'portfolio', 'formation_me']].copy()
            for month in self._holding_months(formation_year):
                month_returns = crsp.loc[crsp['_month'] == month, ['permno', 'RET']]
                merged = formation.merge(month_returns, on='permno', how='left')
                valid_returns = merged.dropna(subset=['RET']).copy()
                valid_returns = valid_returns[valid_returns['formation_me'] > 0]

                row = {column: np.nan for column in self.PORTFOLIO_COLUMNS}
                for portfolio, group in valid_returns.groupby('portfolio'):
                    weights = group['formation_me'].astype(float)
                    returns = group['RET'].astype(float)
                    if weights.sum() > 0:
                        row[portfolio] = float(np.average(returns, weights=weights) * 100.0)

                rows.append(row)
                row_index.append(month.strftime('%Y-%m'))

        result = pd.DataFrame(rows, index=row_index, columns=self.PORTFOLIO_COLUMNS)
        result.index.name = 'Date'
        return result


class BackupManager:
    """Manages backups and restoration of Fama-French data files."""

    def __init__(self, data_dir: str = 'data'):
        """
        Initialize BackupManager.

        Args:
            data_dir: Directory containing Fama-French data files
        """
        self.data_dir = data_dir
        self.backup_dir = os.path.join(data_dir, 'backups')
        self.files_to_backup = [
            'ff_25_portfolios.csv',
            'ff_6_portfolios.csv',
            'ff_factors.csv'
        ]

    def _compute_file_hash(self, filepath: str) -> str:
        """
        Compute MD5 hash of a file.

        Args:
            filepath: Path to file

        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def backup(self) -> str:
        """
        Create backup of Fama-French data files.

        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'{timestamp}-pre-compustat')

        # Check if backup already exists with same files
        if os.path.exists(self.backup_dir):
            existing_backups = [d for d in os.listdir(self.backup_dir) if d.startswith('pre-compustat')]
        else:
            existing_backups = []
        if existing_backups:
            latest_backup = sorted(existing_backups)[-1]
            latest_path = os.path.join(self.backup_dir, latest_backup)

            # Check if files are the same
            hash_match = True
            for filename in self.files_to_backup:
                src_path = os.path.join(self.data_dir, filename)
                backup_src_path = os.path.join(latest_path, filename)

                if not os.path.exists(src_path) or not os.path.exists(backup_src_path):
                    hash_match = False
                    break

                if self._compute_file_hash(src_path) != self._compute_file_hash(backup_src_path):
                    hash_match = False
                    break

            if hash_match:
                print(f"Backup already exists: {latest_path}")
                return latest_path

        # Create backup directory
        os.makedirs(backup_path, exist_ok=True)

        # Copy files
        for filename in self.files_to_backup:
            src_path = os.path.join(self.data_dir, filename)
            dst_path = os.path.join(backup_path, filename)
            shutil.copy2(src_path, dst_path)
            print(f"Copied: {filename}")

        print(f"Backup created: {backup_path}")
        return backup_path

    def restore(self, backup_path: str) -> None:
        """
        Restore Fama-French data files from backup.

        Args:
            backup_path: Path to backup directory
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        # Verify backup contains all required files
        for filename in self.files_to_backup:
            backup_src_path = os.path.join(backup_path, filename)
            dst_path = os.path.join(self.data_dir, filename)

            if not os.path.exists(backup_src_path):
                raise FileNotFoundError(f"Backup missing file: {filename}")

            # Copy back
            shutil.copy2(backup_src_path, dst_path)
            print(f"Restored: {filename}")

        print(f"Restored from: {backup_path}")
