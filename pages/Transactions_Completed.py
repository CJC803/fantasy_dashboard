import streamlit as st
import pandas as pd
import altair as alt
from utils import load_csv, TRANSACTIONS_URL

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

    # ---- Sidebar Filter ----
    st.sidebar.header("⚙️ Filter")
    teams = sorted(df["team"].unique())
    selected_team = st.sidebar.selectbox("Select Team", ["All Teams"] + teams)

    if selected_team != "All Teams":
        filtered_df = df[df["team"] == selected_team]
    else:
        filtered_df = df.copy()

    # ---- Compute total moves per team ----
    move_counts = (
        df["team"].value_counts()
        .reset_index()
        .rename(columns={"index": "Team", "team": "Moves"})
        .sort_values(by="Moves", ascending=False)
    )

    # ---- Summary Metrics ----
    st.subheader("Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total Transactions", f"{len(filtered_df):,}")
    col2.metric("Unique Teams", filtered_df["team"].nunique())

    # ---- Moves Visualization ----
    st.subheader("📊 Total Moves by Team")
    if not move_counts.empty:
        # Ensure proper data types for Altair
        move_counts["Team"] = move_counts["Team"].astype(str)
        move_counts["Moves"] = pd.to_numeric(move_counts["Moves"], errors="coerce")

        chart = (
            alt.Chart(move_counts)
            .mark_bar(size=22, cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
            .encode(
                y=alt.Y("Team:N", sort="-x", title="Team"),
                x=alt.X("Moves:Q", title="Total Moves"),
                color=alt.Color("Moves:Q", scale=alt.Scale(scheme="blues")),
                tooltip=[
                    alt.Tooltip("Team:N", title="Team"),
                    alt.Tooltip("Moves:Q", title="Total Moves"),
                ],
            )
            .configure_axis(labelFontSize=12, titleFontSize=14)
            .configure_view(strokeWidth=0)
            .properties(height=420)
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No transactions match the selected team.")

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
