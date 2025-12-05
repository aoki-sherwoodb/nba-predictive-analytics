"""
NBA Analytics Dashboard built with Streamlit.
Displays real-time NBA statistics and standings with modern UI.
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
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern styling - NBA themed
st.markdown("""
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
        background: linear-gradient(135deg, #17408B 0%, #1d3557 100%);
        padding: 0.75rem 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
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
        padding-top: 100px !important;
        max-width: 1400px;
        padding-bottom: 4rem !important;
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
        border-bottom: 3px solid #C9082A !important;
        font-weight: 600 !important;
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

    /* Live indicator pulse */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #C9082A;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .live-dot {
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        animation: livePulse 1.5s ease-in-out infinite;
    }

    @keyframes livePulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }

    /* Card styling for games */
    .game-card-modern {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .game-card-modern:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


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
@st.cache_data(ttl=300)
def get_standings():
    """Get current NBA standings."""
    return api_get("/api/standings")


@st.cache_data(ttl=60)
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
def get_recent_games(days: int = 7, team_id: int = None):
    """Get recent games."""
    params = {"days": days}
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
    try:
        health = api_get("/health")
        return health and health.get("status") in ["healthy", "degraded"]
    except:
        return False


# Live game API functions
@st.cache_data(ttl=15)
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


@st.cache_data(ttl=300)
def search_players(query: str, limit: int = 10):
    """Search for players by name."""
    return api_get("/api/players/search", {"q": query, "limit": limit})


@st.cache_data(ttl=300)
def compare_players(player1_id: int, player2_id: int):
    """Compare two players."""
    return api_get("/api/players/compare", {"player1_id": player1_id, "player2_id": player2_id})


# Initialize session state for page navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Standings"


def render_header():
    """Render the fixed header with navigation."""
    # Header HTML with logo and title
    header_html = """
    <div class="fixed-header">
        <div class="header-container">
            <div class="header-left">
                <img src="https://cdn.nba.com/logos/leagues/logo-nba.svg" class="nba-logo" alt="NBA Logo"/>
                <h1 class="header-title">Analytics Dashboard</h1>
            </div>
            <div class="nav-tabs-container">
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # Navigation tabs in header - 7 tabs now including Compare Players
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.columns(7)

    with tab1:
        if st.button("Standings", key="nav_standings", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Standings" else "secondary"):
            st.session_state.current_page = "Standings"
            st.rerun()

    with tab2:
        if st.button("Today's Games", key="nav_games", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Today's Games" else "secondary"):
            st.session_state.current_page = "Today's Games"
            st.rerun()

    with tab3:
        if st.button("Live Game", key="nav_live", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Live Game" else "secondary"):
            st.session_state.current_page = "Live Game"
            st.rerun()

    with tab4:
        if st.button("Leaders", key="nav_leaders", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Leaders" else "secondary"):
            st.session_state.current_page = "Leaders"
            st.rerun()

    with tab5:
        if st.button("Team Analysis", key="nav_analysis", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Team Analysis" else "secondary"):
            st.session_state.current_page = "Team Analysis"
            st.rerun()

    with tab6:
        if st.button("Compare", key="nav_compare", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Compare" else "secondary"):
            st.session_state.current_page = "Compare"
            st.rerun()

    with tab7:
        if st.button("Predictions", key="nav_predictions", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Predictions" else "secondary"):
            st.session_state.current_page = "Predictions"
            st.rerun()


def render_status_widget():
    """Render the bottom-right floating status widget."""
    api_healthy = check_api_health()
    status_class = "status-healthy" if api_healthy else "status-error"
    status_text = "Connected" if api_healthy else "Disconnected"

    widget_html = f"""
    <div class="status-widget">
        <div class="status-widget-content">
            <span class="status-indicator {status_class}"></span>
            <span>{status_text}</span>
        </div>
        <div class="widget-divider"></div>
        <span style="color: white; font-size: 0.75rem;">{datetime.now().strftime('%I:%M %p')}</span>
    </div>
    """
    st.markdown(widget_html, unsafe_allow_html=True)


def render_standings():
    """Render the standings page."""
    st.markdown('<h2 class="sub-header">Conference Standings</h2>', unsafe_allow_html=True)

    # Action buttons
    col_refresh, col_sync, col_spacer = st.columns([1, 1, 4])
    with col_refresh:
        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_sync:
        if st.button("Sync from NBA", use_container_width=True):
            result = api_post("/api/refresh/full")
            if result:
                st.success("Sync started!")
                time.sleep(2)
                st.rerun()

    standings = get_standings()

    if not standings:
        st.warning("No standings data available. Try refreshing or syncing data.")
        return

    updated = standings.get('updated_at', 'Unknown')
    st.caption(f"Last updated: {updated}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Eastern Conference")
        if standings.get('east'):
            east_df = pd.DataFrame([
                {
                    'Rank': s.get('conf_rank', '-'),
                    'Team': f"{s['team_abbr']}",
                    'W': s['wins'],
                    'L': s['losses'],
                    'PCT': f"{s['win_pct']:.3f}",
                    'GB': s['games_back'],
                    'Streak': s.get('streak', '-'),
                    'L10': s.get('last_10', '-')
                }
                for s in standings['east']
            ])
            st.dataframe(east_df, use_container_width=True, hide_index=True)
        else:
            st.info("No Eastern Conference standings available")

    with col2:
        st.markdown("### Western Conference")
        if standings.get('west'):
            west_df = pd.DataFrame([
                {
                    'Rank': s.get('conf_rank', '-'),
                    'Team': f"{s['team_abbr']}",
                    'W': s['wins'],
                    'L': s['losses'],
                    'PCT': f"{s['win_pct']:.3f}",
                    'GB': s['games_back'],
                    'Streak': s.get('streak', '-'),
                    'L10': s.get('last_10', '-')
                }
                for s in standings['west']
            ])
            st.dataframe(west_df, use_container_width=True, hide_index=True)
        else:
            st.info("No Western Conference standings available")

    # Visualization
    st.markdown("### Win Percentage by Team")
    all_standings = standings.get('east', []) + standings.get('west', [])
    if all_standings:
        viz_df = pd.DataFrame([
            {
                'Team': s['team_abbr'],
                'Win %': s['win_pct'] * 100,
                'Conference': s['conference']
            }
            for s in all_standings
        ]).sort_values('Win %', ascending=True)

        fig = px.bar(
            viz_df,
            x='Win %',
            y='Team',
            color='Conference',
            orientation='h',
            color_discrete_map={'East': '#17408B', 'West': '#C9082A'},
            title='Win Percentage by Team'
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
        recent = get_recent_games(days=7)
        if not recent:
            st.warning("No recent games available.")
            return
        games = recent[:12]

    auto_refresh = st.checkbox("Auto-refresh (every 30 seconds)", value=False)

    if auto_refresh:
        time.sleep(30)
        st.cache_data.clear()
        st.rerun()

    # Display games in a grid
    for row_start in range(0, len(games), 3):
        cols = st.columns(3)
        for i, col in enumerate(cols):
            game_idx = row_start + i
            if game_idx >= len(games):
                break

            game = games[game_idx]
            status = game.get('status', 'unknown')
            status_emoji = "LIVE" if status == "live" else ("FINAL" if status == "final" else "SCHEDULED")

            home = game.get('home_team', {})
            away = game.get('away_team', {})

            with col:
                with st.container():
                    if status == 'live':
                        st.markdown(f'<div class="live-indicator"><span class="live-dot"></span> LIVE - Q{game.get("period", "")} {game.get("clock", "")}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{status_emoji}**")

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


def draw_3d_shot_chart(shots: list = None) -> go.Figure:
    """Draw a stunning 3D NBA half-court with shot arcs."""
    fig = go.Figure()

    scale = 1.0

    # Court floor outline
    court_x = np.array([-250, 250, 250, -250, -250]) * scale
    court_y = np.array([-50, -50, 420, 420, -50]) * scale
    court_z = np.zeros(5)

    fig.add_trace(go.Scatter3d(
        x=court_x, y=court_y, z=court_z,
        mode='lines',
        line=dict(color='#1a365d', width=4),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Paint/Key outline
    paint_x = np.array([-80, 80, 80, -80, -80]) * scale
    paint_y = np.array([-50, -50, 140, 140, -50]) * scale
    paint_z = np.zeros(5)

    fig.add_trace(go.Scatter3d(
        x=paint_x, y=paint_y, z=paint_z,
        mode='lines',
        line=dict(color='#c53030', width=3),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Free throw circle
    theta_ft = np.linspace(0, 2*np.pi, 50)
    ft_x = 60 * np.cos(theta_ft) * scale
    ft_y = (140 + 60 * np.sin(theta_ft)) * scale
    ft_z = np.zeros_like(theta_ft)

    fig.add_trace(go.Scatter3d(
        x=ft_x, y=ft_y, z=ft_z,
        mode='lines',
        line=dict(color='#c53030', width=2),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Three-point arc
    theta_3pt = np.linspace(np.arccos(220/237.5), np.pi - np.arccos(220/237.5), 100)
    arc3_x = 237.5 * np.cos(theta_3pt) * scale
    arc3_y = 237.5 * np.sin(theta_3pt) * scale
    arc3_z = np.zeros_like(theta_3pt)

    fig.add_trace(go.Scatter3d(
        x=arc3_x, y=arc3_y, z=arc3_z,
        mode='lines',
        line=dict(color='#1a365d', width=3),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Three-point corner lines
    fig.add_trace(go.Scatter3d(
        x=[-220*scale, -220*scale], y=[-50*scale, 90*scale], z=[0, 0],
        mode='lines', line=dict(color='#1a365d', width=3),
        showlegend=False, hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter3d(
        x=[220*scale, 220*scale], y=[-50*scale, 90*scale], z=[0, 0],
        mode='lines', line=dict(color='#1a365d', width=3),
        showlegend=False, hoverinfo='skip'
    ))

    # Basket/Rim
    rim_theta = np.linspace(0, 2*np.pi, 30)
    rim_x = 7.5 * np.cos(rim_theta) * scale
    rim_y = 7.5 * np.sin(rim_theta) * scale
    rim_z = np.ones_like(rim_theta) * 100

    fig.add_trace(go.Scatter3d(
        x=rim_x, y=rim_y, z=rim_z,
        mode='lines',
        line=dict(color='#dd6b20', width=6),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Plot shots if provided
    if shots:
        made_shots = [s for s in shots if s.get('made')]
        missed_shots = [s for s in shots if not s.get('made')]

        def create_shot_arc(shot_x, shot_y, distance):
            t = np.linspace(0, 1, 30)
            x0, y0 = shot_x * scale, shot_y * scale
            z0 = 80
            x1, y1 = 0, 0
            z1 = 100
            arc_height = max(150, 100 + distance * 3)
            arc_x = x0 + (x1 - x0) * t
            arc_y = y0 + (y1 - y0) * t
            arc_z = z0 + (z1 - z0) * t + 4 * (arc_height - max(z0, z1)) * t * (1 - t)
            return arc_x, arc_y, arc_z

        for shot in made_shots:
            arc_x, arc_y, arc_z = create_shot_arc(shot['x'], shot['y'], shot.get('distance', 15))
            fig.add_trace(go.Scatter3d(
                x=arc_x, y=arc_y, z=arc_z,
                mode='lines',
                line=dict(color='#38a169', width=4),
                showlegend=False,
                hoverinfo='skip',
                opacity=0.7
            ))

        if made_shots:
            hover_texts = [
                f"<b>{s.get('player_name', 'Unknown')}</b><br>MADE<br>{s.get('shot_type', '')} ({s.get('distance', 0)}ft)"
                for s in made_shots
            ]
            fig.add_trace(go.Scatter3d(
                x=[s['x'] * scale for s in made_shots],
                y=[s['y'] * scale for s in made_shots],
                z=[80 for _ in made_shots],
                mode='markers',
                marker=dict(size=10, color='#38a169', symbol='circle', line=dict(width=2, color='#276749')),
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>',
                showlegend=False
            ))

        if missed_shots:
            hover_texts_missed = [
                f"<b>{s.get('player_name', 'Unknown')}</b><br>MISSED<br>{s.get('shot_type', '')} ({s.get('distance', 0)}ft)"
                for s in missed_shots
            ]
            fig.add_trace(go.Scatter3d(
                x=[s['x'] * scale for s in missed_shots],
                y=[s['y'] * scale for s in missed_shots],
                z=[80 for _ in missed_shots],
                mode='markers',
                marker=dict(size=8, color='#e53e3e', symbol='x', line=dict(width=2, color='#c53030')),
                text=hover_texts_missed,
                hovertemplate='%{text}<extra></extra>',
                showlegend=False
            ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-300, 300], showgrid=False, showbackground=True, backgroundcolor='#e8dcc4', showticklabels=False, title=''),
            yaxis=dict(range=[-100, 450], showgrid=False, showbackground=True, backgroundcolor='#e8dcc4', showticklabels=False, title=''),
            zaxis=dict(range=[0, 250], showgrid=False, showbackground=False, showticklabels=False, title=''),
            camera=dict(eye=dict(x=0, y=-1.8, z=0.8), center=dict(x=0, y=0.1, z=-0.1), up=dict(x=0, y=0, z=1)),
            aspectmode='manual',
            aspectratio=dict(x=1.2, y=1, z=0.5),
        ),
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor='rgba(20, 20, 30, 1)',
    )

    return fig


def render_play_feed(plays: list, limit: int = 20):
    """Render the play-by-play feed with icons."""
    if not plays:
        st.info("No plays to display yet.")
        return

    icons = {
        'SHOT_MADE': '🟢', 'SHOT_MISSED': '❌', 'FREE_THROW': '🎱',
        'REBOUND': '🔄', 'TURNOVER': '💨', 'FOUL': '📍',
        'VIOLATION': '🚫', 'SUBSTITUTION': '🔀', 'TIMEOUT': '⏸️',
        'JUMP_BALL': '⬆️', 'PERIOD_BEGIN': '▶️', 'PERIOD_END': '⏹️', 'OTHER': '📋',
    }

    recent_plays = list(reversed(plays[-limit:]))

    st.markdown("### Play-by-Play")
    for play in recent_plays:
        event_type = play.get('event_type', 'OTHER')
        icon = icons.get(event_type, '📋')
        period = play.get('period', 0)
        clock = play.get('clock', '')
        description = play.get('description', '')
        team = play.get('team_abbr', '')
        score = f"{play.get('away_score', 0)} - {play.get('home_score', 0)}"

        if event_type in ['SHOT_MADE', 'FREE_THROW']:
            color = '#38a169'
        elif event_type == 'SHOT_MISSED':
            color = '#e53e3e'
        else:
            color = '#4a5568'

        st.markdown(
            f"""<div style="padding: 8px; margin: 4px 0; border-left: 3px solid {color}; background: #f7fafc; border-radius: 4px; color: #1a202c;">
                <span style="font-size: 1.2em;">{icon}</span>
                <strong style="color: #2d3748;">Q{period} {clock}</strong> <span style="color: #4a5568;">[{team}]</span> <span style="color: #1a202c;">{description}</span>
                <span style="float: right; color: #718096;">{score}</span>
            </div>""",
            unsafe_allow_html=True
        )


def render_live_game():
    """Render the live game visualization page."""
    st.markdown('<h2 class="sub-header">Live Game Center</h2>', unsafe_allow_html=True)

    live_games = get_live_games()

    if not live_games:
        st.info("No games currently in progress or scheduled for today.")
        st.markdown("### Check back later for live game updates!")
        return

    active_games = [g for g in live_games if g.get('is_live')]

    if active_games:
        st.markdown(f'<div class="live-indicator"><span class="live-dot"></span> {len(active_games)} game(s) currently LIVE!</div>', unsafe_allow_html=True)
        games_to_show = active_games
    else:
        st.info("No games currently in progress. Showing today's scheduled games.")
        games_to_show = live_games

    game_options = {
        f"{g['away_team_abbr']} @ {g['home_team_abbr']} - {g['status']}": g['game_id']
        for g in games_to_show
    }

    if not game_options:
        st.warning("No games available.")
        return

    selected_label = st.selectbox("Select Game", options=list(game_options.keys()))
    selected_game_id = game_options[selected_label]

    selected_game = next((g for g in games_to_show if g['game_id'] == selected_game_id), None)

    if selected_game:
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.markdown(f"### {selected_game['away_team_name']}")
            st.markdown(f"## {selected_game['away_score']}")
        with col2:
            st.markdown("### VS")
            if selected_game.get('is_live'):
                st.markdown(f"**Q{selected_game.get('period', 0)}** {selected_game.get('game_clock', '')}")
            else:
                st.markdown(f"**{selected_game['status']}**")
        with col3:
            st.markdown(f"### {selected_game['home_team_name']}")
            st.markdown(f"## {selected_game['home_score']}")

    st.markdown("---")

    auto_refresh = st.checkbox("Auto-refresh (15s)", value=selected_game.get('is_live', False) if selected_game else False)
    if auto_refresh:
        st.caption("Auto-refreshing every 15 seconds...")

    shots = get_game_shots(selected_game_id)
    plays = get_game_plays(selected_game_id)

    if shots and selected_game:
        away_team = selected_game.get('away_team_abbr', 'AWAY')
        home_team = selected_game.get('home_team_abbr', 'HOME')
        away_team_id = selected_game.get('away_team_id', 0)
        home_team_id = selected_game.get('home_team_id', 0)

        players_in_game = {}
        for s in shots:
            pid = s.get('player_id', 0)
            pname = s.get('player_name', 'Unknown')
            pteam = s.get('team_abbr', '')
            if pid and pname not in players_in_game:
                players_in_game[pname] = {'id': pid, 'team': pteam}
    else:
        away_team = 'AWAY'
        home_team = 'HOME'
        away_team_id = 0
        home_team_id = 0
        players_in_game = {}

    tab1, tab2, tab3 = st.tabs(["Shot Chart", "Play-by-Play", "Box Score"])

    with tab1:
        st.markdown("### 3D Shot Chart")
        if shots:
            filter_col1, filter_col2, filter_col3 = st.columns([1, 2, 1])

            with filter_col1:
                if away_team_id:
                    st.image(f"https://cdn.nba.com/logos/nba/{away_team_id}/global/L/logo.svg", width=80)
                away_filter = st.checkbox(f"{away_team}", value=True, key="away_filter")

            with filter_col2:
                player_options = ["All Players"] + sorted(players_in_game.keys())
                selected_player = st.selectbox("Filter by Player", options=player_options, key="player_filter")

            with filter_col3:
                if home_team_id:
                    st.image(f"https://cdn.nba.com/logos/nba/{home_team_id}/global/L/logo.svg", width=80)
                home_filter = st.checkbox(f"{home_team}", value=True, key="home_filter")

            filtered_shots = shots.copy()
            if not away_filter:
                filtered_shots = [s for s in filtered_shots if s.get('team_abbr') != away_team]
            if not home_filter:
                filtered_shots = [s for s in filtered_shots if s.get('team_abbr') != home_team]
            if selected_player != "All Players":
                filtered_shots = [s for s in filtered_shots if s.get('player_name') == selected_player]

            if selected_player != "All Players" and selected_player in players_in_game:
                player_info = players_in_game[selected_player]
                headshot_col1, headshot_col2 = st.columns([1, 3])
                with headshot_col1:
                    st.image(f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_info['id']}.png", width=130)
                with headshot_col2:
                    player_shots = [s for s in shots if s.get('player_name') == selected_player]
                    made = len([s for s in player_shots if s.get('made')])
                    fg_pct = (made / len(player_shots) * 100) if player_shots else 0
                    st.markdown(f"### {selected_player}")
                    st.markdown(f"**Team:** {player_info['team']}")
                    st.markdown(f"**FG:** {made}/{len(player_shots)} ({fg_pct:.1f}%)")

            st.caption("Rotate and zoom the 3D court. Green arcs show made shots.")
            st.plotly_chart(draw_3d_shot_chart(filtered_shots), use_container_width=True)

            made_count = len([s for s in filtered_shots if s.get('made')])
            missed_count = len([s for s in filtered_shots if not s.get('made')])
            st.markdown(f"**{len(filtered_shots)} shots shown** | Made: {made_count} | Missed: {missed_count}")
        else:
            st.info("No shot data available for this game yet.")
            st.plotly_chart(draw_3d_shot_chart([]), use_container_width=True)

    with tab2:
        render_play_feed(plays or [])

    with tab3:
        st.markdown("### Box Score")
        game_data = get_live_game_data(selected_game_id)
        if game_data and game_data.get('box_score'):
            box_score = game_data['box_score']
            player_stats = box_score.get('player_stats', [])

            if player_stats:
                teams = set(p['team_abbr'] for p in player_stats)

                for team in sorted(teams):
                    st.markdown(f"#### {team}")
                    team_players = [p for p in player_stats if p['team_abbr'] == team]

                    df = pd.DataFrame([{
                        'Player': p['player_name'],
                        'MIN': p.get('minutes', '0'),
                        'PTS': p.get('points', 0),
                        'REB': p.get('rebounds', 0),
                        'AST': p.get('assists', 0),
                        'STL': p.get('steals', 0),
                        'BLK': p.get('blocks', 0),
                        'FG': f"{p.get('fg_made', 0)}/{p.get('fg_attempted', 0)}",
                        '3P': f"{p.get('three_made', 0)}/{p.get('three_attempted', 0)}",
                        '+/-': p.get('plus_minus', 0)
                    } for p in team_players])

                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Box score not available yet.")
        else:
            st.info("Box score data not available.")


def render_leaders():
    """Render the statistical leaders page."""
    st.markdown('<h2 class="sub-header">Statistical Leaders</h2>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        stat_category = st.selectbox(
            "Category",
            ["points", "rebounds", "assists", "steals", "blocks"],
            format_func=lambda x: x.title()
        )

    with col2:
        num_leaders = st.slider("Number of leaders", 5, 25, 10)

    leaders = get_stat_leaders(stat_category, num_leaders)

    if not leaders:
        st.warning("No statistical data available.")
        return

    df = pd.DataFrame(leaders)
    display_df = df.rename(columns={
        'player_name': 'Player', 'team_abbr': 'Team', 'minutes': 'MPG',
        'points': 'PPG', 'rebounds': 'RPG', 'assists': 'APG',
        'steals': 'SPG', 'blocks': 'BPG', 'turnovers': 'TOV',
        'fg_pct': 'FG%', 'three_pct': '3P%', 'ft_pct': 'FT%', 'plus_minus': '+/-'
    })

    base_cols = ['Player', 'Team', 'MPG']
    stat_cols = {
        'points': ['PPG', 'FG%', '3P%', 'FT%'],
        'rebounds': ['RPG', 'PPG', '+/-'],
        'assists': ['APG', 'PPG', 'TOV'],
        'steals': ['SPG', 'PPG', '+/-'],
        'blocks': ['BPG', 'PPG', '+/-'],
    }
    cols_to_show = base_cols + stat_cols[stat_category]

    st.dataframe(display_df[cols_to_show], use_container_width=True, hide_index=True)

    st.markdown(f"### Top {num_leaders} in {stat_category.title()}")

    stat_map = {'points': 'PPG', 'rebounds': 'RPG', 'assists': 'APG', 'steals': 'SPG', 'blocks': 'BPG'}

    fig = px.bar(
        display_df.head(num_leaders),
        x='Player',
        y=stat_map[stat_category],
        color='Team',
        title=f'{stat_category.title()} Leaders'
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def render_team_analysis():
    """Render team analysis page."""
    st.markdown('<h2 class="sub-header">Team Analysis</h2>', unsafe_allow_html=True)

    teams = get_teams()

    if not teams:
        st.warning("No team data available.")
        return

    team_options = {f"{t['abbreviation']} - {t['name']}": t['id'] for t in teams}
    selected_team = st.selectbox("Select Team", options=list(team_options.keys()))
    team_id = team_options[selected_team]

    recent_games = get_recent_games(days=30, team_id=team_id)

    if recent_games:
        st.markdown("### Recent Games")

        games_data = []
        for game in recent_games:
            home = game['home_team']
            away = game['away_team']

            is_home = home['id'] == team_id
            team_score = home['score'] if is_home else away['score']
            opp_score = away['score'] if is_home else home['score']
            opponent = away['abbr'] if is_home else home['abbr']
            result = 'W' if team_score > opp_score else 'L'

            games_data.append({
                'Date': game.get('game_date', ''),
                'Opponent': f"{'vs' if is_home else '@'} {opponent}",
                'Result': result,
                'Score': f"{team_score}-{opp_score}",
                'Margin': team_score - opp_score
            })

        games_df = pd.DataFrame(games_data)

        col1, col2, col3, col4 = st.columns(4)
        wins = len([g for g in games_data if g['Result'] == 'W'])
        losses = len([g for g in games_data if g['Result'] == 'L'])

        with col1:
            st.metric("Record (Last 30 days)", f"{wins}-{losses}")
        with col2:
            st.metric("Win %", f"{wins/(wins+losses)*100:.1f}%" if wins+losses > 0 else "N/A")
        with col3:
            avg_margin = sum(g['Margin'] for g in games_data) / len(games_data) if games_data else 0
            st.metric("Avg Margin", f"{avg_margin:+.1f}")
        with col4:
            st.metric("Games Played", len(games_data))

        st.dataframe(games_df, use_container_width=True, hide_index=True)

        if len(games_df) > 1:
            st.markdown("### Point Differential Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(games_df))),
                y=games_df['Margin'],
                mode='lines+markers',
                name='Margin',
                line=dict(color='#4299e1'),
                marker=dict(color=['green' if m > 0 else 'red' for m in games_df['Margin']], size=10)
            ))
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_layout(xaxis_title="Game", yaxis_title="Point Margin", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recent games found for this team.")


def render_predictions():
    """Render the predictions page with LSTM forecasts."""
    st.markdown('<h2 class="sub-header">End-of-Season Predictions</h2>', unsafe_allow_html=True)

    predictions = get_predictions()

    if not predictions:
        st.warning("No predictions available. The LSTM model may need to be trained first.")
        return

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
                st.metric("Training Seasons", len(model_info.get("training_seasons", [])))

    st.caption(f"Predictions generated: {predictions.get('prediction_date', 'Unknown')}")

    tab1, tab2, tab3 = st.tabs(["Conference Rankings", "Playoff Probabilities", "Statistical Forecasts"])

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
        if predictions.get('east'):
            actual_east = {s['team_abbr']: s for s in standings.get('east', [])} if standings else {}

            east_data = []
            for p in predictions['east']:
                actual = actual_east.get(p['team_abbr'], {})
                east_data.append({
                    'Rank': p.get('predicted_conference_rank', '-'),
                    'Team': p['team_abbr'],
                    'Pred W': round(p['predicted_wins']),
                    'Pred L': round(p['predicted_losses']),
                    'Actual W': actual.get('wins', '-'),
                    'Playoff %': f"{p['playoff_probability'] * 100:.0f}%",
                })

            st.dataframe(pd.DataFrame(east_data), use_container_width=True, hide_index=True)
        else:
            st.info("No Eastern Conference predictions")

    with col2:
        st.markdown("### Western Conference")
        if predictions.get('west'):
            actual_west = {s['team_abbr']: s for s in standings.get('west', [])} if standings else {}

            west_data = []
            for p in predictions['west']:
                actual = actual_west.get(p['team_abbr'], {})
                west_data.append({
                    'Rank': p.get('predicted_conference_rank', '-'),
                    'Team': p['team_abbr'],
                    'Pred W': round(p['predicted_wins']),
                    'Pred L': round(p['predicted_losses']),
                    'Actual W': actual.get('wins', '-'),
                    'Playoff %': f"{p['playoff_probability'] * 100:.0f}%",
                })

            st.dataframe(pd.DataFrame(west_data), use_container_width=True, hide_index=True)
        else:
            st.info("No Western Conference predictions")

    st.markdown("### Predicted vs Current Wins")
    all_predictions = predictions.get('east', []) + predictions.get('west', [])

    if all_predictions and standings:
        all_standings = standings.get('east', []) + standings.get('west', [])
        standings_map = {s['team_abbr']: s['wins'] for s in all_standings}

        fig = go.Figure()

        teams = [p['team_abbr'] for p in all_predictions]
        pred_wins = [p['predicted_wins'] for p in all_predictions]
        actual_wins = [standings_map.get(t, 0) for t in teams]

        fig.add_trace(go.Bar(name='Predicted Wins', x=teams, y=pred_wins, marker_color='#17408B'))
        fig.add_trace(go.Bar(name='Current Wins', x=teams, y=actual_wins, marker_color='#C9082A'))

        fig.update_layout(
            barmode='group',
            xaxis_tickangle=-45,
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)


def render_playoff_probabilities(predictions: dict):
    """Display playoff probability visualizations."""
    st.markdown("### Playoff Qualification Probabilities")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Eastern Conference")
        east = sorted(predictions.get('east', []), key=lambda x: x.get('playoff_probability', 0), reverse=True)

        if east:
            fig = px.bar(
                x=[t['team_abbr'] for t in east],
                y=[t['playoff_probability'] * 100 for t in east],
                color=[t['playoff_probability'] for t in east],
                color_continuous_scale='RdYlGn',
                labels={'x': 'Team', 'y': 'Probability (%)'}
            )
            fig.update_layout(showlegend=False, height=400, coloraxis_showscale=False)
            fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%", annotation_position="right")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Western Conference")
        west = sorted(predictions.get('west', []), key=lambda x: x.get('playoff_probability', 0), reverse=True)

        if west:
            fig = px.bar(
                x=[t['team_abbr'] for t in west],
                y=[t['playoff_probability'] * 100 for t in west],
                color=[t['playoff_probability'] for t in west],
                color_continuous_scale='RdYlGn',
                labels={'x': 'Team', 'y': 'Probability (%)'}
            )
            fig.update_layout(showlegend=False, height=400, coloraxis_showscale=False)
            fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%", annotation_position="right")
            st.plotly_chart(fig, use_container_width=True)


def render_stat_forecasts(predictions: dict):
    """Display predicted statistical metrics for teams."""
    st.markdown("### Predicted Season Statistics")

    all_teams = predictions.get('east', []) + predictions.get('west', [])
    team_options = {f"{t['team_abbr']} - {t['team_name']}": t for t in all_teams}

    if not team_options:
        st.info("No team predictions available")
        return

    selected = st.selectbox("Select Team", options=list(team_options.keys()))
    team = team_options[selected]

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
        prob_pct = team['playoff_probability'] * 100
        st.metric("Playoff Prob", f"{prob_pct:.0f}%")

    st.markdown("### Team Efficiency: Offense vs Defense")

    fig = px.scatter(
        x=[t['predicted_ppg'] for t in all_teams],
        y=[t['predicted_oppg'] for t in all_teams],
        text=[t['team_abbr'] for t in all_teams],
        color=[t['playoff_probability'] for t in all_teams],
        color_continuous_scale='RdYlGn',
        labels={'x': 'Predicted PPG (Offense)', 'y': 'Predicted OPPG (Defense)', 'color': 'Playoff Prob'}
    )
    fig.update_traces(textposition='top center', marker_size=12)
    fig.update_layout(height=500)

    if all_teams:
        avg_ppg = sum(t['predicted_ppg'] for t in all_teams) / len(all_teams)
        avg_oppg = sum(t['predicted_oppg'] for t in all_teams) / len(all_teams)
        fig.add_hline(y=avg_oppg, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=avg_ppg, line_dash="dash", line_color="gray", opacity=0.5)

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Teams in upper-left (high PPG, low OPPG) are predicted to be most successful.")


def render_player_compare():
    """Render the player comparison page."""
    st.markdown('<h2 class="sub-header">Player Comparison</h2>', unsafe_allow_html=True)
    st.caption("Compare two NBA players side by side")

    # Initialize session state for selected players
    if 'compare_player1' not in st.session_state:
        st.session_state.compare_player1 = None
    if 'compare_player2' not in st.session_state:
        st.session_state.compare_player2 = None

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Player 1")
        search1 = st.text_input("Search Player 1", key="search_player1", placeholder="Enter player name...")
        if search1 and len(search1) >= 2:
            results1 = search_players(search1)
            if results1:
                options1 = {f"{p['player_name']} ({p['team_abbr'] or 'FA'})": p['player_id'] for p in results1}
                selected1 = st.selectbox("Select Player 1", options=list(options1.keys()), key="select_p1")
                if selected1:
                    st.session_state.compare_player1 = options1[selected1]
            else:
                st.info("No players found")

    with col2:
        st.markdown("### Player 2")
        search2 = st.text_input("Search Player 2", key="search_player2", placeholder="Enter player name...")
        if search2 and len(search2) >= 2:
            results2 = search_players(search2)
            if results2:
                options2 = {f"{p['player_name']} ({p['team_abbr'] or 'FA'})": p['player_id'] for p in results2}
                selected2 = st.selectbox("Select Player 2", options=list(options2.keys()), key="select_p2")
                if selected2:
                    st.session_state.compare_player2 = options2[selected2]
            else:
                st.info("No players found")

    # Compare button and results
    if st.session_state.compare_player1 and st.session_state.compare_player2:
        if st.button("Compare Players", type="primary", use_container_width=True):
            with st.spinner("Fetching player stats..."):
                comparison = compare_players(
                    st.session_state.compare_player1,
                    st.session_state.compare_player2
                )

            if comparison:
                st.markdown("---")
                st.markdown(f"### {comparison['season']} Season Stats")

                p1 = comparison['player1']
                p2 = comparison['player2']

                # Side by side stats table
                stats_data = {
                    'Stat': ['Games Played', 'Minutes', 'Points', 'Rebounds', 'Assists',
                             'Steals', 'Blocks', 'Turnovers', 'FG%', '3P%', 'FT%'],
                    p1['player_name']: [
                        p1['games_played'], p1['minutes'], p1['points'], p1['rebounds'],
                        p1['assists'], p1['steals'], p1['blocks'], p1['turnovers'],
                        f"{p1['fg_pct']}%" if p1['fg_pct'] else '-',
                        f"{p1['fg3_pct']}%" if p1['fg3_pct'] else '-',
                        f"{p1['ft_pct']}%" if p1['ft_pct'] else '-'
                    ],
                    p2['player_name']: [
                        p2['games_played'], p2['minutes'], p2['points'], p2['rebounds'],
                        p2['assists'], p2['steals'], p2['blocks'], p2['turnovers'],
                        f"{p2['fg_pct']}%" if p2['fg_pct'] else '-',
                        f"{p2['fg3_pct']}%" if p2['fg3_pct'] else '-',
                        f"{p2['ft_pct']}%" if p2['ft_pct'] else '-'
                    ]
                }

                st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

                # Radar chart for visual comparison
                st.markdown("### Visual Comparison")

                categories = ['PPG', 'RPG', 'APG', 'SPG', 'BPG']
                p1_values = [p1['points'], p1['rebounds'], p1['assists'], p1['steals'], p1['blocks']]
                p2_values = [p2['points'], p2['rebounds'], p2['assists'], p2['steals'], p2['blocks']]

                fig = go.Figure()

                fig.add_trace(go.Scatterpolar(
                    r=p1_values + [p1_values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=p1['player_name'],
                    line_color='#17408B'
                ))

                fig.add_trace(go.Scatterpolar(
                    r=p2_values + [p2_values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=p2['player_name'],
                    line_color='#C9082A'
                ))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, max(max(p1_values), max(p2_values)) * 1.2])
                    ),
                    showlegend=True,
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)

                # Bar chart comparison
                st.markdown("### Per-Game Statistics")

                chart_df = pd.DataFrame({
                    'Stat': categories * 2,
                    'Value': p1_values + p2_values,
                    'Player': [p1['player_name']] * 5 + [p2['player_name']] * 5
                })

                fig_bar = px.bar(
                    chart_df,
                    x='Stat',
                    y='Value',
                    color='Player',
                    barmode='group',
                    color_discrete_map={p1['player_name']: '#17408B', p2['player_name']: '#C9082A'}
                )
                fig_bar.update_layout(height=400)
                st.plotly_chart(fig_bar, use_container_width=True)

            else:
                st.error("Could not fetch comparison data. Please try again.")
    else:
        st.info("Search and select two players to compare their stats.")


# Main application
def main():
    """Main application entry point."""
    render_header()
    render_status_widget()

    st.write("")

    if st.session_state.current_page == "Standings":
        render_standings()
    elif st.session_state.current_page == "Today's Games":
        render_todays_games()
    elif st.session_state.current_page == "Live Game":
        render_live_game()
    elif st.session_state.current_page == "Leaders":
        render_leaders()
    elif st.session_state.current_page == "Team Analysis":
        render_team_analysis()
    elif st.session_state.current_page == "Compare":
        render_player_compare()
    elif st.session_state.current_page == "Predictions":
        render_predictions()


if __name__ == "__main__":
    main()
