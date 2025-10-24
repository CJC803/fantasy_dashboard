import streamlit as st
import plotly.express as px

data = st.session_state["data"]
standings = data["standings"]

st.title("📊 League Standings")

if not standings.empty:
    standings = standings.sort_values("Win%", ascending=False)
    fig = px.bar(
        standings,
        x="Team",
        y="Win%",
        color="Team",
        text="Win%",
        title="Team Win Percentage"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(standings)
