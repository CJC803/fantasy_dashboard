import re
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_all

# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(page_title="Power Rankings", layout="wide")
st.title("⚡ Power Rankings")

# -------------------------------
# Load Data
# -------------------------------
if "data" not in st.session_state:
    st.session_state["data"] = load_all()
data = st.session_state["data"]
power = data.get("power", pd.DataFrame())

if power.empty:
    st.warning("No power ranking data found.")
    st.stop()

# -------------------------------
# Normalize & Validate Columns
# -------------------------------
power.columns = power.columns.astype(str).str.strip()
power.columns = power.columns.str.replace(r"\s+", " ", regex=True)
power.columns = power.columns.str.replace("\u00a0", " ", regex=False)
power.columns = power.columns.str.replace("\u202f", " ", regex=False)

rename_map = {
    "Actual Win": "Actual Win %",
    "Actual Win%": "Actual Win %",
    "Actual Win %": "Actual Win %",
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
    "SoS (opp PF avg)",
    "Power Index",
]

missing = [c for c in expected_cols if c not in power.columns]
if missing:
    st.error(f"Missing columns: {', '.join(missing)}")
    st.dataframe(power.head())
    st.stop()

# -------------------------------
# Helpers
# -------------------------------
def clean_percent_column(series: pd.Series) -> pd.Series:
    """Handles messy % strings and converts to float 0–100."""
    def normalize(x):
        if pd.isna(x):
            return None
        x = re.sub(r"[^0-9.\-]", "", str(x))
        try:
            val = float(x)
            return val * 100 if 0 <= val <= 1 else val
        except ValueError:
            return None
    return pd.Series([normalize(v) for v in series], dtype="float")


# -------------------------------
# Numeric Cleanup
# -------------------------------
for col in ["All-Play %", "Actual Win %"]:
    power[col] = clean_percent_column(power[col])

for c in [
    "PF",
    "Avg Margin",
    "SoS (opp PF avg)",
    "Power Index",
    "Rank",
    "Recent Form (3-wk avg)",
    "Recent Margin (3-wk avg)",
]:
    power[c] = pd.to_numeric(power[c], errors="coerce")

# Sort
if power["Rank"].notna().any():
    power.sort_values("Rank", inplace=True)
else:
    power.sort_values("Power Index", ascending=False, inplace=True)
    power["Rank"] = range(1, len(power) + 1)
power.reset_index(drop=True, inplace=True)

# -------------------------------
# Summary Insights
# -------------------------------
st.subheader("📈 Summary Insights")
col1, col2, col3, col4 = st.columns(4)

top_team = power.loc[power["Rank"].idxmin(), "Team"]
col1.metric("Top Team", top_team)
col2.metric("Avg Power Index", f"{power['Power Index'].mean():.2f}")
col3.metric("Avg PF", f"{power['PF'].mean():.1f}")

best_form_idx = power["Recent Form (3-wk avg)"].idxmax()
col4.metric(
    "Best 3-Week Avg PF",
    f"{power.loc[best_form_idx, 'Recent Form (3-wk avg)']:.1f}",
    power.loc[best_form_idx, "Team"],
)

with st.expander("🔎 Extra insights"):
    ap_row = power.loc[power["All-Play %"].idxmax()] if power["All-Play %"].notna().any() else None
    win_row = power.loc[power["Actual Win %"].idxmax()] if power["Actual Win %"].notna().any() else None
    sos_row = power.loc[power["SoS (opp PF avg)"].idxmax()] if power["SoS (opp PF avg)"].notna().any() else None

    c1, c2, c3 = st.columns(3)
    if ap_row is not None:
        c1.metric("Best All-Play %", f"{ap_row['All-Play %']:.1f}%", ap_row["Team"])
    if win_row is not None:
        c2.metric("Best Actual Win %", f"{win_row['Actual Win %']:.1f}%", win_row["Team"])
    if sos_row is not None:
        c3.metric("Hardest SoS (opp PF)", f"{sos_row['SoS (opp PF avg)']:.1f}", sos_row["Team"])

# -------------------------------
# Full Rankings Bar Chart
# -------------------------------
st.subheader("🏆 Full Power Rankings — Chart")

chart_df = power.sort_values("Power Index", ascending=True).copy()
fig = px.bar(
    chart_df,
    x="Power Index",
    y="Team",
    orientation="h",
    text=chart_df["Rank"].astype(int).astype(str),
    hover_data={
        "Power Index": ":.2f",
        "All-Play %": ":.1f",
        "Actual Win %": ":.1f",
        "PF": ":.0f",
        "Avg Margin": ":.1f",
        "Recent Form (3-wk avg)": ":.1f",
        "Recent Margin (3-wk avg)": ":.1f",
        "SoS (opp PF avg)": ":.1f",
    },
    color="Power Index",
    color_continuous_scale="Blues_r",
)
fig.update_layout(
    xaxis_title="Power Index",
    yaxis_title="Team",
    showlegend=False,
    margin=dict(l=10, r=10, t=30, b=10),
)
fig.update_traces(textposition="outside", cliponaxis=False)
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Luck Index Scatter
# -------------------------------
st.subheader("🍀 Luck Index — Actual Win % vs All-Play %")

luck_df = power.dropna(subset=["Actual Win %", "All-Play %"]).copy()
luck_df["Luck Δ"] = luck_df["Actual Win %"] - luck_df["All-Play %"]

fig_luck = px.scatter(
    luck_df,
    x="All-Play %",
    y="Actual Win %",
    text="Team",
    color="Luck Δ",
    color_continuous_scale="RdYlGn",
    hover_data={
        "All-Play %": ":.1f",
        "Actual Win %": ":.1f",
        "Luck Δ": ":.1f",
    },
)
fig_luck.add_shape(
    type="line",
    x0=luck_df["All-Play %"].min(),
    y0=luck_df["All-Play %"].min(),
    x1=luck_df["All-Play %"].max(),
    y1=luck_df["All-Play %"].max(),
    line=dict(color="gray", dash="dash"),
)
fig_luck.update_traces(textposition="top center", marker=dict(size=10))
fig_luck.update_layout(
    xaxis_title="All-Play %",
    yaxis_title="Actual Win %",
    coloraxis_colorbar_title="Luck Δ",
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig_luck, use_container_width=True)

# -------------------------------
# Full Rankings Table
# -------------------------------
st.subheader("📋 Full Power Rankings — Table")

display = power.copy()
display["All-Play %"] = display["All-Play %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
display["Actual Win %"] = display["Actual Win %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
display["Recent Form (3-wk avg)"] = display["Recent Form (3-wk avg)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["Recent Margin (3-wk avg)"] = display["Recent Margin (3-wk avg)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["PF"] = display["PF"].map(lambda x: f"{x:.0f}" if pd.notna(x) else "")
display["Avg Margin"] = display["Avg Margin"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["SoS (opp PF avg)"] = display["SoS (opp PF avg)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
display["Power Index"] = display["Power Index"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")

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
        "SoS (opp PF avg)",
    ]
]
st.dataframe(display, use_container_width=True, hide_index=True)

# -------------------------------
# Download Button
# -------------------------------
st.download_button(
    "⬇️ Download Power Rankings CSV",
    data=power.to_csv(index=False).encode("utf-8"),
    file_name="power_rankings.csv",
    mime="text/csv",
)
