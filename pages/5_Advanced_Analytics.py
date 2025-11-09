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
    .str.replace("\ufeff", "", regex=False)
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
# Clean numeric and percentage columns
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
    "SoS Played",
    "SoS Remaining",
    "SoS Δ vs Avg",
    "Power Index",
    "Rank",
]
for col in numeric_cols:
    power[col] = pd.to_numeric(power[col], errors="coerce")

power.sort_values("Rank", inplace=True)
power.reset_index(drop=True, inplace=True)

# -----------------------------------
# 📊 Metric Correlation Explorer
# -----------------------------------
st.subheader("📊 Metric Correlation Explorer")

metrics = [
    "All-Play %",
    "Actual Win %",
    "Avg Margin",
    "Recent Form (3-wk avg)",
    "Recent Margin (3-wk avg)",
    "SoS Played",
    "SoS Remaining",
    "SoS Δ vs Avg",
    "PF",
    "Power Index",
]

selected_metrics = st.multiselect(
    "Select metrics to compare with Power Index",
    metrics,
    default=metrics,  # Show all metrics by default
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
# 🧭 Team Radar Visualization
# -----------------------------------
st.subheader("📡 Normalized Team Performance Radar")

teams = sorted(power["Team"].dropna().unique())
selected_team = st.selectbox("Select a team", teams)

if selected_team:
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
# 🧩 Multi-Team Radar Overlay Comparison
# -----------------------------------
st.subheader("🧩 Compare Two Teams — Multi-Metric Radar Overlay")

team_options = sorted(power["Team"].dropna().unique())
col1, col2 = st.columns(2)
team_a = col1.selectbox("Select Team A", team_options, key="team_a")
team_b = col2.selectbox("Select Team B", team_options, key="team_b")

if team_a and team_b:
    scaled = power.copy()
    scaler = MinMaxScaler(feature_range=(0, 100))
    scaled[metrics] = scaler.fit_transform(scaled[metrics])

    row_a = scaled[scaled["Team"] == team_a].iloc[0]
    row_b = scaled[scaled["Team"] == team_b].iloc[0]

    fig_compare = go.Figure()
    fig_compare.add_trace(
        go.Scatterpolar(r=[row_a[m] for m in metrics], theta=metrics, fill='toself', name=team_a)
    )
    fig_compare.add_trace(
        go.Scatterpolar(r=[row_b[m] for m in metrics], theta=metrics, fill='toself', name=team_b)
    )

    fig_compare.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig_compare, use_container_width=True)

# -----------------------------------
# 🤖 Team Clustering by Power Metrics
# -----------------------------------
st.subheader("🤖 Team Clusters by Power Profile")

from sklearn.cluster import KMeans
import numpy as np

cluster_features = ["All-Play %", "Actual Win %", "Avg Margin", "SoS Played", "Power Index"]
cluster_df = power.dropna(subset=cluster_features).copy()

# Normalize for fair clustering
scaler = MinMaxScaler()
scaled_features = scaler.fit_transform(cluster_df[cluster_features])

# 3 clusters — you can adjust if you prefer
kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
cluster_df["Cluster"] = kmeans.fit_predict(scaled_features)

fig_cluster = px.scatter_3d(
    cluster_df,
    x="Power Index",
    y="Avg Margin",
    z="SoS Played",
    color="Cluster",
    hover_name="Team",
    color_continuous_scale="Blues_r",
    title="Team Clusters by Power Profile",
)
fig_cluster.update_layout(margin=dict(l=10, r=10, t=40, b=10))
st.plotly_chart(fig_cluster, use_container_width=True)

with st.expander("📋 Cluster Breakdown"):
    st.dataframe(
        cluster_df[["Team", "Cluster"] + cluster_features],
        use_container_width=True,
        hide_index=True,
    )
# -----------------------------------
# ✅ Suggestions for Future Enhancements
# -----------------------------------
with st.expander("💡 Suggestions for Future Enhancements"):
    st.markdown(
        """
        - Add a **trend tracker** for weekly Power Index and Luck Δ over time.
        - Include a **SoS Influence Chart** comparing Power Index vs SoS Played.
        - Use **regression lines** to quantify correlation strength.
        - Cluster teams with similar Power Index profiles.
        - Add **multi-metric radar overlay** for comparing two teams.
        """
    )
