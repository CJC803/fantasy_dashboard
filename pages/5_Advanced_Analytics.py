import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from utils import load_all

# -----------------------------------
# Page Setup
# -----------------------------------
st.set_page_config(page_title="Advanced Power Analytics", layout="wide")
st.title("🔍 Advanced Power Analytics")

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
power.columns = (
    power.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
    .str.replace("\u00a0", " ", regex=False)
)

rename_map = {
    "Actual Win": "Actual Win %",
    "Actual Win%": "Actual Win %",
    "Actual Win Percentage": "Actual Win %",
}
power.rename(columns=rename_map, inplace=True)

# -----------------------------------
# Helper: clean percent columns
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


for pct_col in ["All-Play %", "Actual Win %"]:
    power[pct_col] = clean_percent(power[pct_col])

numeric_cols = [
    "PF",
    "Avg Margin",
    "Recent Form (3-wk avg)",
    "Recent Margin (3-wk avg)",
    "SoS (opp PF avg)",
    "Power Index",
    "Rank",
]
for col in numeric_cols:
    power[col] = pd.to_numeric(power[col], errors="coerce")

power.sort_values("Rank", inplace=True)
power.reset_index(drop=True, inplace=True)

# -----------------------------------
# Dynamic Metric Correlation Selector
# -----------------------------------
st.subheader("📊 Metric Correlation Explorer")

metrics = [
    "All-Play %",
    "Actual Win %",
    "Avg Margin",
    "Recent Form (3-wk avg)",
    "Recent Margin (3-wk avg)",
    "SoS (opp PF avg)",
    "PF",
    "Power Index",
]

selected_metrics = st.multiselect(
    "Select metrics to compare with Power Index",
    metrics,
    default=["All-Play %", "Actual Win %", "Avg Margin"],
)

if selected_metrics:
    corr_df = (
        power[selected_metrics + ["Power Index"]]
        .corr(numeric_only=True)["Power Index"]
        .drop("Power Index")
        .sort_values(ascending=False)
        .to_frame("Correlation")
    )

    st.dataframe(
        corr_df.style.format("{:.2f}").background_gradient(cmap="Blues"),
        use_container_width=True,
    )

# -----------------------------------
# 🍀 Luck Index — Actual Win % vs All-Play %
# -----------------------------------
st.subheader("🍀 Luck Index vs Actual Results")

luck_df = power.dropna(subset=["Actual Win %", "All-Play %"]).copy()
luck_df["Luck Δ"] = luck_df["Actual Win %"] - luck_df["All-Play %"]

if not luck_df.empty:
    col1, col2 = st.columns([3, 2])

    with col1:
        fig = px.scatter(
            luck_df,
            x="All-Play %",
            y="Actual Win %",
            color="Luck Δ",
            text="Team",
            color_continuous_scale="Blues_r",
            hover_data={"Luck Δ": ":.1f"},
            title="Luck vs Performance Scatter",
        )
        fig.add_shape(
            type="line",
            x0=luck_df["All-Play %"].min(),
            y0=luck_df["All-Play %"].min(),
            x1=luck_df["All-Play %"].max(),
            y1=luck_df["All-Play %"].max(),
            line=dict(color="gray", dash="dash"),
        )
        fig.update_traces(textposition="top center", marker=dict(size=10))
        fig.update_layout(
            xaxis_title="All-Play %",
            yaxis_title="Actual Win %",
            coloraxis_colorbar_title="Luck Δ",
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🍀 Luckiest & Unluckiest Teams")
        sorted_luck = luck_df.sort_values("Luck Δ", ascending=False)
        st.dataframe(
            sorted_luck[["Team", "All-Play %", "Actual Win %", "Luck Δ"]]
            .assign(**{"Luck Δ": sorted_luck["Luck Δ"].map("{:+.1f}".format)})
            .reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("Not enough data to compute luck metrics.")

# -----------------------------------
# 🔥 Luck + Power Heat Map
# -----------------------------------
st.subheader("🔥 Luck + Power Index Heat Map")

if not luck_df.empty:
    heat_df = luck_df[["Team", "Luck Δ", "Power Index"]].copy()
    fig_heat = px.density_heatmap(
        heat_df,
        x="Luck Δ",
        y="Power Index",
        color_continuous_scale="Blues_r",
        nbinsx=10,
        nbinsy=10,
        title="Luck vs Power Index Density",
    )
    fig_heat.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Luck Δ (Actual Win % - All-Play %)",
        yaxis_title="Power Index",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# -----------------------------------
# 🧭 Team Radar Visualization
# -----------------------------------
st.subheader("📡 Normalized Team Performance Radar")

teams = sorted(power["Team"].dropna().unique())
selected_team = st.selectbox("Select a team", teams)

if selected_team:
    # Normalize across all metrics
    scaled = power.copy()
    scaler = MinMaxScaler(feature_range=(0, 100))
    scaled[metrics] = scaler.fit_transform(scaled[metrics])

    row = scaled[scaled["Team"] == selected_team].iloc[0]
    radar_values = [row[m] for m in metrics]

    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=radar_values,
            theta=metrics,
            fill="toself",
            name=selected_team,
        )
    )
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# -----------------------------------
# ✅ Suggested Improvements
# -----------------------------------
with st.expander("💡 Suggestions for Future Enhancements"):
    st.markdown(
        """
        - Add a **trend tracker** over time to visualize weekly Power Index or Luck changes.  
        - Include a **SoS Impact chart** (overlay Power Index vs Strength of Schedule).  
        - Use a **regression trendline** to quantify Luck vs Performance slope per team.  
        - Introduce **clustering** to group teams with similar stat profiles.  
        - Optionally, connect to weekly matchup pages to dynamically update analytics.
        """
    )
