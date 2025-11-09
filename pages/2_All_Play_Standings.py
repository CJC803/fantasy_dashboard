import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.title("🏈 All-Play Standings")

# === Load current data ===
data = st.session_state.get("data", {})
allplay = data.get("allplay", pd.DataFrame())

if allplay.empty:
    st.info("No All-Play data available.")
else:
    # === Normalize ===
    allplay.columns = allplay.columns.str.strip()
    if "Win%" not in allplay.columns:
        st.error("Missing 'Win%' column in data.")
    else:
        allplay = allplay.sort_values("Win%", ascending=False).reset_index(drop=True)

        # === Step 1: Log daily snapshot ===
        today = datetime.now().strftime("%Y-%m-%d")
        st.session_state.setdefault("allplay_history", {})

        # Store snapshot only once per day
        if today not in st.session_state["allplay_history"]:
            st.session_state["allplay_history"][today] = allplay.copy()
            st.toast(f"📊 Saved daily snapshot for {today}", icon="✅")

        # === Step 2: Compare to previous day ===
        history = st.session_state["allplay_history"]
        merged = allplay.copy()

        if len(history) >= 2:
            dates = sorted(history.keys())
            prev_day, curr_day = dates[-2], dates[-1]
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

        # === Step 3: KPI metrics ===
        # Drop any rows missing key stats
        merged = merged.dropna(subset=["Team", "Win%"])
        
        if not merged.empty:
            top_team = merged.iloc[0]["Team"]
            top_win = merged.iloc[0]["Win%"]
        
            bottom_team = merged.iloc[-1]["Team"]
            bottom_win = merged.iloc[-1]["Win%"]
        
            # Handle non-numeric or missing values
            top_win = float(top_win) if pd.notna(top_win) else 0
            bottom_win = float(bottom_win) if pd.notna(bottom_win) else 0
        
            c1, c2, c3 = st.columns(3)
            c1.metric("Teams Tracked", len(merged))
            c2.metric("Lowest All-Play Team", f"{bottom_team} ({bottom_win:.3f})")
            c3.metric("Top Team", f"{top_team} ({top_win:.3f})")
        else:
            st.warning("⚠️ No valid teams or Win% data available.")

        if trend_available:
            avg_delta = merged["Δ Win%"].mean()
            biggest_riser = merged.loc[merged["Δ Win%"].idxmax()]
            biggest_faller = merged.loc[merged["Δ Win%"].idxmin()]

            st.markdown(
                f"""
                <div style='background-color:#111;padding:12px;border-radius:10px;margin-top:1rem;margin-bottom:1.2rem'>
                    <h3 style='color:#ff9f43;margin:0;font-weight:600'>
                        🥇 {top_team} leads ({top_win:.3f} Win%)<br>
                        📈 Riser: {biggest_riser["Team"]} ({biggest_riser["Δ Win%"]:+.3f}) &nbsp;&nbsp;
                        📉 Drop: {biggest_faller["Team"]} ({biggest_faller["Δ Win%"]:+.3f})
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )

        # === Step 4: Chart ===
        fig = px.bar(
            merged,
            x="Team",
            y="Win%",
            color="Win%",
            color_continuous_scale=px.colors.sequential.Blues_r,
            title="Cumulative All-Play Win Percentage",
        )
        
        # Remove text labels above bars
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Win%: %{y:.3f}<extra></extra>"
        )
        
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


        # === Step 5: Detailed Table ===
        st.subheader("📋 Detailed Standings")

        def style_delta(val):
            color = "#2ecc71" if val > 0 else "#e74c3c" if val < 0 else "#999"
            return f"color:{color}; font-weight:600"

        merged = merged[["Team", "Wins", "Losses", "Win%", "Δ Win%"]]
        styled = merged.style.format({"Win%": "{:.3f}", "Δ Win%": "{:+.3f}"}).applymap(style_delta, subset=["Δ Win%"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # === Footer ===
        st.caption(
            f"🕒 Updated {datetime.now():%b %d, %Y %I:%M %p} — comparing daily snapshots ({'trend active' if trend_available else 'first day recorded'})."
        )
