import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_all

# ---- Load Data ----
if "data" not in st.session_state:
    st.session_state["data"] = load_all()

data = st.session_state["data"]
power = data["power"]
st.write("Raw All-Play % values:", power["All-Play %"].head(10))

st.set_page_config(page_title="Power Rankings", layout="wide")
st.title("⚡ Power Rankings")

if power.empty:
    st.warning("No power ranking data found.")
    st.stop()

# ---- Clean up dataframe ----
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
# ---- Numeric cleanup ----
import re

def clean_percent_column(series: pd.Series) -> pd.Series:
    """Convert messy percent strings like '65%', '65.0 %', or '0.65' into floats."""
    s = series.astype(str)
    # Remove %, commas, and invisible space characters (Google Sheets adds weird ones)
    s = s.apply(lambda x: re.sub(r"[%\s\u202F\u00A0,]", "", x))
    # Convert to numeric
    s = pd.to_numeric(s, errors="coerce")
    # Scale decimals if 0–1 range
    if s.dropna().max() <= 1:
        s *= 100
    return s

# ✅ Apply cleaner BEFORE other numeric conversions
power["All-Play %"] = clean_percent_column(power["All-Play %"])
power["Recent Form (3 wk avg)"] = clean_percent_column(power["Recent Form (3 wk avg)"])

# ✅ Now convert the rest
for c in ["PF", "Avg Margin", "SoS (opp PF avg)", "Power Index"]:
    power[c] = pd.to_numeric(power[c], errors="coerce")

power = power.sort_values("Rank", ascending=True).reset_index(drop=True)
# ---- Adjust percentages ----
if power["All-Play %"].max() <= 1:  # detect if values are like 0.67 not 67
    power["All-Play %"] = power["All-Play %"] * 100
# ---- Summary Stats ----
st.subheader("📈 Summary Insights")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Top Team", power.loc[0, "Team"])
col2.metric("Avg Power Index", f"{power['Power Index'].mean():.2f}")
col3.metric("Avg PF", f"{power['PF'].mean():.1f}")
col4.metric("Avg Margin", f"{power['Avg Margin'].mean():.1f}")

# ---- Power Index vs All-Play Scatter ----
with st.expander("📊 View Power Index vs All-Play % Chart", expanded=False):
    fig = px.scatter(
        power,
        x="All-Play %",
        y="Power Index",
        text="Team",
        color="Recent Form (3 wk avg)",
        size="PF",
        color_continuous_scale="Blues",
        title="Power Index vs All-Play %",
        hover_data=["Team", "PF", "Avg Margin", "SoS (opp PF avg)"],
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)

# ---- Rankings Table ----
st.subheader("🏆 Full Power Rankings")
styled = power.style.background_gradient(
    subset=["Power Index"], cmap="YlGnBu"
).format({
    "All-Play %": "{:.1f}%",
    "Avg Margin": "{:.1f}",
    "PF": "{:.0f}",
    "Recent Form (3 wk avg)": "{:.1f}",
    "SoS (opp PF avg)": "{:.1f}",
    "Power Index": "{:.2f}",
})

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
)

# ---- Download ----
st.download_button(
    "⬇️ Download Power Rankings CSV",
    data=power.to_csv(index=False).encode("utf-8"),
    file_name="power_rankings.csv",
    mime="text/csv",
)
