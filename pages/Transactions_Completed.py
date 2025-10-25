import streamlit as st
import pandas as pd
import altair as alt
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
    # ---- Filter out lineup changes and unwanted transaction types ----
    df = df[df["details"].str.contains("Add:|Drop:", case=False, na=False)]

    # ---- Remove unnecessary columns ----
    df = df.drop(columns=["id", "type", "time", "status"], errors="ignore")

    # ---- Compute total moves per team ----
    move_counts = df["team"].value_counts().reset_index()
    move_counts.columns = ["Team", "Moves"]

    # ---- Sidebar Filters ----
    st.sidebar.header("⚙️ Filters")
    teams = st.sidebar.multiselect("Filter by Team", sorted(df["team"].unique()))

    filtered_df = df.copy()
    if teams:
        filtered_df = filtered_df[filtered_df["team"].isin(teams)]

    # ---- Summary Metrics ----
    st.subheader("Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total Transactions", f"{len(filtered_df):,}")
    col2.metric("Unique Teams", filtered_df["team"].nunique())

    # ---- Moves Visualization ----
    st.subheader("📊 Total Moves by Team")
    chart = (
        alt.Chart(filtered_df["team"].value_counts().reset_index())
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("team:Q", title="Total Moves"),
            y=alt.Y("index:N", title="Team", sort="-x"),
            color=alt.Color("team:Q", scale=alt.Scale(scheme="blues")),
            tooltip=["index", "team"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

    # ---- Display Transactions ----
    st.subheader("Transactions Table")
    st.dataframe(
        filtered_df.sort_values(by="team").reset_index(drop=True),
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
