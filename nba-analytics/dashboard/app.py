"""
NBA Analytics Dashboard built with Streamlit.
Displays real-time NBA statistics and standings.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import time
import os
import numpy as np

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="NBA Analytics Dashboard",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
<style>
    /* Hide Streamlit default header and menu */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Fixed header banner - NBA colors */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background: #17408B;
        padding: 0.75rem 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .header-container {
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        gap: 2rem;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .nba-logo {
        height: 45px;
        width: auto;
    }

    .header-title {
        font-size: 1.6rem;
        font-weight: bold;
        color: white;
        margin: 0;
        letter-spacing: 0.5px;
        white-space: nowrap;
    }

    /* Navigation tabs - now in header */
    .nav-tabs-container {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* Fixed bottom-right status widget */
    .status-widget {
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 998;
        background: rgba(23, 64, 139, 0.95);
        backdrop-filter: blur(10px);
        padding: 0.6rem 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border: 1px solid rgba(255,255,255,0.1);
    }

    .status-widget-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: white;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-healthy {
        background-color: #48bb78;
        box-shadow: 0 0 8px #48bb78;
        animation: pulse 2s ease-in-out infinite;
    }

    .status-error {
        background-color: #f56565;
        box-shadow: 0 0 8px #f56565;
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    .widget-divider {
        width: 1px;
        height: 20px;
        background: rgba(255,255,255,0.2);
    }

    /* Main content area with top margin for fixed header */
    .main .block-container {
        padding-top: 80px !important;
        max-width: 1400px;
        padding-bottom: 4rem !important;
    }

    /* Streamlit button styling overrides for tabs */
    div[data-testid="column"] button {
        width: 100%;
        border-radius: 0 !important;
        font-weight: 500;
        transition: all 0.2s ease;
        margin: 0 !important;
    }

    /* Style for nav tab buttons */
    .stButton button {
        background: rgba(255,255,255,0.05) !important;
        color: rgba(255,255,255,0.8) !important;
        font-size: 0.9rem !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        border-right: 1px solid rgba(255,255,255,0.15) !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 0 !important;
    }

    .stButton button:hover {
        background: rgba(255,255,255,0.12) !important;
        color: white !important;
        border-bottom: 3px solid rgba(255,255,255,0.4) !important;
    }

    .stButton button[kind="primary"] {
        background: rgba(255,255,255,0.18) !important;
        color: white !important;
        border-bottom: 3px solid white !important;
        font-weight: 600 !important;
    }

    .stButton button[kind="primary"]:hover {
        background: rgba(255,255,255,0.22) !important;
    }

    /* Remove border-radius from last tab */
    .stButton button:last-child {
        border-right: none !important;
    }

    /* Action buttons styling */
    .action-button button {
        background: rgba(255,255,255,0.15) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.9rem !important;
        font-size: 0.85rem !important;
    }

    .action-button button:hover {
        background: rgba(255,255,255,0.25) !important;
        border-color: rgba(255,255,255,0.5) !important;
    }

    /* Styling for content */
    .sub-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }

    .game-card {
        background: #f7fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4299e1;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .win {
        color: #38a169;
        font-weight: bold;
    }

    .loss {
        color: #e53e3e;
        font-weight: bold;
    }

    .stMetric {
        background-color: #f0f4f8;
        padding: 1rem;
        border-radius: 8px;
    }

    /* Action buttons in header */
    .header-buttons {
        display: flex;
        gap: 0.5rem;
        margin-left: 1rem;
    }

    .header-btn {
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }

    .header-btn:hover {
        background: rgba(255,255,255,0.3);
    }
</style>
""",
    unsafe_allow_html=True,
)


# API helper functions
def api_get(endpoint: str, params: dict = None):
    """Make GET request to API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None


def api_post(endpoint: str):
    """Make POST request to API."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None


# Caching decorators
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_standings():
    """Get current NBA standings."""
    return api_get("/api/standings")


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_todays_games():
    """Get today's games."""
    return api_get("/api/games/today")


@st.cache_data(ttl=300)
def get_teams():
    """Get all teams."""
    return api_get("/api/teams")


@st.cache_data(ttl=300)
def get_stat_leaders(stat: str, limit: int = 10):
    """Get statistical leaders."""
    return api_get("/api/stats/leaders", {"stat": stat, "limit": limit})


@st.cache_data(ttl=300)
def get_recent_games(
    days: int = 7, team_id: int = None, include_all_statuses: bool = False
):
    """Get recent games."""
    params = {"days": days, "include_all_statuses": include_all_statuses}
    if team_id:
        params["team_id"] = team_id
    return api_get("/api/games/recent", params)


@st.cache_data(ttl=600)
def get_player_stats(player_id: int):
    """Get player game stats."""
    return api_get(f"/api/stats/player/{player_id}")


@st.cache_data(ttl=300)
def get_predictions():
    """Get end-of-season predictions for all teams."""
    return api_get("/api/predictions")


@st.cache_data(ttl=3600)
def get_model_info():
    """Get active prediction model info."""
    return api_get("/api/predictions/model/info")


def check_api_health():
    """Check if API is healthy."""
    health = api_get("/health")
    return health and health.get("status") in ["healthy", "degraded"]


# Live game API functions
@st.cache_data(ttl=15)  # Cache for 15 seconds for live data
def get_live_games():
    """Get all live/today's games."""
    return api_get("/api/games/live")


@st.cache_data(ttl=15)
def get_live_game_data(game_id: str):
    """Get live data for a specific game."""
    return api_get(f"/api/games/{game_id}/live")


@st.cache_data(ttl=15)
def get_game_shots(game_id: str):
    """Get shot chart data for a game."""
    return api_get(f"/api/games/{game_id}/shots")


@st.cache_data(ttl=15)
def get_game_plays(game_id: str):
    """Get play-by-play data for a game."""
    return api_get(f"/api/games/{game_id}/plays")


