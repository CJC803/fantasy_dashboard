import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# Normalize Columns (aggressive cleanup)
# -----------------------------------
power.columns = (
    power.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
    .str.replace("\u00a0", " ", regex=False)   # non-breaking space
    .str.replace("\ufeff", "", regex=False)    # BOM
    .str.replace("SoSΔvsAvg", "SoS Δ vs Avg", regex=False)  # common sheet-export quirk
)

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
# Helpers
# -----------------------------------
def clean_percent(series: pd.Series) -> pd.Series:
    """Accepts values like 0.61, 61, '61%', '0.61', '61.0 %' and returns 61.0 style floats."""
    def to_float(x):
        if pd.isna(x):
            return None
        s = re.sub(r"[^0-9.\-]", "", str(x))
        if s == "" or s == "." or s == "-":
            return None
        try:
            val = float(s)
            # If 0..1, treat as fraction -> percent
            return val * 100 if 0 <= val <= 1 else val
        except ValueError:
            return None
    return pd.Series((to_float(v) for v in series), dtype="float")

# -----------------------------------
# Type cleanup
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

# Rank SoS metrics
# Convention: 1 = hardest / highest value. Ties share rank (method="min").
for col in ["SoS Played", "SoS Remaining", "SoS Δ vs Avg"]:
    power[f"{col} Rank"] = power[col].rank(method="min", ascending=False).astype("Int64")

# Sort by Rank for display
power.sort_values("Rank", inplace=True)
power.reset_index(drop=True, inplace=True)

# -----------------------------------
# Summary KPIs
# -----------------------------------
st.subheader("📈 Summary Insights")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Top Team", power.loc[0, "Team"])
c2.metric("Avg Power Index", f"{power['Power Index'].mean():.2f}")
c3.metric("Avg PF", f"{power['PF'].mean():.1f}")
best_form_team = power.loc[power["Recent Form (3-wk avg)"].idxmax(), "Team"]
best_form_val = power["Recent Form (3-wk avg)"].max()
c4.metric("Best 3-Week Avg PF", f"{best_form_val:.1f}", best_form_team)

# -----------------------------------
# Advanced Insights (expandable)
# -----------------------------------
with st.expander("🔎 Advanced Insights"):
    c1, c2, c3 = st.columns(3)

    # Luck (Actual - All-Play)
    power["Luck Δ"] = power["Actual Win %"] - power["All-Play %"]
    luckiest = power.loc[power["Luck Δ"].idxmax()]
    unluckiest = power.loc[power["Luck Δ"].idxmin()]
    c1.metric("Luckiest Team", luckiest["Team"], f"{luckiest['Luck Δ']:+.1f}%")
    c2.metric("Unluckiest Team", unluckiest["Team"], f"{unluckiest['Luck Δ']:+.1f}%")

    # SoS extremes (Remaining)
    hardest_remaining = power.loc[power["SoS Remaining"].idxmax()]
    easiest_remaining = power.loc[power["SoS Remaining"].idxmin()]
    c3.metric(
        "Toughest Remaining SoS",
        hardest_remaining["Team"],
        f"{hardest_remaining['SoS Remaining']:.1f}",
    )

    c4, c5, c6 = st.columns(3)
    c4.metric(
        "Easiest Remaining SoS",
        easiest_remaining["Team"],
        f"{easiest_remaining['SoS Remaining']:.1f}",
    )

    # Biggest Avg Margin
    margin_team = power.loc[power["Avg Margin"].idxmax()]
    c5.metric("Biggest Avg Margin", f"{margin_team['Avg Margin']:.1f}", margin_team["Team"])

    # Over-performer: high Power Index despite tough schedule already played
    overperform = (
        power.assign(Combined=lambda x: x["Power Index"] + x["SoS Played"])
        .sort_values("Combined", ascending=False)
        .iloc[0]
    )
    c6.metric("Over-performer (Power+SoS Played)", overperform["Team"], f"{overperform['Power Index']:.2f}")

    st.caption(
        "Notes: Luck Δ = Actual Win % − All-Play %. SoS ranks use ‘1’ as hardest (ties share rank). "
        "Hover the chart below to see exact SoS values next to their ranks."
    )

# -----------------------------------
# Power Index Chart (hover shows SoS values + ranks)
# -----------------------------------
st.subheader("🏆 Full Power Rankings — Chart")

chart_df = power.sort_values("Power Index", ascending=True).copy()

# customdata for hover (values then ranks)
chart_df["SoS Played Rank"] = chart_df["SoS Played Rank"].astype("Int64")
chart_df["SoS Remaining Rank"] = chart_df["SoS Remaining Rank"].astype("Int64")
chart_df["SoS Δ vs Avg Rank"] = chart_df["SoS Δ vs Avg Rank"].astype("Int64")

custom_cols = [
    "All-Play %",
    "Actual Win %",
    "Avg Margin",
    "PF",
    "SoS Played",
    "SoS Remaining",
    "SoS Δ vs Avg",
    "SoS Played Rank",
    "SoS Remaining Rank",
    "SoS Δ vs Avg Rank",
]
chart_df_custom = chart_df[custom_cols].values

fig = px.bar(
    chart_df,
    x="Power Index",
    y="Team",
    orientation="h",
    text=chart_df["Rank"].astype(int),
    color="Power Index",
    color_continuous_scale="Blues_r",
)
# Replace default hover with explicit template that shows SoS values + ranks
fig.update_traces(
    customdata=chart_df_custom,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Power Index: %{x:.2f}<br>"
        "PF: %{customdata[3]:.0f}<br>"
        "All-Play %: %{customdata[0]:.1f}%<br>"
        "Actual Win %: %{customdata[1]:.1f}%<br>"
        "Avg Margin: %{customdata[2]:.1f}<br>"
        "SoS Played: %{customdata[4]:.1f} (Rank %{customdata[7]})<br>"
        "SoS Remaining: %{customdata[5]:.1f} (Rank %{customdata[8]})<br>"
        "SoS Δ vs Avg: %{customdata[6]:.1f} (Rank %{customdata[9]})"
        "<extra></extra>"
    ),
)

fig.update_layout(
    xaxis_title="Power Index",
    yaxis_title="Team",
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------
# Table (SoS as ranks; values shown via chart hover)
# -----------------------------------
st.subheader("📋 Full Power Rankings — Table")

display = power.copy()

# format percents & numbers
display["All-Play %"] = display["All-Play %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
display["Actual Win %"] = display["Actual Win %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
display["PF"] = display["PF"].map(lambda x: f"{x:.0f}" if pd.notna(x) else "")
display["Avg Margin"] = display["Avg Margin"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["Power Index"] = display["Power Index"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
display["Recent Form (3-wk avg)"] = display["Recent Form (3-wk avg)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["Recent Margin (3-wk avg)"] = display["Recent Margin (3-wk avg)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")

# Show only the rank versions of SoS columns in the table
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
