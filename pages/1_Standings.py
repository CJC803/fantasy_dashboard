import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import load_all

st.title("🏆 Standings & Playoff Bracket")

# === Load data ===
if "data" not in st.session_state:
    st.session_state["data"] = load_all()

data = st.session_state["data"]
standings = data["standings"]

if standings.empty:
    st.warning("No standings data found.")
else:
    # --- Identify columns dynamically ---
    team_col = next((c for c in standings.columns if "team" in c.lower()), None)
    win_col = next((c for c in standings.columns if "win" in c.lower() or "pct" in c.lower()), None)

    if not team_col or not win_col:
        st.error("Couldn't identify team or win column. Please check your sheet headers.")
        st.dataframe(standings.head())
    else:
        # --- Prepare data ---
        standings[win_col] = pd.to_numeric(standings[win_col], errors="coerce")
        standings = standings.sort_values(win_col, ascending=False).reset_index(drop=True)
        standings["Rank"] = range(1, len(standings) + 1)

       # === Vertical Bar Chart of Current Standings ===
colors = []
for r in standings["Rank"]:
    if r in [4, 5]:  # Play-in teams
        colors.append("orange")
    elif r <= 3:      # Playoff locks
        colors.append("green")
    else:             # Outside playoff
        colors.append("lightgray")

fig_chart = go.Figure(
    go.Bar(
        x=standings[team_col],
        y=standings[win_col],
        marker_color=colors
    )
)

# Add playoff cutoff marker (between 5th and 6th)
cutoff_y = standings.loc[5, win_col] - 0.05 if len(standings) > 5 else None
if cutoff_y:
    fig_chart.add_hline(
        y=cutoff_y,
        line_dash="dash",
        line_color="red",
        annotation_text="Playoff Cutoff",
        annotation_position="top right",
        annotation_font_color="red",
    )

fig_chart.update_layout(
    title="📈 Team Performance by Record",
    xaxis_title="Team",
    yaxis_title=win_col,
    height=450,
    margin=dict(t=40, b=40, l=40, r=20),
)
st.plotly_chart(fig_chart, use_container_width=True)

    

       
        # === Playoff Bracket ===
        top5 = standings.head(5)
        team_names = top5[team_col].tolist()

        if len(team_names) < 5:
            st.warning("Need at least 5 teams to draw the playoff bracket.")
        else:
            fig = go.Figure()
            nodes = {
                "4": (0, 3), "5": (0, 1),
                "1": (2, 4), "2": (2, 2), "3": (2, 0),
                "F1": (4, 3), "F2": (4, 1),
                "W": (6, 2),
            }
            labels = {
                "4": f"4️⃣ {team_names[3]}",
                "5": f"5️⃣ {team_names[4]}",
                "1": f"1️⃣ {team_names[0]}",
                "2": f"2️⃣ {team_names[1]}",
                "3": f"3️⃣ {team_names[2]}",
                "F1": "🏆 Winner of 1 vs (4/5)",
                "F2": "🏆 Winner of 2 vs 3",
                "W": "🏆 Champion",
            }

            for key, (x, y) in nodes.items():
                fig.add_trace(
                    go.Scatter(
                        x=[x],
                        y=[y],
                        mode="text",
                        text=[labels[key]],
                        textfont=dict(size=16),
                        hoverinfo="none",
                    )
                )

            fig.update_layout(
                title="🏈 Fantasy Playoff Bracket (Top 5 Teams)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                height=400,
                margin=dict(t=40, b=20, l=20, r=20),
                annotations=[
                    dict(x=0, y=4.2, text="Week 15 – Play-In", showarrow=False, font=dict(size=10, color="gray")),
                    dict(x=2, y=4.6, text="Week 16 – Semifinals", showarrow=False, font=dict(size=10, color="gray")),
                    dict(x=4, y=4.2, text="Week 17 – Championship", showarrow=False, font=dict(size=10, color="gray")),
                ],
            )
            st.plotly_chart(fig, use_container_width=True)
