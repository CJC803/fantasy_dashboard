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
def week_selector(df, week_col="week", pts_col="pts", default_week=None):
    """
    Streamlit week selector that:
    - Excludes future weeks (where all pts are blank)
    - Defaults to the most recent week that has any valid points
    """
    # Convert columns safely
    df[week_col] = pd.to_numeric(df[week_col], errors="coerce")

    # Identify completed weeks — where at least one points value exists
    if pts_col in df.columns:
        df[pts_col] = pd.to_numeric(df[pts_col], errors="coerce")
        week_points = (
            df.groupby(week_col)[pts_col]
            .apply(lambda s: s.notna().any() and s.sum() > 0)
        )
        completed_weeks = week_points[week_points].index.tolist()
    else:
        completed_weeks = sorted(df[week_col].dropna().unique())

    completed_weeks = sorted(set(completed_weeks))

    # --- Default logic ---
    # Always default to last completed week (with actual data)
    if completed_weeks:
        default_week = completed_weeks[-1]
        default_index = len(completed_weeks) - 1
    else:
        default_week = None
        default_index = 0

    # --- Streamlit UI ---
    return st.selectbox(
        "Select Week",
        options=completed_weeks,
        index=default_index if completed_weeks else 0,
        key="week_selector",
    )


