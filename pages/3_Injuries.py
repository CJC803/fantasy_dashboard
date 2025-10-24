import streamlit as st
import pandas as pd

st.title("🚑 Injury Report")

data = st.session_state["data"]
injuries = data["injuries"]

if injuries.empty:
    st.info("No injury data available.")
else:
    # Normalize column names for consistency
    injuries.columns = injuries.columns.str.strip().str.lower()

    # === Filter out "active" or "healthy" players ===
    status_col = next((c for c in injuries.columns if "status" in c or "injury" in c), None)
    if status_col:
        injuries = injuries[~injuries[status_col].str.contains("active|healthy|none", case=False, na=False)]

    if injuries.empty:
        st.success("✅ No current injuries — everyone’s healthy!")
    else:
        # === Optional Team Filter ===
        team_col = next((c for c in injuries.columns if "team" in c), None)
        if team_col:
            teams = sorted(injuries[team_col].dropna().unique())
            selected_team = st.sidebar.selectbox("Filter by Team", ["All Teams"] + teams)
            if selected_team != "All Teams":
                injuries = injuries[injuries[team_col] == selected_team]

        # === Summary ===
        st.caption(f"Showing {len(injuries)} injured players")

        # === Display injuries ===
        st.dataframe(injuries, use_container_width=True)
