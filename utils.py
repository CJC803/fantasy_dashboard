import pandas as pd
import streamlit as st

# === Replace these with your own CSV export URLs ===
STANDINGS_URL = "https://docs.google.com/spreadsheets/d/18JjC_OdQrs1uu4hrUdUTm_4CGhy3kPIm3EOPAC9b18U/export?format=csv&gid=1760588931"
ALLPLAY_URL   = "https://docs.google.com/spreadsheets/d/18JjC_OdQrs1uu4hrUdUTm_4CGhy3kPIm3EOPAC9b18U/export?format=csv&gid=457551150"
INJURIES_URL  = "https://docs.google.com/spreadsheets/d/18JjC_OdQrs1uu4hrUdUTm_4CGhy3kPIm3EOPAC9b18U/export?format=csv&gid=818211409"
POWER_URL     = "https://docs.google.com/spreadsheets/d/18JjC_OdQrs1uu4hrUdUTm_4CGhy3kPIm3EOPAC9b18U/export?format=csv&gid=1068946133"
MATCHUPS_URL  = "https://docs.google.com/spreadsheets/d/18JjC_OdQrs1uu4hrUdUTm_4CGhy3kPIm3EOPAC9b18U/export?format=csv&gid=1393390675"
TRANSACTIONS_URL = "https://docs.google.com/spreadsheets/d/18JjC_OdQrs1uu4hrUdUTm_4CGhy3kPIm3EOPAC9b18U/export?format=csv&gid=622740068"
@st.cache_data(ttl=300)
def load_csv(url):
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.warning(f"⚠️ Could not load {url}: {e}")
        return pd.DataFrame()

def load_all():
    return {
        "standings": load_csv(STANDINGS_URL),
        "allplay":   load_csv(ALLPLAY_URL),
        "injuries":  load_csv(INJURIES_URL),
        "power":     load_csv(POWER_URL),
        "matchups":  load_csv(MATCHUPS_URL),
    }

def week_selector(df, week_col="week", default_week=None):
    """
    Creates a Streamlit week selector with optional default value.
    If default_week isn't found, defaults to the last available week.
    """
    weeks = sorted(df[week_col].dropna().unique())

    # Pick default index
    if default_week in weeks:
        default_index = weeks.index(default_week)
    else:
        default_index = len(weeks) - 1  # last week if default missing

    return st.selectbox(
        "Select Week",
        options=weeks,
        index=default_index if weeks else 0,
        key="week_selector"
    )

