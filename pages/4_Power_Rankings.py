import streamlit as st
import plotly.express as px

data = st.session_state["data"]
power = data["power"]

st.title("\u26a1 Power Rankings")

if not power.empty:
    if "Score" in power.columns:
        power = power.sort_values("Score", ascending=False)
    fig = px.bar(
        power,
        x="Team" if "Team" in power.columns else power.columns[0],
        y="Score",
        color="Score",
        color_continuous_scale="Viridis",
        text="Score",
        title="Power Ranking Scores"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(power)
