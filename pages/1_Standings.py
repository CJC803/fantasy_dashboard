import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    # 🔍 Detect columns dynamically
    team_col = next((c for c in standings.columns if "team" in c.lower()), None)
    win_col = next((c for c in standings.columns if "win" in c.lower() or "pct" in c.lower()), None)

    if not team_col or not win_col:
        st.error("Couldn't find the team or win percentage column. Please check your sheet headers.")
        st.dataframe(standings.head())
    else:
        # 🧹 Clean numeric column
        standings[win_col] = pd.to_numeric(standings[win_col], errors="coerce")

        # ✅ Sort descending (best to worst)
        standings = standings.sort_values(win_col, ascending=False).reset_index(drop=True)

        # === Add Rank column ===
        standings["Rank"] = range(1, len(standings) + 1)

        # === Create color map to highlight playoff teams ===
        # Default blue gradient, highlight playoff bubble and matchup
        colors = []
        for i in range(len(standings)):
            if standings.loc[i, "Rank"] in (4, 5):
                colors.append("orange")  # 🟠 Highlight potential playoff matchup
            elif standings.loc[i, "Rank"] <= 5:
                colors.append("#1f77b4")  # 🟦 Playoff team
            else:
                colors.append("lightgray")  # ⚪ Missed playoffs

        # === Create main bar chart ===
        fig = px.bar(
            standings,
            x=team_col,
            y=win_col,
            text=win_col,
            title="🏈 Team Win Percentage with Playoff Cutoff",
            color_discrete_sequence=["#1f77b4"],  # default color overridden per bar below
        )

        # Override bar colors individually
        fig.update_traces(marker_color=colors, texttemplate="%{text:.3f}")

        # === Add cutoff line between 5th and 6th ===
        if len(standings) > 5:
            # X position between team 5 and 6
            cutoff_index = 5 - 0.5
            fig.add_shape(
                type="line",
                x0=cutoff_index,
                x1=cutoff_index,
                y0=0,
                y1=standings[win_col].max(),
                line=dict(color="red", width=2, dash="dash"),
            )

            fig.add_annotation(
                x=cutoff_index,
                y=standings[win_col].max() * 0.95,
                text="Playoff Cutoff",
                showarrow=False,
                font=dict(color="red", size=12, family="Arial"),
                bgcolor="rgba(255,255,255,0.7)"
            )

        # === Final layout tweaks ===
        fig.update_layout(
            showlegend=False,
            xaxis_title="Team",
            yaxis_title="Win %",
            xaxis=dict(tickmode="array", tickvals=list(range(len(standings))), ticktext=standings[team_col]),
            margin=dict(t=60, b=60),
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(standings)
