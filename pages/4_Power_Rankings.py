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
    score_col = next((c for c in power.columns if "score" in c.lower() or "power" in c.lower() or "rank" in c.lower()), None)

    if not team_col or not score_col:
        st.error("Couldn't identify team or score columns. Please check your sheet headers.")
        st.dataframe(power.head())
    else:
        # Clean numeric column
        power[score_col] = pd.to_numeric(power[score_col], errors="coerce")

        # ✅ Sort so highest score = rank 1
        power = power.sort_values(score_col, ascending=False).reset_index(drop=True)

        # Assign rank numbers explicitly
        power["Rank"] = range(1, len(power) + 1)

        # Plot horizontal bar chart (rank 1 on top)
        fig = px.bar(
            power,
            x=score_col,
            y=team_col,
            orientation="h",
            color=score_col,
            text="Rank",
            color_continuous_scale="Viridis",
            title="Power Rankings (1 = Highest)"
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            showlegend=False,
            xaxis_title="Score",
            yaxis_title="Team",
        )
      st.plotly_chart(fig, use_container_width=True)

        # ✅ Display table matching chart order (1 on top → 12 bottom)
        display_df = power.sort_values("Rank", ascending=False).reset_index(drop=True)
        st.dataframe(display_df)
