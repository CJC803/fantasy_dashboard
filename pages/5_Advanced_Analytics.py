import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
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
# Cleaning helpers
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

for col in ["All-Play %", "Actual Win %"]:
    power[col] = clean_percent(power[col])

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

# Metrics to analyze (excluding Power Index)
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
]

selected_metrics = st.multiselect(
    "Select metrics to analyze correlation with Power Index",
    metrics,
    default=metrics,  # Default = all metrics (excluding Power Index)
)

if selected_metrics:
    corr_df = (
        power[selected_metrics + ["Power Index"]]
        .corr(numeric_only=True)["Power Index"]
        .drop("Power Index")
        .sort_values(ascending=False)
        .to_frame("Correlation with Power Index")
    )

    st.dataframe(
        corr_df.style.format("{:.2f}").background_gradient(cmap="Blues"),
        use_container_width=True,
    )
else:
    st.info("Select at least one metric to view correlation with Power Index.")


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
            color_continuous_scale="Blues_r",
            hover_data={
                "Team": True,
                "All-Play %": ":.1f",
                "Actual Win %": ":.1f",
                "Luck Δ": ":.1f",
            },
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
        fig.update_traces(marker=dict(size=9))
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

    # 🔥 Heatmap — Luck vs Power
    st.subheader("🔥 Luck vs Power Index Heatmap")
    fig_heat = px.density_heatmap(
        luck_df,
        x="Luck Δ",
        y="Power Index",
        nbinsx=10,
        nbinsy=10,
        color_continuous_scale="Blues",
        title="Luck Δ vs Power Index Density",
    )
    fig_heat.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Luck Δ (Actual Win % - All-Play %)",
        yaxis_title="Power Index",
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Not enough data to compute luck metrics.")

# -----------------------------------
# 📡 Normalized Team Performance Radar
# -----------------------------------
st.subheader("📡 Normalized Team Performance Radar")

teams = sorted(power["Team"].dropna().unique())
selected_team = st.selectbox("Select a team", teams)

if selected_team:
    scaler = MinMaxScaler(feature_range=(0, 100))
    scaled = power.copy()
    scaled[metrics] = scaler.fit_transform(scaled[metrics])

    row = scaled[scaled["Team"] == selected_team].iloc[0]
    fig_radar = go.Figure(
        go.Scatterpolar(
            r=[row[m] for m in metrics],
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

team_a, team_b = st.columns(2)
team1 = team_a.selectbox("Select Team A", teams, key="team_a")
team2 = team_b.selectbox("Select Team B", teams, key="team_b")

if team1 and team2:
    scaler = MinMaxScaler(feature_range=(0, 100))
    scaled = power.copy()
    scaled[metrics] = scaler.fit_transform(scaled[metrics])

    row1 = scaled[scaled["Team"] == team1].iloc[0]
    row2 = scaled[scaled["Team"] == team2].iloc[0]

    fig_overlay = go.Figure()
    fig_overlay.add_trace(go.Scatterpolar(r=[row1[m] for m in metrics], theta=metrics, fill="toself", name=team1))
    fig_overlay.add_trace(go.Scatterpolar(r=[row2[m] for m in metrics], theta=metrics, fill="toself", name=team2))
    fig_overlay.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig_overlay, use_container_width=True)

# -----------------------------------
# 🤖 Team Clustering by Power Metrics
# -----------------------------------
st.subheader("🤖 Team Clusters by Power Profile")

cluster_features = ["All-Play %", "Actual Win %", "Avg Margin", "SoS Played", "Power Index"]
cluster_df = power.dropna(subset=cluster_features).copy()

scaler = MinMaxScaler()
scaled_features = scaler.fit_transform(cluster_df[cluster_features])

kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
cluster_df["Cluster"] = kmeans.fit_predict(scaled_features)

fig_cluster = px.scatter_3d(
    cluster_df,
    x="Power Index",
    y="Avg Margin",
    z="SoS Played",
    color="Cluster",
    hover_name="Team",
    color_continuous_scale="Blues",
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

