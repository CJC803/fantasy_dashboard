import streamlit as st
import pandas as pd
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
    st.stop()

# ---- Filter out lineup changes and unwanted transaction types ----
df = df[df["details"].str.contains("Add:|Drop:", case=False, na=False)]

# ---- Remove unnecessary columns ----
df = df.drop(columns=["id", "type", "time", "status"], errors="ignore")

# ---- Sidebar Filter ----
st.sidebar.header("⚙️ Filter")
teams = sorted(df["team"].dropna().unique().tolist())
selected_team = st.sidebar.selectbox("Select Team", ["All Teams"] + teams)

filtered_df = df if selected_team == "All Teams" else df[df["team"] == selected_team]

# ---- Compute total moves per team ----
if "team" in df.columns and not df.empty:
    move_counts = (
        df["team"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Team", df["team"].name: "Moves"})
        .convert_dtypes()
        .sort_values(by="Moves", ascending=False)
    )
else:
    move_counts = pd.DataFrame(columns=["Team", "Moves"])

# ---- Summary Metrics ----
st.subheader("Summary")
col1, col2 = st.columns(2)
col1.metric("Total Transactions", f"{len(filtered_df):,}")
col2.metric("Unique Teams", filtered_df["team"].nunique())


# ---- Display Transactions ----
st.subheader("Transactions Table")
if not filtered_df.empty:
    st.dataframe(
        filtered_df.sort_values(by="team").reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No transactions match the selected team.")

# ---- CSV Download ----
st.download_button(
    "⬇️ Download CSV",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="transactions_completed.csv",
    mime="text/csv",
)
