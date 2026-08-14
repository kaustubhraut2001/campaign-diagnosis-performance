import os
import pandas as pd
import numpy as np

class DataCleaner:
    """
    Data Cleaning & Pipeline Module for Campaign Performance Diagnostic Engine.
    Handles uncleaned CSV dataset: date format variations, inconsistent channel naming,
    whitespace/casing variations, missing values, duplicate rows, and derived metrics calculation.
    """
    
    CHANNEL_MAP = {
        'meta': 'Meta',
        'meta ': 'Meta',
        'fb': 'Meta',
        'facebook': 'Meta',
        'google search': 'Google Search',
        'google display': 'Google Display',
        'google pmax': 'Google PMax',
        'pmax': 'Google PMax',
        'youtube': 'YouTube'
    }

    def __init__(self, data_path: str = None):
        if data_path is None:
            # Default paths lookup
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "..", "campaign-performance-diagnostic", "data", "campaign_performance.csv"),
                os.path.join(os.path.dirname(__file__), "..", "data", "campaign_performance.csv"),
                os.path.join("data", "campaign_performance.csv"),
                r"d:\Company Assignment\campaign-performance-diagnostic\campaign-performance-diagnostic\data\campaign_performance.csv"
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    data_path = p
                    break
        
        self.data_path = data_path

    def load_and_clean(self):
        if not self.data_path or not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Campaign dataset not found at path: {self.data_path}")

        raw_df = pd.read_csv(self.data_path)
        initial_rows = len(raw_df)
        audit_report = {
            "initial_rows": initial_rows,
            "nulls_fixed": {},
            "duplicates_removed": 0,
            "channels_unified": set(),
            "date_range": None
        }

        df = raw_df.copy()

        # 1. Clean String Columns (Whitespace & Casing)
        string_cols = ['campaign_id', 'campaign_name', 'channel', 'objective', 'creative_id', 'city', 'tier', 'device', 'age_group', 'gender']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Title-case / standard capitalization for City & Tier
        df['city'] = df['city'].str.title()
        df['tier'] = df['tier'].str.title()
        df['device'] = df['device'].str.title()

        # 2. Canonicalize Channel Names
        def clean_channel(ch):
            c_lower = str(ch).strip().lower()
            return self.CHANNEL_MAP.get(c_lower, str(ch).strip())

        raw_channels = df['channel'].unique()
        df['channel'] = df['channel'].apply(clean_channel)
        audit_report["channels_unified"] = list(df['channel'].unique())

        # 3. Handle Dates
        df['date_raw'] = df['date']
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        # If there are any unparsed dates, try alternative formats
        if df['date'].isnull().any():
            df['date'] = df['date'].fillna(pd.to_datetime(df['date_raw'], format='%d/%m/%Y', errors='coerce'))
            df['date'] = df['date'].fillna(pd.to_datetime(df['date_raw'], format='%m-%d-%Y', errors='coerce'))

        df = df.drop(columns=['date_raw'])

        # 4. Handle Numeric Columns & Nulls
        numeric_cols = ['impressions', 'clicks', 'spend_inr', 'conversions', 'revenue_inr']
        for col in numeric_cols:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    audit_report["nulls_fixed"][col] = int(null_count)
                    df[col] = df[col].fillna(0.0)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # 5. Remove Duplicates
        df_no_dups = df.drop_duplicates()
        audit_report["duplicates_removed"] = initial_rows - len(df_no_dups)
        df = df_no_dups.copy()

        # 6. Sort by Date
        df = df.sort_values(by='date').reset_index(drop=True)

        min_date = df['date'].min().strftime('%Y-%m-%d') if not df['date'].empty else 'N/A'
        max_date = df['date'].max().strftime('%Y-%m-%d') if not df['date'].empty else 'N/A'
        audit_report["date_range"] = f"{min_date} to {max_date}"
        audit_report["final_rows"] = len(df)

        # 7. Derived Helper Columns
        df['year_month'] = df['date'].dt.strftime('%Y-%m')
        df['year_week'] = df['date'].dt.strftime('%Y-W%U')
        df['ctr'] = np.where(df['impressions'] > 0, df['clicks'] / df['impressions'], 0.0)
        df['cpc'] = np.where(df['clicks'] > 0, df['spend_inr'] / df['clicks'], 0.0)
        df['cpa'] = np.where(df['conversions'] > 0, df['spend_inr'] / df['conversions'], 0.0)
        df['roas'] = np.where(df['spend_inr'] > 0, df['revenue_inr'] / df['spend_inr'], 0.0)
        df['cvr'] = np.where(df['clicks'] > 0, df['conversions'] / df['clicks'], 0.0)

        return df, audit_report

if __name__ == '__main__':
    cleaner = DataCleaner()
    df, report = cleaner.load_and_clean()
    print("Data Cleaned Successfully!")
    print(f"Final Shape: {df.shape}")
    print("Report:", report)
