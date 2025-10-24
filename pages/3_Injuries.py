import streamlit as st

data = st.session_state["data"]
injuries = data["injuries"]

st.title("🚑 Injury Report")

if injuries.empty:
    st.info("No injury data available.")
else:
    # Filter by team if "Team" column exists
    if "Team" in injuries.columns:
        teams = sorted(injuries["Team"].dropna().unique())
        selected_team = st.sidebar.selectbox("Filter by Team", ["All"] + teams)
        if selected_team != "All":
            injuries = injuries[injuries["Team"] == selected_team]
    st.dataframe(injuries)
