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
            fig = go.Figure()

            # Define node positions (x, y)
            nodes = {
                # Round 1
                "4": (0, 3),
                "5": (0, 1),
                # Semifinals
                "1": (2, 4),
                "2": (2, 2),
                "3": (2, 0),
                # Finals
                "F1": (4, 3),
                "F2": (4, 1),
                # Winner
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

            # Draw connecting lines (like real bracket)
            lines = [
                # Round 1 -> Semifinal 1
                ((0.5, 2), (2, 3.5)),
                # Semifinal 1 -> Final
                ((2.5, 3.5), (4, 3)),
                # Semifinal 2 (2 vs 3) -> Final
                ((2.5, 1), (4, 1)),
                # Final -> Champion
                ((4.5, 2), (6, 2)),
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

            # Plot team positions
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

            # Layout like real bracket
            fig.update_layout(
                title="🏈 Fantasy Playoff Bracket (5 Teams – True Elimination)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                height=600,
                margin=dict(t=60, b=20, l=20, r=20),
                annotations=[
                    dict(x=0, y=4.5, text="Week 15 – Play-In", showarrow=False, font=dict(size=12, color="gray")),
                    dict(x=2, y=5, text="Week 16 – Semifinals", showarrow=False, font=dict(size=12, color="gray")),
                    dict(x=4, y=4.5, text="Week 17 – Championship", showarrow=False, font=dict(size=12, color="gray")),
                ],
            )

            st.plotly_chart(fig, use_container_width=True)
