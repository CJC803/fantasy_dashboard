import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🚑 Injury Report")

data = st.session_state.get("data", {})
injuries = data.get("injuries", pd.DataFrame())

if injuries.empty:
    st.info("No injury data available.")
else:
    injuries.columns = injuries.columns.str.strip().str.lower()

    status_col = next((c for c in injuries.columns if "status" in c or "injury" in c), None)
    team_col = next((c for c in injuries.columns if "team" in c or "proteam" in c), None)
    pos_col = next((c for c in injuries.columns if "pos" in c), None)

    # Filter out healthy players
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

        if pos_col:
            positions = sorted(injuries[pos_col].dropna().unique())
            selected_positions = st.sidebar.multiselect("Filter by Position", positions, default=positions)
            injuries = injuries[injuries[pos_col].isin(selected_positions)]

        # === KPI Metrics ===
        total_injured = len(injuries)
        total_teams = injuries[team_col].nunique() if team_col else 0
        total_positions = injuries[pos_col].nunique() if pos_col else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Injured", total_injured)
        c2.metric("Teams Impacted", total_teams)
        c3.metric("Positions Affected", total_positions)
        st.caption(f"🕒 Updated: {pd.Timestamp.now():%b %d, %Y %I:%M %p}")

        # === Injury Table (Expandable) ===
        with st.expander("🩹 View Injury List"):
            st.dataframe(injuries, use_container_width=True)

        # === Charts ===
        if team_col and pos_col:
            col1, col2 = st.columns(2)

            # --- Team Bar Chart ---
            with col1:
                team_counts = injuries[team_col].value_counts().reset_index()
                team_counts.columns = ["Team", "Injured Players"]

                fig_team = px.bar(
                    team_counts,
                    x="Injured Players",
                    y="Team",
                    orientation="h",
                    text="Injured Players",
                    color="Injured Players",
                    color_continuous_scale=px.colors.sequential.Blues_r,
                    title="Team Injury Count",
                )
                fig_team.update_layout(
                    yaxis_title=None,
                    xaxis_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f0f0f0"),
                    coloraxis_showscale=False,
                    margin=dict(t=60, b=20),
                )
                fig_team.update_traces(textposition="outside")
                st.plotly_chart(fig_team, use_container_width=True)

            # --- Position Radar Chart ---
            with col2:
                pos_counts = injuries[pos_col].value_counts().reset_index()
                pos_counts.columns = ["Position", "Injured Players"]

                fig_radar = px.line_polar(
                    pos_counts,
                    r="Injured Players",
                    theta="Position",
                    line_close=True,
                    title="🕸️ Injuries by Position",
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
                )
                st.plotly_chart(fig_radar, use_container_width=True)
