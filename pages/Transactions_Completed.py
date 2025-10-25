import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Adjust these to your own configuration
SHEET_ID = "<YOUR_GOOGLE_SHEET_ID>"
WORKSHEET_NAME = "transactions_completed"
SERVICE_ACCOUNT_FILE = "service_account.json"  # path to your service account JSON file

@st.cache_data
def load_transactions():
    """Fetch the 'transactions_completed' tab as a DataFrame."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    return pd.DataFrame(ws.get_all_records())

def main():
    st.set_page_config(page_title="Completed Transactions", layout="wide")
    st.title("\ud83d\udccb Completed Transactions")

    with st.spinner("Loading transactions..."):
        df = load_transactions()

    if df.empty:
        st.info("No completed transactions found.")
        return

    # High-level metrics
    st.subheader("Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total transactions", f"{len(df):,}")
    col2.metric("Unique teams", df["team"].nunique())

    # Filters
    st.subheader("Filters")
    teams = st.multiselect(
        "Filter by team",
        options=sorted(df["team"].unique()),
        default=[],
    )
    txn_types = st.multiselect(
        "Filter by transaction type",
        options=sorted(df["type"].unique()),
        default=[],
    )

    filtered_df = df.copy()
    if teams:
        filtered_df = filtered_df[filtered_df["team"].isin(teams)]
    if txn_types:
        filtered_df = filtered_df[filtered_df["type"].isin(txn_types)]

    # Display transactions
    st.subheader("Transactions")
    st.dataframe(
        filtered_df.sort_values(by="time", ascending=False).reset_index(drop=True),
        use_container_width=True,
    )

    # Download button
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        data=csv_data,
        file_name="transactions_completed.csv",
        mime="text/csv",
    )

if __name__ == "__main__":
    main()