def draw_nba_court(shots: list = None) -> go.Figure:
    """
    Draw an NBA half-court with shot locations using Plotly.
    Court dimensions are in 10ths of feet (NBA standard).
    """
    fig = go.Figure()

    # Court dimensions (in 10ths of feet)
    # Origin (0,0) is at the basket

    # Court outline (half court)
    court_shapes = [
        # Outer boundary
        dict(
            type="rect",
            x0=-250,
            y0=-50,
            x1=250,
            y1=420,
            line=dict(color="black", width=2),
            fillcolor="rgba(245, 222, 179, 0.3)",
        ),
        # Paint/Key (16 ft wide, 19 ft deep = 160 x 190)
        dict(
            type="rect",
            x0=-80,
            y0=-50,
            x1=80,
            y1=140,
            line=dict(color="black", width=2),
            fillcolor="rgba(0,0,0,0)",
        ),
        # Free throw circle (6 ft radius = 60)
        dict(
            type="circle",
            x0=-60,
            y0=80,
            x1=60,
            y1=200,
            line=dict(color="black", width=2),
            fillcolor="rgba(0,0,0,0)",
        ),
        # Backboard (6 ft wide = 60)
        dict(
            type="line",
            x0=-30,
            y0=-7.5,
            x1=30,
            y1=-7.5,
            line=dict(color="black", width=3),
        ),
        # Basket/Rim (9 inch radius = 7.5)
        dict(
            type="circle",
            x0=-7.5,
            y0=-7.5,
            x1=7.5,
            y1=7.5,
            line=dict(color="orange", width=3),
            fillcolor="rgba(0,0,0,0)",
        ),
        # Restricted area (4 ft radius = 40)
        dict(
            type="path",
            path="M -40 0 A 40 40 0 0 1 40 0",
            line=dict(color="black", width=2),
        ),
        # Three-point line corners (22 ft = 220)
        dict(
            type="line",
            x0=-220,
            y0=-50,
            x1=-220,
            y1=90,
            line=dict(color="black", width=2),
        ),
        dict(
            type="line",
            x0=220,
            y0=-50,
            x1=220,
            y1=90,
            line=dict(color="black", width=2),
        ),
    ]

    # Three-point arc (23.75 ft = 237.5 from basket)
    theta = np.linspace(np.arccos(220 / 237.5), np.pi - np.arccos(220 / 237.5), 100)
    arc_x = 237.5 * np.cos(theta)
    arc_y = 237.5 * np.sin(theta)

    fig.add_trace(
        go.Scatter(
            x=arc_x,
            y=arc_y,
            mode="lines",
            line=dict(color="black", width=2),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Add court shapes
    fig.update_layout(shapes=court_shapes)

    # Plot shots if provided
    if shots:
        made_shots = [s for s in shots if s.get("made")]
        missed_shots = [s for s in shots if not s.get("made")]

        # Made shots (green filled circles)
        if made_shots:
            fig.add_trace(
                go.Scatter(
                    x=[s["x"] for s in made_shots],
                    y=[s["y"] for s in made_shots],
                    mode="markers",
                    marker=dict(
                        size=12,
                        color="green",
                        symbol="circle",
                        line=dict(width=2, color="darkgreen"),
                    ),
                    name="Made",
                    text=[
                        f"{s.get('player_name', 'Unknown')} - {s.get('shot_type', '')} ({s.get('distance', 0)}ft)"
                        for s in made_shots
                    ],
                    hovertemplate="%{text}<extra></extra>",
                )
            )

        # Missed shots (red hollow circles)
        if missed_shots:
            fig.add_trace(
                go.Scatter(
                    x=[s["x"] for s in missed_shots],
                    y=[s["y"] for s in missed_shots],
                    mode="markers",
                    marker=dict(
                        size=12,
                        color="white",
                        symbol="circle",
                        line=dict(width=2, color="red"),
                    ),
                    name="Missed",
                    text=[
                        f"{s.get('player_name', 'Unknown')} - {s.get('shot_type', '')} ({s.get('distance', 0)}ft)"
                        for s in missed_shots
                    ],
                    hovertemplate="%{text}<extra></extra>",
                )
            )

    # Update layout
    fig.update_layout(
        xaxis=dict(
            range=[-275, 275],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True,
        ),
        yaxis=dict(
            range=[-75, 450],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            fixedrange=True,
        ),
        height=500,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def draw_3d_shot_chart(shots: list = None) -> go.Figure:
    """
    Draw a stunning 3D NBA half-court with shot arcs using Plotly.
    Features:
    - 3D court surface with NBA markings
    - Green parabolic arcs for made shots from shot location to basket
    - Player headshots and names on hover
    - Full width, no legend
    """

    fig = go.Figure()

    # Court dimensions (in 10ths of feet)
    # Scale factor to normalize the 3D view
    scale = 1.0

    # Draw the court floor as a surface
    court_x = np.array([-250, 250, 250, -250, -250]) * scale
    court_y = np.array([-50, -50, 420, 420, -50]) * scale
    court_z = np.zeros(5)

    # Court floor outline
    fig.add_trace(
        go.Scatter3d(
            x=court_x,
            y=court_y,
            z=court_z,
            mode="lines",
            line=dict(color="#1a365d", width=4),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Paint/Key outline
    paint_x = np.array([-80, 80, 80, -80, -80]) * scale
    paint_y = np.array([-50, -50, 140, 140, -50]) * scale
    paint_z = np.zeros(5)

    fig.add_trace(
        go.Scatter3d(
            x=paint_x,
            y=paint_y,
            z=paint_z,
            mode="lines",
            line=dict(color="#c53030", width=3),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Free throw circle
    theta_ft = np.linspace(0, 2 * np.pi, 50)
    ft_x = 60 * np.cos(theta_ft) * scale
    ft_y = (140 + 60 * np.sin(theta_ft)) * scale
    ft_z = np.zeros_like(theta_ft)

    fig.add_trace(
        go.Scatter3d(
            x=ft_x,
            y=ft_y,
            z=ft_z,
            mode="lines",
            line=dict(color="#c53030", width=2),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Three-point arc
    theta_3pt = np.linspace(np.arccos(220 / 237.5), np.pi - np.arccos(220 / 237.5), 100)
    arc3_x = 237.5 * np.cos(theta_3pt) * scale
    arc3_y = 237.5 * np.sin(theta_3pt) * scale
    arc3_z = np.zeros_like(theta_3pt)

    fig.add_trace(
        go.Scatter3d(
            x=arc3_x,
            y=arc3_y,
            z=arc3_z,
            mode="lines",
            line=dict(color="#1a365d", width=3),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Three-point corner lines
    fig.add_trace(
        go.Scatter3d(
            x=[-220 * scale, -220 * scale],
            y=[-50 * scale, 90 * scale],
            z=[0, 0],
            mode="lines",
            line=dict(color="#1a365d", width=3),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=[220 * scale, 220 * scale],
            y=[-50 * scale, 90 * scale],
            z=[0, 0],
            mode="lines",
            line=dict(color="#1a365d", width=3),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Basket/Rim (at z=10 for height)
    rim_theta = np.linspace(0, 2 * np.pi, 30)
    rim_x = 7.5 * np.cos(rim_theta) * scale
    rim_y = 7.5 * np.sin(rim_theta) * scale
    rim_z = np.ones_like(rim_theta) * 100  # Rim height (10 feet = 100 tenths)

    fig.add_trace(
        go.Scatter3d(
            x=rim_x,
            y=rim_y,
            z=rim_z,
            mode="lines",
            line=dict(color="#dd6b20", width=6),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Backboard
    fig.add_trace(
        go.Scatter3d(
            x=[-30 * scale, 30 * scale],
            y=[-7.5 * scale, -7.5 * scale],
            z=[80, 80],
            mode="lines",
            line=dict(color="white", width=8),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=[-30 * scale, 30 * scale],
            y=[-7.5 * scale, -7.5 * scale],
            z=[130, 130],
            mode="lines",
            line=dict(color="white", width=8),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=[-30 * scale, -30 * scale],
            y=[-7.5 * scale, -7.5 * scale],
            z=[80, 130],
            mode="lines",
            line=dict(color="white", width=8),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=[30 * scale, 30 * scale],
            y=[-7.5 * scale, -7.5 * scale],
            z=[80, 130],
            mode="lines",
            line=dict(color="white", width=8),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Plot shots if provided
    if shots:
        made_shots = [s for s in shots if s.get("made")]
        missed_shots = [s for s in shots if not s.get("made")]

        # Function to create parabolic arc from shot location to basket
        def create_shot_arc(shot_x, shot_y, distance):
            """Create a parabolic trajectory from shot location to basket."""
            t = np.linspace(0, 1, 30)

            # Start point (shot location)
            x0, y0 = shot_x * scale, shot_y * scale
            z0 = 80  # Release height (~8 feet)

            # End point (basket)
            x1, y1 = 0, 0
            z1 = 100  # Rim height

            # Arc height based on distance (higher arc for longer shots)
            arc_height = max(150, 100 + distance * 3)

            # Parametric parabola
            arc_x = x0 + (x1 - x0) * t
            arc_y = y0 + (y1 - y0) * t
            # Parabolic z with peak in the middle
            arc_z = z0 + (z1 - z0) * t + 4 * (arc_height - max(z0, z1)) * t * (1 - t)

            return arc_x, arc_y, arc_z

        # Draw arcs for made shots (green)
        for shot in made_shots:
            arc_x, arc_y, arc_z = create_shot_arc(
                shot["x"], shot["y"], shot.get("distance", 15)
            )
            fig.add_trace(
                go.Scatter3d(
                    x=arc_x,
                    y=arc_y,
                    z=arc_z,
                    mode="lines",
                    line=dict(color="#38a169", width=4),
                    showlegend=False,
                    hoverinfo="skip",
                    opacity=0.7,
                )
            )

        # Made shots as points at shot location with player info on hover
        if made_shots:
            # Create hover text (clean, without HTML images - those don't render in Plotly 3D)
            hover_texts = []
            custom_data = []
            for s in made_shots:
                player_name = s.get("player_name", "Unknown")
                player_id = s.get("player_id", 0)
                shot_type = s.get("shot_type", "")
                distance = s.get("distance", 0)
                team = s.get("team_abbr", "")

                hover_texts.append(
                    f"<b style='font-size:14px'>{player_name}</b><br>"
                    f"<span style='color:#48bb78'>MADE</span><br>"
                    f"{team} | {shot_type} | {distance}ft"
                )
                custom_data.append([player_id, player_name, team])

            fig.add_trace(
                go.Scatter3d(
                    x=[s["x"] * scale for s in made_shots],
                    y=[s["y"] * scale for s in made_shots],
                    z=[80 for _ in made_shots],  # Release height
                    mode="markers",
                    marker=dict(
                        size=10,
                        color="#38a169",
                        symbol="circle",
                        line=dict(width=2, color="#276749"),
                        opacity=0.9,
                    ),
                    text=hover_texts,
                    customdata=custom_data,
                    hovertemplate="%{text}<extra></extra>",
                    showlegend=False,
                )
            )

        # Missed shots as X markers (no arcs)
        if missed_shots:
            hover_texts_missed = []
            custom_data_missed = []
            for s in missed_shots:
                player_name = s.get("player_name", "Unknown")
                player_id = s.get("player_id", 0)
                shot_type = s.get("shot_type", "")
                distance = s.get("distance", 0)
                team = s.get("team_abbr", "")

                hover_texts_missed.append(
                    f"<b style='font-size:14px'>{player_name}</b><br>"
                    f"<span style='color:#e53e3e'>MISSED</span><br>"
                    f"{team} | {shot_type} | {distance}ft"
                )
                custom_data_missed.append([player_id, player_name, team])

            fig.add_trace(
                go.Scatter3d(
                    x=[s["x"] * scale for s in missed_shots],
                    y=[s["y"] * scale for s in missed_shots],
                    z=[80 for _ in missed_shots],
                    mode="markers",
                    marker=dict(
                        size=8,
                        color="#e53e3e",
                        symbol="x",
                        line=dict(width=2, color="#c53030"),
                        opacity=0.7,
                    ),
                    text=hover_texts_missed,
                    customdata=custom_data_missed,
                    hovertemplate="%{text}<extra></extra>",
                    showlegend=False,
                )
            )

    # Update layout for 3D view
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                range=[-300, 300],
                showgrid=False,
                showbackground=True,
                backgroundcolor="#e8dcc4",  # Court wood color
                showticklabels=False,
                title="",
                showspikes=False,
            ),
            yaxis=dict(
                range=[-100, 450],
                showgrid=False,
                showbackground=True,
                backgroundcolor="#e8dcc4",
                showticklabels=False,
                title="",
                showspikes=False,
            ),
            zaxis=dict(
                range=[0, 250],
                showgrid=False,
                showbackground=False,
                showticklabels=False,
                title="",
                showspikes=False,
            ),
            camera=dict(
                eye=dict(x=0, y=-1.8, z=0.8),
                center=dict(x=0, y=0.1, z=-0.1),
                up=dict(x=0, y=0, z=1),
            ),
            aspectmode="manual",
            aspectratio=dict(x=1.2, y=1, z=0.5),
        ),
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor="rgba(20, 20, 30, 1)",
    )

    return fig


def render_play_feed(plays: list, limit: int = 20):
    """Render the play-by-play feed with icons."""
    if not plays:
        st.info("No plays to display yet.")
        return

    # Event type icons
    icons = {
        "SHOT_MADE": "🏀",
        "SHOT_MISSED": "❌",
        "FREE_THROW": "🎱",
        "REBOUND": "🔄",
        "TURNOVER": "💨",
        "FOUL": "📍",
        "VIOLATION": "🚫",
        "SUBSTITUTION": "🔀",
        "TIMEOUT": "⏸️",
        "JUMP_BALL": "⬆️",
        "PERIOD_BEGIN": "▶️",
        "PERIOD_END": "⏹️",
        "OTHER": "📋",
    }

    # Reverse to show most recent first
    recent_plays = list(reversed(plays[-limit:]))

    st.markdown("### Play-by-Play")
    for play in recent_plays:
        event_type = play.get("event_type", "OTHER")
        icon = icons.get(event_type, "📋")
        period = play.get("period", 0)
        clock = play.get("clock", "")
        description = play.get("description", "")
        team = play.get("team_abbr", "")
        score = f"{play.get('away_score', 0)} - {play.get('home_score', 0)}"

        # Color based on event type
        if event_type in ["SHOT_MADE", "FREE_THROW"]:
            color = "#38a169"
        elif event_type == "SHOT_MISSED":
            color = "#e53e3e"
        else:
            color = "#4a5568"

        st.markdown(
            f"""<div style="padding: 8px; margin: 4px 0; border-left: 3px solid {color}; background: #f7fafc; border-radius: 4px; color: #1a202c;">
                <span style="font-size: 1.2em;">{icon}</span>
                <strong style="color: #2d3748;">Q{period} {clock}</strong> <span style="color: #4a5568;">[{team}]</span> <span style="color: #1a202c;">{description}</span>
                <span style="float: right; color: #718096;">{score}</span>
            </div>""",
            unsafe_allow_html=True,
        )


def render_shot_heatmap(shots: list) -> go.Figure:
    """Render a shot heat map on the court."""
    if not shots:
        return draw_nba_court([])

    fig = draw_nba_court([])

    # Add density contour for shots
    x_coords = [s["x"] for s in shots]
    y_coords = [s["y"] for s in shots]

    fig.add_trace(
        go.Histogram2dContour(
            x=x_coords,
            y=y_coords,
            colorscale="Hot",
            reversescale=True,
            showscale=False,
            contours=dict(showlabels=False, coloring="heatmap"),
            opacity=0.6,
            name="Shot Density",
        )
    )

    return fig


def render_live_game():
    """Render the live game visualization page."""
    st.markdown('<h2 class="sub-header">Live Game</h2>', unsafe_allow_html=True)

    # Fetch live games
    live_games = get_live_games()

    if not live_games:
        st.info("No games currently in progress or scheduled for today.")
        st.markdown("### Check back later for live game updates!")
        return

    # Filter to only live games or show all scheduled
    active_games = [g for g in live_games if g.get("is_live")]

    if active_games:
        st.success(f"🔴 {len(active_games)} game(s) currently LIVE!")
        games_to_show = active_games
    else:
        st.info("No games currently in progress. Showing today's scheduled games.")
        games_to_show = live_games

    # Game selector
    game_options = {
        f"{g['away_team_abbr']} @ {g['home_team_abbr']} - {g['status']}": g["game_id"]
        for g in games_to_show
    }

    if not game_options:
        st.warning("No games available.")
        return

    selected_label = st.selectbox("Select Game", options=list(game_options.keys()))
    selected_game_id = game_options[selected_label]

    # Find selected game info
    selected_game = next(
        (g for g in games_to_show if g["game_id"] == selected_game_id), None
    )

    if selected_game:
        # Game header
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.markdown(f"### {selected_game['away_team_name']}")
            st.markdown(f"## {selected_game['away_score']}")
        with col2:
            st.markdown("### VS")
            if selected_game.get("is_live"):
                st.markdown(
                    f"**Q{selected_game.get('period', 0)}** {selected_game.get('game_clock', '')}"
                )
            else:
                st.markdown(f"**{selected_game['status']}**")
        with col3:
            st.markdown(f"### {selected_game['home_team_name']}")
            st.markdown(f"## {selected_game['home_score']}")

    st.markdown("---")

    # Auto-refresh option
    auto_refresh = st.checkbox(
        "Auto-refresh (15s)",
        value=selected_game.get("is_live", False) if selected_game else False,
    )
    if auto_refresh:
        # Using streamlit-autorefresh would be ideal, but we can use st.rerun with a placeholder
        st.caption("Auto-refreshing every 15 seconds...")

    # Get shot data for this game
    shots = get_game_shots(selected_game_id)
    plays = get_game_plays(selected_game_id)

    # Extract team info from shots for filtering
    if shots and selected_game:
        away_team = selected_game.get("away_team_abbr", "AWAY")
        home_team = selected_game.get("home_team_abbr", "HOME")
        away_team_id = selected_game.get("away_team_id", 0)
        home_team_id = selected_game.get("home_team_id", 0)

        # Get unique players from shots
        players_in_game = {}
        for s in shots:
            pid = s.get("player_id", 0)
            pname = s.get("player_name", "Unknown")
            pteam = s.get("team_abbr", "")
            if pid and pname not in players_in_game:
                players_in_game[pname] = {"id": pid, "team": pteam}
    else:
        away_team = "AWAY"
        home_team = "HOME"
        away_team_id = 0
        home_team_id = 0
        players_in_game = {}

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Shot Chart", "Play-by-Play", "Heat Map", "Box Score"]
    )

    with tab1:
        st.markdown("### 3D Shot Chart")

        if shots:
            # Team and Player filtering controls
            filter_col1, filter_col2, filter_col3 = st.columns([1, 2, 1])

            with filter_col1:
                # Away team logo and filter button
                st.image(
                    f"https://cdn.nba.com/logos/nba/{away_team_id}/global/L/logo.svg",
                    width=80,
                )
                away_filter = st.checkbox(f"{away_team}", value=True, key="away_filter")

            with filter_col2:
                # Player filter dropdown
                player_options = ["All Players"] + sorted(players_in_game.keys())
                selected_player = st.selectbox(
                    "Filter by Player", options=player_options, key="player_filter"
                )

            with filter_col3:
                # Home team logo and filter button
                st.image(
                    f"https://cdn.nba.com/logos/nba/{home_team_id}/global/L/logo.svg",
                    width=80,
                )
                home_filter = st.checkbox(f"{home_team}", value=True, key="home_filter")

            # Filter shots based on selections
            filtered_shots = shots.copy()

            # Team filter
            if not away_filter:
                filtered_shots = [
                    s for s in filtered_shots if s.get("team_abbr") != away_team
                ]
            if not home_filter:
                filtered_shots = [
                    s for s in filtered_shots if s.get("team_abbr") != home_team
                ]

            # Player filter
            if selected_player != "All Players":
                filtered_shots = [
                    s for s in filtered_shots if s.get("player_name") == selected_player
                ]

            # Display player headshot panel if a player is selected
            if selected_player != "All Players" and selected_player in players_in_game:
                player_info = players_in_game[selected_player]
                headshot_col1, headshot_col2 = st.columns([1, 3])
                with headshot_col1:
                    st.image(
                        f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_info['id']}.png",
                        width=130,
                    )
                with headshot_col2:
                    player_shots = [
                        s for s in shots if s.get("player_name") == selected_player
                    ]
                    made = len([s for s in player_shots if s.get("made")])
                    missed = len([s for s in player_shots if not s.get("made")])
                    fg_pct = (made / len(player_shots) * 100) if player_shots else 0

                    st.markdown(f"### {selected_player}")
                    st.markdown(f"**Team:** {player_info['team']}")
                    st.markdown(f"**FG:** {made}/{len(player_shots)} ({fg_pct:.1f}%)")

            st.caption("Rotate and zoom the 3D court. Green arcs show made shots.")

            # Display the 3D chart
            st.plotly_chart(
                draw_3d_shot_chart(filtered_shots), use_container_width=True
            )

            # Stats summary
            made_count = len([s for s in filtered_shots if s.get("made")])
            missed_count = len([s for s in filtered_shots if not s.get("made")])
            st.markdown(
                f"**{len(filtered_shots)} shots shown** | 🟢 Made: {made_count} | ❌ Missed: {missed_count}"
            )
        else:
            st.info("No shot data available for this game yet.")
            st.plotly_chart(draw_3d_shot_chart([]), use_container_width=True)

    with tab2:
        render_play_feed(plays or [])

    with tab3:
        st.markdown("### Shot Heat Map")
        if shots:
            # Team filter for heatmap
            hm_col1, hm_col2, hm_col3 = st.columns([1, 2, 1])
            with hm_col1:
                st.image(
                    f"https://cdn.nba.com/logos/nba/{away_team_id}/global/L/logo.svg",
                    width=60,
                )
                hm_away = st.checkbox(f"{away_team}", value=True, key="hm_away")
            with hm_col2:
                st.markdown("#### Filter by Team")
            with hm_col3:
                st.image(
                    f"https://cdn.nba.com/logos/nba/{home_team_id}/global/L/logo.svg",
                    width=60,
                )
                hm_home = st.checkbox(f"{home_team}", value=True, key="hm_home")

            # Filter shots for heatmap
            hm_shots = shots.copy()
            if not hm_away:
                hm_shots = [s for s in hm_shots if s.get("team_abbr") != away_team]
            if not hm_home:
                hm_shots = [s for s in hm_shots if s.get("team_abbr") != home_team]

            # Larger heatmap
            heatmap_fig = render_shot_heatmap(hm_shots)
            heatmap_fig.update_layout(height=600)
            st.plotly_chart(heatmap_fig, use_container_width=True)
            st.caption(
                f"Showing {len(hm_shots)} shots | Hot zones indicate high shot frequency"
            )
        else:
            st.info("No shot data available for heat map.")

    with tab4:
        st.markdown("### Box Score")
        game_data = get_live_game_data(selected_game_id)
        if game_data and game_data.get("box_score"):
            box_score = game_data["box_score"]
            player_stats = box_score.get("player_stats", [])

            if player_stats:
                # Split by team
                teams = set(p["team_abbr"] for p in player_stats)

                for team in sorted(teams):
                    st.markdown(f"#### {team}")
                    team_players = [p for p in player_stats if p["team_abbr"] == team]

                    df = pd.DataFrame(
                        [
                            {
                                "Player": p["player_name"],
                                "MIN": p.get("minutes", "0"),
                                "PTS": p.get("points", 0),
                                "REB": p.get("rebounds", 0),
                                "AST": p.get("assists", 0),
                                "STL": p.get("steals", 0),
                                "BLK": p.get("blocks", 0),
                                "FG": f"{p.get('fg_made', 0)}/{p.get('fg_attempted', 0)}",
                                "3P": f"{p.get('three_made', 0)}/{p.get('three_attempted', 0)}",
                                "+/-": p.get("plus_minus", 0),
                            }
                            for p in team_players
                        ]
                    )

                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Box score not available yet.")
        else:
            st.info("Box score data not available.")


# Dashboard components
def render_header():
    """Render the main header."""
    st.markdown(
        '<h1 class="main-header">🏀 NBA Analytics Dashboard</h1>',
        unsafe_allow_html=True,
    )

    # Check API health
    if check_api_health():
        st.success("✅ Connected to API")
    else:
        st.error("❌ API connection failed. Make sure the backend is running.")
        st.stop()


def render_sidebar():
    """Render the sidebar with navigation and controls."""
    with st.sidebar:
        st.image("https://cdn.nba.com/logos/leagues/logo-nba.svg", width=100)
        st.markdown("## Navigation")

        page = st.radio(
            "Select Page",
            [
                "📊 Standings",
                "🎮 Today's Games",
                "🏆 Leaders",
                "📈 Team Analysis",
                "🔮 Predictions",
                "🏀 Live Game",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        st.markdown("## Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", help="Refresh data from API"):
                st.cache_data.clear()
                st.rerun()

        with col2:
            if st.button("📥 Sync", help="Trigger data sync"):
                result = api_post("/api/refresh/full")
                if result:
                    st.success("Sync started!")

        st.markdown("---")
        st.markdown("### About")
        st.info(
            "Real-time NBA analytics dashboard featuring "
            "standings, game scores, and player statistics."
        )

        return page


def render_standings():
    """Render the standings page."""
    st.markdown(
        '<h2 class="sub-header">Conference Standings</h2>', unsafe_allow_html=True
    )

    standings = get_standings()

    if not standings:
        st.warning(
            "No standings data available. Try refreshing or syncing data.", icon="⚠️"
        )
        return

    # Display last updated
    updated = standings.get("updated_at", "Unknown")
    st.caption(f"Last updated: {updated}")

    # Create two columns for East and West
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔵 Eastern Conference")
        if standings.get("east"):
            east_df = pd.DataFrame(
                [
                    {
                        "Rank": s.get("conf_rank", "-"),
                        "Team": f"{s['team_abbr']}",
                        "W": s["wins"],
                        "L": s["losses"],
                        "PCT": f"{s['win_pct']:.3f}",
                        "GB": s["games_back"],
                        "Streak": s.get("streak", "-"),
                        "L10": s.get("last_10", "-"),
                    }
                    for s in standings["east"]
                ]
            )
            st.dataframe(
                east_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Team": st.column_config.TextColumn("Team", width="small"),
                    "W": st.column_config.NumberColumn("W", width="small"),
                    "L": st.column_config.NumberColumn("L", width="small"),
                    "PCT": st.column_config.TextColumn("PCT", width="small"),
                    "GB": st.column_config.NumberColumn("GB", width="small"),
                    "Streak": st.column_config.TextColumn("Streak", width="small"),
                    "L10": st.column_config.TextColumn("L10", width="small"),
                },
            )
        else:
            st.info("No Eastern Conference standings available")

    with col2:
        st.markdown("### 🔴 Western Conference")
        if standings.get("west"):
            west_df = pd.DataFrame(
                [
                    {
                        "Rank": s.get("conf_rank", "-"),
                        "Team": f"{s['team_abbr']}",
                        "W": s["wins"],
                        "L": s["losses"],
                        "PCT": f"{s['win_pct']:.3f}",
                        "GB": s["games_back"],
                        "Streak": s.get("streak", "-"),
                        "L10": s.get("last_10", "-"),
                    }
                    for s in standings["west"]
                ]
            )
            st.dataframe(
                west_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Team": st.column_config.TextColumn("Team", width="small"),
                    "W": st.column_config.NumberColumn("W", width="small"),
                    "L": st.column_config.NumberColumn("L", width="small"),
                    "PCT": st.column_config.TextColumn("PCT", width="small"),
                    "GB": st.column_config.NumberColumn("GB", width="small"),
                    "Streak": st.column_config.TextColumn("Streak", width="small"),
                    "L10": st.column_config.TextColumn("L10", width="small"),
                },
            )
        else:
            st.info("No Western Conference standings available")

    # Visualization: Win percentage comparison
    st.markdown("### Win Percentage by Team")

    all_standings = standings.get("east", []) + standings.get("west", [])
    if all_standings:
        viz_df = pd.DataFrame(
            [
                {
                    "Team": s["team_abbr"],
                    "Win %": s["win_pct"] * 100,
                    "Conference": s["conference"],
                }
                for s in all_standings
            ]
        ).sort_values("Win %", ascending=True)

        fig = px.bar(
            viz_df,
            x="Win %",
            y="Team",
            color="Conference",
            orientation="h",
            color_discrete_map={"East": "#1f77b4", "West": "#d62728"},
            title="Win Percentage by Team",
        )
        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)


def render_todays_games():
    """Render today's games page."""
    st.markdown('<h2 class="sub-header">Today\'s Games</h2>', unsafe_allow_html=True)
    st.caption(f"Date: {date.today().strftime('%B %d, %Y')}")

    games = get_todays_games()

    if not games:
        st.info("No games scheduled for today. Showing recent games instead.")
        st.markdown("### Recent Completed Games")
        recent = get_recent_games(days=7)
        if not recent:
            st.warning("No recent games available.")
            return
        games = recent[:12]  # Show up to 12 recent games

    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (every 30 seconds)", value=False)

    if auto_refresh:
        time.sleep(30)
        st.cache_data.clear()
        st.rerun()

    # Display games in a 3-column grid
    for row_start in range(0, len(games), 3):
        cols = st.columns(3)
        for i, col in enumerate(cols):
            game_idx = row_start + i
            if game_idx >= len(games):
                break

            game = games[game_idx]
            status = game.get("status", "unknown")
            status_emoji = (
                "🔴" if status == "live" else ("✅" if status == "final" else "⏰")
            )

            home = game.get("home_team", {})
            away = game.get("away_team", {})

            with col:
                # Use a container for the card styling
                with st.container():
                    # Status header
                    status_text = f"{status_emoji} **{status.upper()}**"
                    if status == "live":
                        status_text += (
                            f" - Q{game.get('period', '')} {game.get('clock', '')}"
                        )
                    st.markdown(status_text)

                    # Game matchup using columns
                    c1, c2, c3 = st.columns([2, 1, 2])
                    with c1:
                        st.markdown(f"**{away.get('abbr', 'TBD')}**")
                        st.markdown(f"### {away.get('score', '-')}")
                    with c2:
                        st.markdown("@")
                    with c3:
                        st.markdown(f"**{home.get('abbr', 'TBD')}**")
                        st.markdown(f"### {home.get('score', '-')}")

                    st.divider()


def render_leaders():
    """Render the statistical leaders page."""
    st.markdown(
        '<h2 class="sub-header">Statistical Leaders</h2>', unsafe_allow_html=True
    )

    # Stat category selector
    col1, col2 = st.columns([1, 3])
    with col1:
        stat_category = st.selectbox(
            "Category",
            ["points", "rebounds", "assists", "steals", "blocks"],
            format_func=lambda x: x.title(),
        )

    with col2:
        num_leaders = st.slider("Number of leaders", 5, 25, 10)

    # Get leaders
    leaders = get_stat_leaders(stat_category, num_leaders)

    if not leaders:
        st.warning("No statistical data available.", icon="⚠️")
        return

    # Create DataFrame
    df = pd.DataFrame(leaders)

    # Rename columns for display
    display_df = df.rename(
        columns={
            "player_name": "Player",
            "team_abbr": "Team",
            "minutes": "MPG",
            "points": "PPG",
            "rebounds": "RPG",
            "assists": "APG",
            "steals": "SPG",
            "blocks": "BPG",
            "turnovers": "TOV",
            "fg_pct": "FG%",
            "three_pct": "3P%",
            "ft_pct": "FT%",
            "plus_minus": "+/-",
        }
    )

    # Select columns based on category
    base_cols = ["Player", "Team", "MPG"]
    stat_cols = {
        "points": ["PPG", "FG%", "3P%", "FT%"],
        "rebounds": ["RPG", "PPG"],
        "assists": ["APG", "PPG", "TOV"],
        "steals": ["SPG", "PPG"],
        "blocks": ["BPG", "PPG"],
    }
    cols_to_show = base_cols + stat_cols[stat_category]

    # Display table
    st.dataframe(display_df[cols_to_show], use_container_width=True, hide_index=True)

    # Visualization
    st.markdown(f"### Top {num_leaders} in {stat_category.title()}")

    stat_map = {
        "points": "PPG",
        "rebounds": "RPG",
        "assists": "APG",
        "steals": "SPG",
        "blocks": "BPG",
    }

    fig = px.bar(
        display_df.head(num_leaders),
        x="Player",
        y=stat_map[stat_category],
        color="Team",
        title=f"{stat_category.title()} Leaders",
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def render_team_analysis():
    """Render team analysis page."""
    st.markdown('<h2 class="sub-header">Team Analysis</h2>', unsafe_allow_html=True)

    # Get teams
    teams = get_teams()

    if not teams:
        st.warning("No team data available.", icon="⚠️")
        return

    # Team selector
    team_options = {f"{t['abbreviation']} - {t['name']}": t["id"] for t in teams}
    selected_team = st.selectbox("Select Team", options=list(team_options.keys()))
    team_id = team_options[selected_team]

    # Get team's recent games (include all statuses for current season)
    recent_games = get_recent_games(days=30, team_id=team_id, include_all_statuses=True)

    if recent_games:
        st.markdown("### Recent Games")

        # Create games DataFrame
        games_data = []
        for game in recent_games:
            home = game["home_team"]
            away = game["away_team"]

            is_home = home["id"] == team_id
            team_score = home["score"] if is_home else away["score"]
            opp_score = away["score"] if is_home else home["score"]
            opponent = away["abbr"] if is_home else home["abbr"]
            result = "W" if team_score > opp_score else "L"

            games_data.append(
                {
                    "Date": game.get("game_date", ""),
                    "Opponent": f"{'vs' if is_home else '@'} {opponent}",
                    "Result": result,
                    "Score": f"{team_score}-{opp_score}",
                    "Margin": team_score - opp_score,
                }
            )

        games_df = pd.DataFrame(games_data)

        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        wins = len([g for g in games_data if g["Result"] == "W"])
        losses = len([g for g in games_data if g["Result"] == "L"])

        with col1:
            st.metric("Record (Last 30 days)", f"{wins}-{losses}")
        with col2:
            st.metric(
                "Win %",
                f"{wins/(wins+losses)*100:.1f}%" if wins + losses > 0 else "N/A",
            )
        with col3:
            avg_margin = (
                sum(g["Margin"] for g in games_data) / len(games_data)
                if games_data
                else 0
            )
            st.metric("Avg Margin", f"{avg_margin:+.1f}")
        with col4:
            st.metric("Games Played", len(games_data))

        # Display games table
        st.dataframe(
            games_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Result": st.column_config.TextColumn(
                    "Result",
                    width="small",
                )
            },
        )

        # Margin chart
        if len(games_df) > 1:
            st.markdown("### Point Differential Trend")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(games_df))),
                    y=games_df["Margin"],
                    mode="lines+markers",
                    name="Margin",
                    line=dict(color="#4299e1"),
                    marker=dict(
                        color=["green" if m > 0 else "red" for m in games_df["Margin"]],
                        size=10,
                    ),
                )
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_layout(
                xaxis_title="Game", yaxis_title="Point Margin", showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recent games found for this team.")


def render_predictions():
    """Render the predictions page with LSTM forecasts."""
    st.markdown(
        '<h2 class="sub-header">End-of-Season Predictions</h2>', unsafe_allow_html=True
    )

    predictions = get_predictions()

    if not predictions:
        st.warning(
            "No predictions available. The LSTM model may need to be trained first. "
            "Use the Admin API to trigger model training."
        )
        return

    # Model info expander
    model_info = get_model_info()
    if model_info:
        with st.expander("Model Information"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Model Version", model_info.get("model_version", "N/A"))
            with col2:
                mae = model_info.get("mae_wins")
                st.metric("Wins MAE", f"{mae:.2f}" if mae else "N/A")
            with col3:
                st.metric(
                    "Training Seasons", len(model_info.get("training_seasons", []))
                )

    st.caption(
        f"Predictions generated: {predictions.get('prediction_date', 'Unknown')}"
    )

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(
        ["Conference Rankings", "Playoff Probabilities", "Statistical Forecasts"]
    )

    with tab1:
        render_predicted_rankings(predictions)

    with tab2:
        render_playoff_probabilities(predictions)

    with tab3:
        render_stat_forecasts(predictions)


def render_predicted_rankings(predictions: dict):
    """Display predicted conference rankings."""
    standings = get_standings()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Eastern Conference")
        if predictions.get("east"):
            # Get actual standings for comparison
            actual_east = (
                {s["team_abbr"]: s for s in standings.get("east", [])}
                if standings
                else {}
            )

            east_data = []
            for p in predictions["east"]:
                actual = actual_east.get(p["team_abbr"], {})
                east_data.append(
                    {
                        "Rank": p.get("predicted_conference_rank", "-"),
                        "Team": p["team_abbr"],
                        "Pred W": round(p["predicted_wins"]),
                        "Pred L": round(p["predicted_losses"]),
                        "Actual W": actual.get("wins", "-"),
                        "Playoff %": f"{p['playoff_probability'] * 100:.0f}%",
                    }
                )

            st.dataframe(
                pd.DataFrame(east_data),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No Eastern Conference predictions")

    with col2:
        st.markdown("### Western Conference")
        if predictions.get("west"):
            actual_west = (
                {s["team_abbr"]: s for s in standings.get("west", [])}
                if standings
                else {}
            )

            west_data = []
            for p in predictions["west"]:
                actual = actual_west.get(p["team_abbr"], {})
                west_data.append(
                    {
                        "Rank": p.get("predicted_conference_rank", "-"),
                        "Team": p["team_abbr"],
                        "Pred W": round(p["predicted_wins"]),
                        "Pred L": round(p["predicted_losses"]),
                        "Actual W": actual.get("wins", "-"),
                        "Playoff %": f"{p['playoff_probability'] * 100:.0f}%",
                    }
                )

            st.dataframe(
                pd.DataFrame(west_data),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No Western Conference predictions")

    # Predicted vs Actual Wins Chart
    st.markdown("### Predicted vs Current Wins")
    all_predictions = predictions.get("east", []) + predictions.get("west", [])

    if all_predictions and standings:
        all_standings = standings.get("east", []) + standings.get("west", [])
        standings_map = {s["team_abbr"]: s["wins"] for s in all_standings}

        fig = go.Figure()

        teams = [p["team_abbr"] for p in all_predictions]
        pred_wins = [p["predicted_wins"] for p in all_predictions]
        actual_wins = [standings_map.get(t, 0) for t in teams]

        fig.add_trace(
            go.Bar(name="Predicted Wins", x=teams, y=pred_wins, marker_color="#667eea")
        )

        fig.add_trace(
            go.Bar(name="Current Wins", x=teams, y=actual_wins, marker_color="#48bb78")
        )

        fig.update_layout(
            barmode="group",
            xaxis_tickangle=-45,
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)


def render_playoff_probabilities(predictions: dict):
    """Display playoff probability visualizations."""
    st.markdown("### Playoff Qualification Probabilities")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Eastern Conference")
        east = sorted(
            predictions.get("east", []),
            key=lambda x: x.get("playoff_probability", 0),
            reverse=True,
        )

        if east:
            fig = px.bar(
                x=[t["team_abbr"] for t in east],
                y=[t["playoff_probability"] * 100 for t in east],
                color=[t["playoff_probability"] for t in east],
                color_continuous_scale="RdYlGn",
                labels={"x": "Team", "y": "Probability (%)"},
            )
            fig.update_layout(showlegend=False, height=400, coloraxis_showscale=False)
            fig.add_hline(
                y=50,
                line_dash="dash",
                line_color="gray",
                annotation_text="50%",
                annotation_position="right",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Western Conference")
        west = sorted(
            predictions.get("west", []),
            key=lambda x: x.get("playoff_probability", 0),
            reverse=True,
        )

        if west:
            fig = px.bar(
                x=[t["team_abbr"] for t in west],
                y=[t["playoff_probability"] * 100 for t in west],
                color=[t["playoff_probability"] for t in west],
                color_continuous_scale="RdYlGn",
                labels={"x": "Team", "y": "Probability (%)"},
            )
            fig.update_layout(showlegend=False, height=400, coloraxis_showscale=False)
            fig.add_hline(
                y=50,
                line_dash="dash",
                line_color="gray",
                annotation_text="50%",
                annotation_position="right",
            )
            st.plotly_chart(fig, use_container_width=True)


def render_stat_forecasts(predictions: dict):
    """Display predicted statistical metrics for teams."""
    st.markdown("### Predicted Season Statistics")

    all_teams = predictions.get("east", []) + predictions.get("west", [])
    team_options = {f"{t['team_abbr']} - {t['team_name']}": t for t in all_teams}

    if not team_options:
        st.info("No team predictions available")
        return

    selected = st.selectbox("Select Team", options=list(team_options.keys()))
    team = team_options[selected]

    # Display predicted stats in metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Predicted Wins", f"{team['predicted_wins']:.0f}")
        st.metric("Win %", f"{team['predicted_win_pct']:.1%}")

    with col2:
        st.metric("Predicted PPG", f"{team['predicted_ppg']:.1f}")
        st.metric("Predicted OPPG", f"{team['predicted_oppg']:.1f}")

    with col3:
        st.metric("Predicted Pace", f"{team['predicted_pace']:.1f}")
        st.metric("Def Rating", f"{team['predicted_defensive_rating']:.1f}")

    with col4:
        st.metric("Conf Rank", f"#{team['predicted_conference_rank']}")
        prob_pct = team["playoff_probability"] * 100
        st.metric("Playoff Prob", f"{prob_pct:.0f}%")

    # Offensive vs Defensive scatter plot
    st.markdown("### Team Efficiency: Offense vs Defense")

    fig = px.scatter(
        x=[t["predicted_ppg"] for t in all_teams],
        y=[t["predicted_oppg"] for t in all_teams],
        text=[t["team_abbr"] for t in all_teams],
        color=[t["playoff_probability"] for t in all_teams],
        color_continuous_scale="RdYlGn",
        labels={
            "x": "Predicted PPG (Offense)",
            "y": "Predicted OPPG (Defense)",
            "color": "Playoff Prob",
        },
    )
    fig.update_traces(textposition="top center", marker_size=12)
    fig.update_layout(height=500)

    # Add quadrant lines at averages
    if all_teams:
        avg_ppg = sum(t["predicted_ppg"] for t in all_teams) / len(all_teams)
        avg_oppg = sum(t["predicted_oppg"] for t in all_teams) / len(all_teams)
        fig.add_hline(y=avg_oppg, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=avg_ppg, line_dash="dash", line_color="gray", opacity=0.5)

    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Teams in upper-right (high PPG, low OPPG) are predicted to be most successful."
    )


# Main application
def main():
    """Main application entry point."""
    render_header()
    page = render_sidebar()

    if page == "📊 Standings":
        render_standings()
    elif st.session_state.current_page == "Today's Games":
        render_todays_games()
    elif st.session_state.current_page == "Leaders":
        render_leaders()
    elif st.session_state.current_page == "Team Analysis":
        render_team_analysis()
    elif page == "🔮 Predictions":
        render_predictions()
    elif page == "🏀 Live Game":
        render_live_game()


if __name__ == "__main__":
    main()
