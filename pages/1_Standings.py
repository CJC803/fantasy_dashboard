import plotly.graph_objects as go

# === Create bracket data ===
# Assumes standings are already sorted best→worst and have columns: Rank, Team, Win %
bracket_teams = standings.loc[:4, [team_col, "Rank"]].copy()  # Top 5
team_names = bracket_teams[team_col].tolist()

# Coordinates for bracket
nodes = {
    # Round 1 (Play-in)
    "R1_4": (0, 2),
    "R1_5": (0, 1),
    # Round 2 (Semifinals)
    "SF_1": (2, 3.5),
    "SF_2": (2, 1.5),
    "SF_3": (2, 0.5),
    # Championship
    "F_1": (4, 2),
}

# Team labels for each slot
labels = {
    "R1_4": f"4️⃣ {team_names[3]}",
    "R1_5": f"5️⃣ {team_names[4]}",
    "SF_1": f"1️⃣ {team_names[0]}",
    "SF_2": f"2️⃣ {team_names[1]}",
    "SF_3": f"3️⃣ {team_names[2]}",
    "F_1": "🏆 Winner",
}

# Create figure
fig = go.Figure()

# Draw lines for matchups
lines = [
    # Play-in → Semifinal 1
    ((0.5, 1.5), (2, 3.5)),  # Winner (4/5) to Seed 1
    # Semifinal 2 → Championship
    ((2.5, 2.5), (4, 2)),    # Winner of semi 1 to final
    ((2.5, 1.0), (4, 2)),    # Winner of semi 2 to final
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

# Add team boxes / labels
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

# Layout tweaks
fig.update_layout(
    title="🏆 Playoff Bracket",
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
