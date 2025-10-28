import re
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_all

st.set_page_config(page_title="Power Rankings", layout="wide")
st.title("⚡ Power Rankings")

# ---- Load Data ----
if "data" not in st.session_state:
    st.session_state["data"] = load_all()
data = st.session_state["data"]
power = data["power"]

if power.empty:
    st.warning("No power ranking data found.")
    st.stop()

# ---- Normalize columns ----
power.columns = power.columns.str.strip()

expected_cols = [
    "Rank",
    "Team",
    "PF",
    "All-Play %",
    "Avg Margin",
    "Recent Form (3 wk avg)",
    "SoS (opp PF avg)",
    "Power Index",
]
missing = [c for c in expected_cols if c not in power.columns]
if missing:
    st.error(f"Missing columns: {', '.join(missing)}")
    st.dataframe(power.head())
    st.stop()

# ---- Helpers ----
def clean_percent_column(series: pd.Series) -> pd.Series:
    """
    Convert messy percent strings like '65%', '65.0 %', ' 65 % ', or decimals '0.65'
    into floats in the 0–100 range.
    """
    # Force string, strip %, commas, any whitespace (incl. non-breaking)
    s = series.astype(str).apply(lambda x: re.sub(r"[%\s\u202F\u00A0,]", "", x))
    s = pd.to_numeric(s, errors="coerce")
    # If values look like fractions (<=1), scale to percent
    if s.dropna().max() <= 1:
        s = s * 100
    return s

# ---- Numeric cleanup ----
power["All-Play %"] = clean_percent_column(power["All-Play %"])
power["Recent Form (3 wk avg)"] = clean_percent_column(power["Recent Form (3 wk avg)"])

for c in ["PF", "Avg Margin", "SoS (opp PF avg)", "Power Index", "Rank"]:
    power[c] = pd.to_numeric(power[c], errors="coerce")

# Keep sort by ascending Rank if Rank is present & valid, else by Power Index desc
if power["Rank"].notna().any():
    power = power.sort_values("Rank", ascending=True).reset_index(drop=True)
else:
    power = power.sort_values("Power Index", ascending=False).reset_index(drop=True)
    power["Rank"] = range(1, len(power) + 1)

# =======================
#      INSIGHTS TOP
# =======================
st.subheader("📈 Summary Insights")
col1, col2, col3, col4 = st.columns(4)

top_team = power.loc[power["Rank"].idxmin(), "Team"]
col1.metric("Top Team", top_team)

col2.metric("Avg Power Index", f"{power['Power Index'].mean():.2f}")
col3.metric("Avg PF", f"{power['PF'].mean():.1f}")

# Best recent form (3-week)
best_form_idx = power["Recent Form (3 wk avg)"].idxmax()
best_form_team = power.loc[best_form_idx, "Team"]
best_form_val = power.loc[best_form_idx, "Recent Form (3 wk avg)"]
col4.metric("Best Recent Form (3w)", f"{best_form_val:.1f}%", best_form_team)
# Optional secondary insights row
with st.expander("🔎 Extra insights"):
    # Safely get max rows
    ap_row = power.loc[power["All-Play %"].idxmax()] if power["All-Play %"].notna().any() else None
    sos_row = power.loc[power["SoS (opp PF avg)"].idxmax()] if power["SoS (opp PF avg)"].notna().any() else None

    if ap_row is not None:
        ap_team = ap_row["Team"]
        ap_val = ap_row["All-Play %"]
    else:
        ap_team, ap_val = "N/A", 0

    if sos_row is not None:
        sos_team = sos_row["Team"]
        sos_val = sos_row["SoS (opp PF avg)"]
    else:
        sos_team, sos_val = "N/A", 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Best All-Play %", f"{ap_val:.1f}%", ap_team)
    c2.metric("Hardest SoS (opp PF)", f"{sos_val:.1f}", sos_team)
    c3.metric("Teams", f"{power['Team'].nunique()}")

# =======================
#  FULL RANKINGS CHART
# =======================
st.subheader("🏆 Full Power Rankings — Chart")

# Sorted by Power Index, rank labels on bars
chart_df = power.sort_values("Power Index", ascending=True).copy()  # low→high so the top is at bottom
fig = px.bar(
    chart_df,
    x="Power Index",
    y="Team",
    orientation="h",
    text=chart_df["Rank"].astype(int).astype(str),
    hover_data={
        "Team": True,
        "Power Index": ":.2f",
        "All-Play %": ":.1f",
        "PF": ":.0f",
        "Avg Margin": ":.1f",
        "Recent Form (3 wk avg)": ":.1f",
        "SoS (opp PF avg)": ":.1f",
    },
    color="Power Index",
    color_continuous_scale="Blues",
)
fig.update_layout(
    xaxis_title="Power Index",
    yaxis_title="Team",
    showlegend=False,
    margin=dict(l=10, r=10, t=30, b=10),
)
fig.update_traces(
    textposition="outside",
    cliponaxis=False,
)
st.plotly_chart(fig, use_container_width=True)

# =======================
#   FULL RANKINGS TABLE
# =======================
st.subheader("📋 Full Power Rankings — Table")

# Create a display copy with formatted percentages, leaving numeric df intact for any future math
display = power.copy()
display["All-Play %"] = display["All-Play %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
display["Recent Form (3 wk avg)"] = display["Recent Form (3 wk avg)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
display["PF"] = display["PF"].map(lambda x: f"{x:.0f}" if pd.notna(x) else "")
display["Avg Margin"] = display["Avg Margin"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["SoS (opp PF avg)"] = display["SoS (opp PF avg)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["Power Index"] = display["Power Index"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")

# Reorder columns nicely
display = display[[
    "Rank",
    "Team",
    "Power Index",
    "All-Play %",
    "PF",
    "Avg Margin",
    "Recent Form (3 wk avg)",
    "SoS (opp PF avg)",
]]

st.dataframe(display, use_container_width=True, hide_index=True)

# ---- Download ----
st.download_button(
    "⬇️ Download Power Rankings CSV",
    data=power.to_csv(index=False).encode("utf-8"),
    file_name="power_rankings.csv",
    mime="text/csv",
)
