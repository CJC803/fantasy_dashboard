import streamlit as st
import pandas as pd
import plotly.express as px
from utils import week_selector

data = st.session_state["data"]
matchups = data["matchups"]

st.title("📅 Matchup Summary")

if matchups.empty:
    st.info("No matchup data available.")
else:
    week = week_selector(matchups, week_col="Week")
    if week is not None:
        week_df = matchups[matchups["Week"] == week]
        st.subheader(f"Results \u2013 Week {week}")
        st.dataframe(week_df)

        if {"HomeTeam", "HomePoints", "AwayTeam", "AwayPoints"}.issubset(week_df.columns):
            melted = week_df.melt(
                id_vars=["Week"],
                value_vars=["HomePoints", "AwayPoints"],
                var_name="Side",
                value_name="Points"
            )
            fig = px.box(
                melted,
                x="Side",
                y="Points",
                title=f"Score Distribution \u2013 Week {week}",
                color="Side"
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### \U0001f9ae Points For / Points Against (Cumulative)")
    if {"HomeTeam","HomePoints","AwayTeam","AwayPoints"}.issubset(matchups.columns):
        pf = pd.concat([
            matchups[["HomeTeam","HomePoints"]].rename(columns={"HomeTeam":"Team","HomePoints":"PF"}),
            matchups[["AwayTeam","AwayPoints"]].rename(columns={"AwayTeam":"Team","AwayPoints":"PF"})
        ])
        pa = pd.concat([
            matchups[["HomeTeam","AwayPoints"]].rename(columns={"HomeTeam":"Team","AwayPoints":"PA"}),
            matchups[["AwayTeam","HomePoints"]].rename(columns={"AwayTeam":"Team","HomePoints":"PA"})
        ])
        pf = pf.groupby("Team", as_index=False).sum()
        pa = pa.groupby("Team", as_index=False).sum()
        leaderboard = pf.merge(pa, on="Team", how="outer").fillna(0)
        leaderboard["Diff"] = leaderboard["PF"] - leaderboard["PA"]

        st.dataframe(leaderboard)

        fig_pf = px.bar(
            leaderboard.sort_values("PF", ascending=False),
            x="Team", y="PF", color="PF",
            color_continuous_scale="Teal", text_auto=".0f",
            title="Total Points For"
        )
        fig_pf.update_layout(showlegend=False)
        st.plotly_chart(fig_pf, use_container_width=True)

        fig_pa = px.bar(
            leaderboard.sort_values("PA", ascending=False),
            x="Team", y="PA", color="PA",
            color_continuous_scale="Reds", text_auto=".0f",
            title="Total Points Against"
        )
        fig_pa.update_layout(showlegend=False)
        st.plotly_chart(fig_pa, use_container_width=True)

        fig_diff = px.bar(
            leaderboard.sort_values("Diff", ascending=False),
            x="Team", y="Diff", color="Diff",
            color_continuous_scale="Bluered_r", text_auto=".0f",
            title="Point Differential (PF \u2212 PA)"
        )
        fig_diff.update_layout(showlegend=False)
        st.plotly_chart(fig_diff, use_container_width=True)
