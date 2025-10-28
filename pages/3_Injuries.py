import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🚑 Injury Report")

data = st.session_state.get("data", {})
injuries = data.get("injuries", pd.DataFrame())

if injuries.empty:
    st.info("No injury data available.")
else:
    # === Normalize column names ===
    injuries.columns = injuries.columns.str.strip().str.lower()

    # === Identify key columns ===
    status_col = next((c for c in injuries.columns if "status" in c or "injury" in c), None)
    team_col = next((c for c in injuries.columns if "team" in c or "proteam" in c), None)

    # === Filter out healthy players ===
    if status_col:
        injuries = injuries[~injuries[status_col].str.contains("active|healthy|none", case=False, na=False)]

    if injuries.empty:
        st.success("✅ No current injuries — everyone’s healthy!")
    else:
        # === Sidebar Filters ===
        st.sidebar.header("Filters")

        if team_col:
            teams = sorted(injuries[team_col].dropna().unique())
            selected_team = st.sidebar.selectbox("Filter by Team", ["All Teams"] + teams)
            if selected_team != "All Teams":
                injuries = injuries[injuries[team_col] == selected_team]

        # === KPI Metrics ===
        total_injured = len(injuries)
        total_teams = injuries[team_col].nunique() if team_col else 0

        c1, c2 = st.columns(2)
        c1.metric("Total Injured", total_injured)
        c2.metric("Teams Impacted", total_teams)
        st.caption(f"🕒 Updated: {pd.Timestamp.now():%b %d, %Y %I:%M %p}")

        # === Injury Table (Expandable) ===
        with st.expander("🩹 View Injury List"):
            st.dataframe(injuries, use_container_width=True)

        # === Charts: Both by Team ===
        if team_col:
            team_counts = injuries[team_col].value_counts().reset_index()
            team_counts.columns = ["Team", "Injured Players"]

            col1, col2 = st.columns(2)

            # --- Radar Chart: Injuries by Team ---
            with col1:
                fig_radar = px.line_polar(
                    team_counts,
                    r="Injured Players",
                    theta="Team",
                    line_close=True,
                    title="🕸️ Injured Players by Team (Radar)",
                    color_discrete_sequence=["#ff9f43"],  # gold accent
                )
                fig_radar.update_traces(
                    fill="toself",
                    line_color="#ff9f43",
                    hovertemplate="<b>%{theta}</b><br>Injured: %{r}<extra></extra>",
                )
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, showticklabels=True, color="gray"),
                        angularaxis=dict(tickfont=dict(size=12))
                    ),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f0f0f0"),
                    margin=dict(t=60, b=20),
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            # --- Bar Chart: Injuries by Team ---
            with col2:
                fig_bar = px.bar(
                    team_counts,
                    x="Team",
                    y="Injured Players",
                    color="Injured Players",
                    text="Injured Players",
                    color_continuous_scale=px.colors.sequential.Blues_r,
                    title="Injured Players by Team (Bar)",
                )
                fig_bar.update_traces(textposition="outside")
                fig_bar.update_layout(
                    xaxis_title=None,
                    yaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f0f0f0"),
                    coloraxis_showscale=False,
                    margin=dict(t=60, b=20),
                )
                st.plotly_chart(fig_bar, use_container_width=True)
