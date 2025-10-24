import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🚑 Injury Report")

data = st.session_state["data"]
injuries = data["injuries"]

if injuries.empty:
    st.info("No injury data available.")
else:
    # Normalize column names
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

        # === Radar Chart: Injured Players by Team ===
        if team_col:
            injury_counts = injuries[team_col].value_counts().reset_index()
            injury_counts.columns = ["Team", "Injured Players"]

            fig = px.line_polar(
                injury_counts,
                r="Injured Players",
                theta="Team",
                line_close=True,
                title="🕸️ Injured Players by Team",
            )
            fig.update_traces(fill='toself', line_color="crimson")
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, showticklabels=True)))
            st.plotly_chart(fig, use_container_width=True)
