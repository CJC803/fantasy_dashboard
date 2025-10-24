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
    # 🔍 Detect columns dynamically
    team_col = next((c for c in power.columns if "team" in c.lower()), None)
    score_col = next(
        (c for c in power.columns if "score" in c.lower() or "power" in c.lower() or "rank" in c.lower()),
        None
    )

    if not team_col or not score_col:
        st.error("Couldn't identify team or score columns. Please check your sheet headers.")
        st.dataframe(power.head())
    else:
        # ✅ Clean numeric column
        power[score_col] = pd.to_numeric(power[score_col], errors="coerce")

        # ✅ Sort descending so best scores are first
        power = power.sort_values(score_col, ascending=False).reset_index(drop=True)

        # ✅ If 'Rank' already exists, rename it to avoid collision
        if "Rank" in power.columns:
            power = power.rename(columns={"Rank": "Original Rank"})

        # ✅ Assign Rank so 1 = best score
        power["Rank"] = range(1, len(power) + 1)

        # === Chart (Rank 1 = top, biggest bar) ===
        power = power.sort_values("Rank", ascending=True)
        fig = px.bar(
            power,
            x=score_col,
            y=team_col,
            orientation="h",
            color=score_col,
            text="Rank",
            color_continuous_scale="Viridis",
            title="🏆 Power Rankings (1 = Highest)"
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="Score",
            yaxis_title="Team"
        )

        st.plotly_chart(fig, use_container_width=True)

        # === Table (deduplicate column names + Rank 1 = top) ===
        power = power.loc[:, ~power.columns.duplicated()]
        st.dataframe(power[["Rank", team_col, score_col]])
