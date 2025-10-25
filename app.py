import streamlit as st
from utils import load_all

st.set_page_config(
    page_title="Fantasy Football Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("🏈 Fantasy Dashboard")
st.sidebar.markdown("Use the sidebar to explore pages.")

# Load the data once into session state
if "data" not in st.session_state:
    st.session_state["data"] = load_all()

st.title("🏟️ League Overview")
st.markdown("""
12 Rookies Enter... Only One Survives to Become a Legend
Navigate between Standings, All-Play Standings, Injuries, Power Rankings, Matchup Summary, and Transactions.
Updates Twice a Day.
""")
