import streamlit as st
import pandas as pd
from utils import load_csv, TRANSACTIONS_URL  # shared CSV loader and URL

# ---- Page Config ----
st.set_page_config(page_title="Completed Transactions", layout="wide")
st.title("📋 Completed Transactions")

# ---- Data Load ----
@st.cache_data(ttl=300)
def load_transactions():
    """Load transactions_completed CSV from Google Sheets."""
    return load_csv(TRANSACTIONS_URL)

with st.spinner("Loading transactions..."):
    df = load_transactions()

# ---- Handle empty data ----
if df.empty:
    st.info("No completed transactions found.")
else:
    # ---- Summary Metrics ----
    st.subheader("Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total Transactions", f"{len(df):,}")
    col2.metric("Unique Teams", df["team"].nunique())

    # ---- Filters ----
    st.subheader("Filters")
    teams = st.multiselect("Filter by team", sorted(df["team"].unique()))
    txn_types = st.multiselect("Filter by type", sorted(df["type"].unique()))

    filtered_df = df.copy()
    if teams:
        filtered_df = filtered_df[filtered_df["team"].isin(teams)]
    if txn_types:
        filtered_df = filtered_df[filtered_df["type"].isin(txn_types)]

    # ---- Hide internal columns (id, type, time) ----
    display_df = filtered_df.drop(columns=["id", "type", "time"], errors="ignore")

    # ---- Display Transactions ----
    st.subheader("Transactions Table")
    st.dataframe(
        display_df.sort_values(by="team").reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    # ---- CSV Download ----
    st.download_button(
        "⬇️ Download CSV",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="transactions_completed.csv",
        mime="text/csv",
    )
