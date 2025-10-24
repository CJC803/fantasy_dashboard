import streamlit as st
import plotly.express as px

data = st.session_state["data"]
allplay = data["allplay"]

st.title("\U0001F3C8 All-Play Standings")

if not allplay.empty:
    # Sort by Win% if column exists
    if "Win%" in allplay.columns:
        allplay = allplay.sort_values("Win%", ascending=False)
    fig = px.bar(
        allplay,
        x="Team" if "Team" in allplay.columns else "team_name",
        y="Win%" if "Win%" in allplay.columns else "win_pct",
        color="Win%" if "Win%" in allplay.columns else "win_pct",
        text="Win%" if "Win%" in allplay.columns else "win_pct",
        color_continuous_scale="Magma",
        title="Cumulative All-Play Win Percentage"
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_layout(showlegend=False, yaxis_title="Win %")
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(allplay)
