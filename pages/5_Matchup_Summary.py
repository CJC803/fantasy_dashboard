import streamlit as st
import pandas as pd
import plotly.express as px
from utils import week_selector

st.title("📅 Matchup Summary")

data = st.session_state["data"]
matchups = data["matchups"]

if matchups.empty:
    st.warning("No matchup data available.")
else:
    # Normalize headers
    matchups.columns = matchups.columns.str.strip().str.lower()

    # Expect: week, team, opp, pts
    required_cols = {"week", "team", "opp", "pts"}
    if not required_cols.issubset(matchups.columns):
        st.error(f"Missing expected columns: {required_cols - set(matchups.columns)}")
        st.dataframe(matchups.head())
    else:
        # Convert types
        matchups["week"] = pd.to_numeric(matchups["week"], errors="coerce")
        matchups["pts"] = pd.to_numeric(matchups["pts"], errors="coerce")

        # Week selector
        week = week_selector(matchups, week_col="week")

        if week is not None:
            st.subheader(f"Results – Week {week}")
            week_df = matchups[matchups["week"] == week].copy()

            # === Build matchup pairs ===
            merged = pd.merge(
                week_df,
                week_df,
                left_on=["week", "team"],
                right_on=["week", "opp"],
                suffixes=("_team", "_opp"),
            )

            # Avoid duplicate pairs
            merged = merged[merged["team_team"] < merged["team_opp"]].copy()

            # Winner / margin columns
            merged["Winner"] = merged.apply(
                lambda x: x["team_team"] if x["pts_team"] > x["pts_opp"] else x["team_opp"],
                axis=1,
            )
            merged["Margin"] = (merged["pts_team"] - merged["pts_opp"]).abs().round(2)

            # Rename columns AFTER checking they exist
            rename_map = {
                "team_team": "Team",
                "pts_team": "Points",
                "team_opp": "Opponent",
                "pts_opp": "Opp Points",
            }
            merged = merged.rename(columns=rename_map)

            # Ensure columns exist safely
            valid_cols = [c for c in ["week", "Team", "Points", "Opponent", "Opp Points", "Winner", "Margin"] if c in merged.columns]

            st.dataframe(merged[valid_cols], use_container_width=True)

            # === Chart: Points distribution ===
            fig = px.box(
                week_df,
                x="week",
                y="pts",
                points="all",
                title=f"Score Distribution – Week {week}",
                color_discrete_sequence=["#4C78A8"],
            )
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Points")
            st.plotly_chart(fig, use_container_width=True)

        # === Season Totals ===
        st.markdown("### 🧮 Points For / Against / Differential (Season Totals)")

        pf = matchups.groupby("team", as_index=False)["pts"].sum().rename(columns={"pts": "PF"})
        pa = matchups.groupby("opp", as_index=False)["pts"].sum().rename(columns={"opp": "team", "pts": "PA"})
        leaderboard = pf.merge(pa, on="team", how="outer").fillna(0)
        leaderboard["Diff"] = leaderboard["PF"] - leaderboard["PA"]
        leaderboard = leaderboard.sort_values("Diff", ascending=False).reset_index(drop=True)

        st.dataframe(leaderboard, use_container_width=True)

        # === Charts ===
        for metric, color, title in [
            ("PF", "Teal", "Total Points For"),
            ("PA", "Reds", "Total Points Against"),
            ("Diff", "Bluered_r", "Point Differential (PF − PA)"),
        ]:
            fig = px.bar(
                leaderboard.sort_values(metric, ascending=False),
                x="team",
                y=metric,
                color=metric,
                text_auto=".0f",
                color_continuous_scale=color,
                title=title,
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
