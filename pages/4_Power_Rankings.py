import re
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_all

# -----------------------------------
# Page Setup
# -----------------------------------
st.set_page_config(page_title="Power Rankings", layout="wide")
st.title("⚡ Power Rankings")

# -----------------------------------
# Load Data
# -----------------------------------
if "data" not in st.session_state:
    st.session_state["data"] = load_all()

data = st.session_state["data"]
power = data.get("power", pd.DataFrame())

if power.empty:
    st.warning("No power ranking data found.")
    st.stop()

# -----------------------------------
# Normalize Columns
# -----------------------------------
power.columns = power.columns.astype(str).str.strip()
power.columns = power.columns.str.replace(r"\s+", " ", regex=True)
power.columns = power.columns.str.replace("\u00a0", " ", regex=False)

rename_map = {
    "Actual Win": "Actual Win %",
    "Actual Win%": "Actual Win %",
    "Actual Win Percentage": "Actual Win %",
}
power.rename(columns=rename_map, inplace=True)

expected_cols = [
    "Rank",
    "Team",
    "PF",
    "All-Play %",
    "Actual Win %",
    "Avg Margin",
    "Recent Form (3-wk avg)",
    "Recent Margin (3-wk avg)",
    "SoS Played",
    "SoS Remaining",
    "SoS Δ vs Avg",
    "Power Index",
]
missing = [c for c in expected_cols if c not in power.columns]
if missing:
    st.error(f"Missing columns: {', '.join(missing)}")
    st.dataframe(power.head())
    st.stop()

# -----------------------------------
# Helper Functions
# -----------------------------------
def clean_percent(series):
    def to_float(x):
        if pd.isna(x):
            return None
        x = re.sub(r"[^0-9.\-]", "", str(x))
        try:
            val = float(x)
            return val * 100 if 0 <= val <= 1 else val
        except ValueError:
            return None
    return pd.Series([to_float(v) for v in series], dtype="float")

# -----------------------------------
# Data Cleanup
# -----------------------------------
for pct_col in ["All-Play %", "Actual Win %"]:
    power[pct_col] = clean_percent(power[pct_col])

numeric_cols = [
    "PF",
    "Avg Margin",
    "Recent Form (3-wk avg)",
    "Recent Margin (3-wk avg)",
    "SoS Played",
    "SoS Remaining",
    "SoS Δ vs Avg",
    "Power Index",
    "Rank",
]
for col in numeric_cols:
    power[col] = pd.to_numeric(power[col], errors="coerce")

# Rank SoS metrics (1 = hardest / highest)
for col in ["SoS Played", "SoS Remaining", "SoS Δ vs Avg"]:
    if col in power.columns:
        power[f"{col} Rank"] = power[col].rank(method="min", ascending=False).astype(int)

power.sort_values("Rank", inplace=True)
power.reset_index(drop=True, inplace=True)

# -----------------------------------
# Summary Insights
# -----------------------------------
st.subheader("📈 Summary Insights")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Top Team", power.loc[0, "Team"])
col2.metric("Avg Power Index", f"{power['Power Index'].mean():.2f}")
col3.metric("Avg PF", f"{power['PF'].mean():.1f}")
best_form_team = power.loc[power["Recent Form (3-wk avg)"].idxmax(), "Team"]
best_form_value = power["Recent Form (3-wk avg)"].max()
col4.metric("Best 3-Week Avg PF", f"{best_form_value:.1f}", best_form_team)

# -----------------------------------
# Extended Insights
# -----------------------------------
with st.expander("🔎 Advanced Insights"):
    c1, c2, c3 = st.columns(3)

    # 1. Luck metric
    if "Actual Win %" in power.columns and "All-Play %" in power.columns:
        power["Luck Δ"] = power["Actual Win %"] - power["All-Play %"]
        luckiest = power.loc[power["Luck Δ"].idxmax()]
        unluckiest = power.loc[power["Luck Δ"].idxmin()]
        c1.metric("Luckiest Team", luckiest["Team"], f"{luckiest['Luck Δ']:+.1f}%")
        c2.metric("Unluckiest Team", unluckiest["Team"], f"{unluckiest['Luck Δ']:+.1f}%")

    # 2. SoS extremes
    hardest_remaining = power.loc[power["SoS Remaining"].idxmax()]
    easiest_remaining = power.loc[power["SoS Remaining"].idxmin()]
    c3.metric("Toughest Remaining SoS", hardest_remaining["Team"], f"{hardest_remaining['SoS Remaining']:.1f}")

    c4, c5, c6 = st.columns(3)
    # 3. Biggest margin performer
    margin_team = power.loc[power["Avg Margin"].idxmax()]
    c4.metric("Biggest Avg Margin", f"{margin_team['Avg Margin']:.1f}", margin_team["Team"])

    # 4. Overperformer vs SoS (high Power Index + high SoS)
    if "Power Index" in power.columns:
        overperform = power.assign(
            Combined=lambda x: x["Power Index"] + x["SoS Played"]
        ).sort_values("Combined", ascending=False).iloc[0]
        c5.metric("Overperformer (Power+SoS)", overperform["Team"], f"{overperform['Power Index']:.2f}")

    # 5. Power Index stability
    c6.metric("Power Index Range", f"{power['Power Index'].min():.2f}–{power['Power Index'].max():.2f}")

# -----------------------------------
# Power Index Chart
# -----------------------------------
st.subheader("🏆 Full Power Rankings — Chart")

chart_df = power.sort_values("Power Index", ascending=True)
fig = px.bar(
    chart_df,
    x="Power Index",
    y="Team",
    orientation="h",
    text=chart_df["Rank"].astype(int),
    color="Power Index",
    color_continuous_scale="Blues_r",
    hover_data={
        "All-Play %": ":.1f",
        "Actual Win %": ":.1f",
        "Avg Margin": ":.1f",
        "PF": ":.0f",
        "SoS Played": ":.1f",
        "SoS Remaining": ":.1f",
        "SoS Δ vs Avg": ":.1f",
        "Power Index": ":.2f",
    },
)
fig.update_layout(
    xaxis_title="Power Index",
    yaxis_title="Team",
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------
# Table
# -----------------------------------
st.subheader("📋 Full Power Rankings — Table")

display = power.copy()
display["All-Play %"] = display["All-Play %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
display["Actual Win %"] = display["Actual Win %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
display["PF"] = display["PF"].map(lambda x: f"{x:.0f}" if pd.notna(x) else "")
display["Avg Margin"] = display["Avg Margin"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["Power Index"] = display["Power Index"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
display["Recent Form (3-wk avg)"] = display["Recent Form (3-wk avg)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["Recent Margin (3-wk avg)"] = display["Recent Margin (3-wk avg)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")

# Rank columns instead of raw SoS
display = display[
    [
        "Rank",
        "Team",
        "Power Index",
        "All-Play %",
        "Actual Win %",
        "PF",
        "Avg Margin",
        "Recent Form (3-wk avg)",
        "Recent Margin (3-wk avg)",
        "SoS Played Rank",
        "SoS Remaining Rank",
        "SoS Δ vs Avg Rank",
    ]
]
st.dataframe(display, use_container_width=True, hide_index=True)

# -----------------------------------
# Download
# -----------------------------------
st.download_button(
    "⬇️ Download Power Rankings CSV",
    data=power.to_csv(index=False).encode("utf-8"),
    file_name="power_rankings.csv",
    mime="text/csv",
)
