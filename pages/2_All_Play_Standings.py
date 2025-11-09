import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------------------
# Page Setup
# -----------------------------------
st.set_page_config(page_title="All-Play Standings", layout="wide")
st.title("🏈 All-Play Standings")

# -----------------------------------
# Load Data
# -----------------------------------
data = st.session_state.get("data", {})
allplay = data.get("allplay", pd.DataFrame())

if allplay.empty:
    st.info("No All-Play data available.")
    st.stop()

# -----------------------------------
# Normalize and Validate
# -----------------------------------
allplay.columns = allplay.columns.str.strip()
if "Win%" not in allplay.columns:
    st.error("Missing 'Win%' column in data.")
    st.stop()

# Ensure numeric Win%
allplay["Win%"] = pd.to_numeric(allplay["Win%"], errors="coerce")
allplay = allplay.dropna(subset=["Team", "Win%"])
allplay = allplay.sort_values("Win%", ascending=False).reset_index(drop=True)

# -----------------------------------
# Daily Snapshot Tracking
# -----------------------------------
today = datetime.now().strftime("%Y-%m-%d")
st.session_state.setdefault("allplay_history", {})

if today not in st.session_state["allplay_history"]:
    st.session_state["allplay_history"][today] = allplay.copy()
    st.toast(f"📊 Saved daily snapshot for {today}", icon="✅")

history = st.session_state["allplay_history"]
merged = allplay.copy()

if len(history) >= 2:
    dates = sorted(history.keys())
    prev_day = dates[-2]
    prev_df = history[prev_day]
    merged = pd.merge(
        allplay,
        prev_df[["team_id", "Win%"]],
        on="team_id",
        how="left",
        suffixes=("", "_prev")
    )
    merged["Δ Win%"] = merged["Win%"] - merged["Win%_prev"]
    trend_available = True
else:
    merged["Δ Win%"] = 0.0
    trend_available = False

# -----------------------------------
# Expandable Insights Section
# -----------------------------------
st.subheader("📊 Summary Insights")

if not merged.empty:
    top_team = merged.iloc[0]["Team"]
    top_win = merged.iloc[0]["Win%"]
    bottom_team = merged.iloc[-1]["Team"]
    bottom_win = merged.iloc[-1]["Win%"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Teams Tracked", len(merged))
    c2.metric("Top Team", f"{top_team}", f"{top_win:.3f}")
    c3.metric("Lowest Team", f"{bottom_team}", f"{bottom_win:.3f}")

    with st.expander("🔎 View Additional Insights"):
        if trend_available:
            biggest_riser = merged.loc[merged["Δ Win%"].idxmax()]
            biggest_faller = merged.loc[merged["Δ Win%"].idxmin()]
            avg_delta = merged["Δ Win%"].mean()

            st.markdown(
                f"""
                **Top Performer:** 🥇 {top_team} ({top_win:.3f} Win%)  
                **Biggest Riser:** 📈 {biggest_riser["Team"]} (+{biggest_riser["Δ Win%"]:.3f})  
                **Biggest Drop:** 📉 {biggest_faller["Team"]} ({biggest_faller["Δ Win%"]:+.3f})  
                **League Avg Change:** {avg_delta:+.3f}
                """,
            )
        else:
            st.info("No trend data yet — daily tracking starts today.")

# -----------------------------------
# Bar Chart Visualization
# -----------------------------------
st.subheader("📈 All-Play Win Percentage")

fig = px.bar(
    merged,
    x="Team",
    y="Win%",
    color="Win%",
    color_continuous_scale=px.colors.sequential.Blues_r,
    title="Cumulative All-Play Win Percentage",
)

fig.update_traces(hovertemplate="<b>%{x}</b><br>Win%: %{y:.3f}<extra></extra>")
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0f0f0"),
    xaxis_title=None,
    yaxis_title="Win %",
    coloraxis_showscale=False,
    margin=dict(t=60, b=20),
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------
# Detailed Table
# -----------------------------------
st.subheader("📋 Detailed Standings")

def style_delta(val):
    color = "#2ecc71" if val > 0 else "#e74c3c" if val < 0 else "#999"
    return f"color:{color}; font-weight:600"

merged = merged[["Team", "Wins", "Losses", "Win%", "Δ Win%"]]
styled = (
    merged.style.format({"Win%": "{:.3f}", "Δ Win%": "{:+.3f}"})
    .applymap(style_delta, subset=["Δ Win%"])
)
st.dataframe(styled, use_container_width=True, hide_index=True)

# -----------------------------------
# Footer
# -----------------------------------
status = "trend active" if trend_available else "first day recorded"
st.caption(f"🕒 Updated {datetime.now():%b %d, %Y %I:%M %p} — {status}.")
