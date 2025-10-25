import streamlit as st
import pandas as pd
from utils import load_csv, TRANSACTIONS_URL  # ✅ uses the shared loader and URL

st.set_page_config(page_title="Completed Transactions", layout="wide")
st.title("📋 Completed Transactions")

@st.cache_data
def load_transactions():
    return load_csv(TRANSACTIONS_URL)

with st.spinner("Loading transactions..."):
    df = load_transactions()

if df.empty:
    st.info("No completed transactions found.")
else:
    # High-level metrics
    st.subheader("Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total transactions", f"{len(df):,}")
    col2.metric("Unique teams", df["team"].nunique())

    # Filters
    st.subheader("Filters")
    teams = st.multiselect("Filter by team", sorted(df["team"].unique()))
    txn_types = st.multiselect("Filter by type", sorted(df["type"].unique()))

    filtered_df = df.copy()
    if teams:
        filtered_df = filtered_df[filtered_df["team"].isin(teams)]
    if txn_types:
        filtered_df = filtered_df[filtered_df["type"].isin(txn_types)]

    # Display transactions
    st.dataframe(
        filtered_df.sort_values(by="time", ascending=False).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    # Download CSV
    st.download_button(
        "⬇️ Download CSV",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="transactions_completed.csv",
        mime="text/csv",
    )
