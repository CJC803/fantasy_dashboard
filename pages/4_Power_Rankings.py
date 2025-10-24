import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_all

# 🔒 Ensure session_state is populated
if "data" not in st.session_state:
    st.session_state["data"] = load_all()

data = st.session_state["data"]
power = data["power"]

st.title("⚡ Power Rankings")

if power.empty:
    st.warning("No power ranking data found.")
else:
    # 🔍 Try to detect key columns dynamically
    team_col = next((c for c in power.columns if "team" in c.lower()), None)
    score_col = next((c for c in power.columns if "score" in c.lower() or "power" in c.lower() or "rank" in c.lower()), None)

    if not team_col or not score_col:
        st.error("Couldn't identify team or score columns. Please check your sheet headers.")
        st.dataframe(power.head())
    else:
        # Clean numeric column
        power[score_col] = pd.to_numeric(power[score_col], errors="coerce")

        # Sort so #1 (highest score) is on top
        power = power.sort_values(score_col, ascending=True)

        # Plot
        fig = px.bar(
            power,
            x=score_col,
            y=team_col,
            orientation="h",  # horizontal bars
            color=score_col,
            text=score_col,
            color_continuous_scale="Viridis_r",  # reversed colors
            title="Power Rankings (1 = Highest)"
        )

        fig.update_layout(
            yaxis=dict(categoryorder="total ascending"),  # top = rank 1
            showlegend=False,
            xaxis_title="Score",
            yaxis_title="Team"
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(power)
