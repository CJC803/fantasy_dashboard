import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_all

# 🔒 Ensure session_state is populated
if "data" not in st.session_state:
    st.session_state["data"] = load_all()

data = st.session_state["data"]
standings = data["standings"]

st.title("📊 League Standings")

if standings.empty:
    st.warning("No standings data found.")
else:
    # 🔍 Try to detect columns dynamically
    team_col = next((c for c in standings.columns if "team" in c.lower()), None)
    win_col = next((c for c in standings.columns if "win" in c.lower() or "pct" in c.lower()), None)

    if not team_col or not win_col:
        st.error("Couldn't find the team or win percentage column. Please check your sheet headers.")
        st.dataframe(standings.head())
    else:
        # Clean numeric column
        standings[win_col] = pd.to_numeric(standings[win_col], errors="coerce")

        # Sort by win percentage descending
        standings = standings.sort_values(win_col, ascending=False)

        # Plot
        fig = px.bar(
            standings,
            x=team_col,
            y=win_col,
            color=win_col,
            text=win_col,
            color_continuous_scale="Blues",
            title="Team Win Percentage"
        )
        fig.update_layout(showlegend=False, xaxis_title="Team", yaxis_title="Win %")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(standings)
