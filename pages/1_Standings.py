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

        st.subheader("📊 Current Standings")
        st.dataframe(standings[[team_col, win_col, "Rank"]], use_container_width=True)

        # === Create playoff bracket (Top 5) ===
        top5 = standings.head(5)
        team_names = top5[team_col].tolist()

        if len(team_names) < 5:
            st.warning("Need at least 5 teams to draw the playoff bracket.")
        else:
            # Coordinates for bracket layout
            nodes = {
                "R1_4": (0, 2),   # 4 seed
                "R1_5": (0, 1),   # 5 seed
                "SF_1": (2, 3.5), # 1 seed
                "SF_2": (2, 1.5), # 2 seed
                "SF_3": (2, 0.5), # 3 seed
                "F_1": (4, 2),    # Championship
            }

            labels = {
                "R1_4": f"4️⃣ {team_names[3]}",
                "R1_5": f"5️⃣ {team_names[4]}",
                "SF_1": f"1️⃣ {team_names[0]}",
                "SF_2": f"2️⃣ {team_names[1]}",
                "SF_3": f"3️⃣ {team_names[2]}",
                "F_1": "🏆 Winner",
            }

            fig = go.Figure()

            # Draw connecting lines
            lines = [
                # Play-in winner → Seed 1 (Week 16)
                ((0.5, 1.5), (2, 3.5)),
                # Semifinal winners → Championship
                ((2.5, 2.5), (4, 2)),
                ((2.5, 1.0), (4, 2)),
            ]
            for (x_pair, y_pair) in lines:
                fig.add_shape(
                    type="line",
                    x0=x_pair[0],
                    y0=y_pair[0],
                    x1=x_pair[1],
                    y1=y_pair[1],
                    line=dict(color="gray", width=2),
                )

            # Add text labels for each slot
            for key, (x, y) in nodes.items():
                fig.add_trace(
                    go.Scatter(
                        x=[x],
                        y=[y],
                        mode="text",
                        text=[labels[key]],
                        textfont=dict(size=14),
                        hoverinfo="none",
                    )
                )

            # Final layout and annotations
            fig.update_layout(
                title="🏈 Fantasy Playoff Bracket (5 Teams)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                height=500,
                margin=dict(t=60, b=20, l=20, r=20),
                annotations=[
                    dict(x=0, y=3, text="Week 15 – Play-In", showarrow=False, font=dict(size=12, color="gray")),
                    dict(x=2, y=4.5, text="Week 16 – Semifinals", showarrow=False, font=dict(size=12, color="gray")),
                    dict(x=4, y=3.5, text="Week 17 – Championship", showarrow=False, font=dict(size=12, color="gray")),
                ],
            )

            st.plotly_chart(fig, use_container_width=True)
