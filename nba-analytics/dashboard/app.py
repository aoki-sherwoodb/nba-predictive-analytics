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

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="NBA Analytics Dashboard",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
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


def check_api_health():
    """Check if API is healthy."""
    try:
        health = api_get("/health")
        return health and health.get("status") in ["healthy", "degraded"]
    except:
        return False


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

    # Navigation tabs in header
    tab1, tab2, tab3, tab4 = st.columns(4)

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
        if st.button("Leaders", key="nav_leaders", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Leaders" else "secondary"):
            st.session_state.current_page = "Leaders"
            st.rerun()

    with tab4:
        if st.button("Team Analysis", key="nav_analysis", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Team Analysis" else "secondary"):
            st.session_state.current_page = "Team Analysis"
            st.rerun()


def render_status_widget():
    """Render the bottom-right floating status widget with action buttons."""
    # Check API health
    api_healthy = check_api_health()
    status_class = "status-healthy" if api_healthy else "status-error"
    status_text = "Connected" if api_healthy else "Disconnected"

    # Status widget HTML
    widget_html = f"""
    <div class="status-widget">
        <div class="status-widget-content">
            <span class="status-indicator {status_class}"></span>
            <span>{status_text}</span>
        </div>
        <div class="widget-divider"></div>
        <div id="widget-actions"></div>
    </div>
    """
    st.markdown(widget_html, unsafe_allow_html=True)

    # Action buttons in widget
    action_col1, action_col2 = st.columns([1, 1])

    with action_col1:
        st.markdown('<div class="action-button">', unsafe_allow_html=True)
        if st.button("🔄", key="widget_refresh", use_container_width=True,
                     help="Clear cache and refresh data"):
            st.cache_data.clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with action_col2:
        st.markdown('<div class="action-button">', unsafe_allow_html=True)
        if st.button("📥", key="widget_sync", use_container_width=True,
                     help="Trigger full data sync from NBA API"):
            result = api_post("/api/refresh/full")
            if result:
                st.success("Sync started!", icon="✅")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Sync failed!", icon="❌")
        st.markdown('</div>', unsafe_allow_html=True)


def render_standings():
    """Render the standings page."""
    st.markdown('<h2 class="sub-header">Conference Standings</h2>', unsafe_allow_html=True)

    standings = get_standings()

    if not standings:
        st.warning("No standings data available. Try refreshing or syncing data.", icon="⚠️")
        return

    # Display last updated
    updated = standings.get('updated_at', 'Unknown')
    st.caption(f"Last updated: {updated}")

    # Create two columns for East and West
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔵 Eastern Conference")
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
            st.dataframe(
                east_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Rank': st.column_config.NumberColumn('Rank', width='small'),
                    'Team': st.column_config.TextColumn('Team', width='small'),
                    'W': st.column_config.NumberColumn('W', width='small'),
                    'L': st.column_config.NumberColumn('L', width='small'),
                    'PCT': st.column_config.TextColumn('PCT', width='small'),
                    'GB': st.column_config.NumberColumn('GB', width='small'),
                    'Streak': st.column_config.TextColumn('Streak', width='small'),
                    'L10': st.column_config.TextColumn('L10', width='small'),
                }
            )
        else:
            st.info("No Eastern Conference standings available")

    with col2:
        st.markdown("### 🔴 Western Conference")
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
            st.dataframe(
                west_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Rank': st.column_config.NumberColumn('Rank', width='small'),
                    'Team': st.column_config.TextColumn('Team', width='small'),
                    'W': st.column_config.NumberColumn('W', width='small'),
                    'L': st.column_config.NumberColumn('L', width='small'),
                    'PCT': st.column_config.TextColumn('PCT', width='small'),
                    'GB': st.column_config.NumberColumn('GB', width='small'),
                    'Streak': st.column_config.TextColumn('Streak', width='small'),
                    'L10': st.column_config.TextColumn('L10', width='small'),
                }
            )
        else:
            st.info("No Western Conference standings available")

    # Visualization: Win percentage comparison
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
            color_discrete_map={'East': '#1f77b4', 'West': '#d62728'},
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
        st.info("No games scheduled for today.", icon="ℹ️")
        return

    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (every 30 seconds)", value=False)

    if auto_refresh:
        time.sleep(30)
        st.cache_data.clear()
        st.rerun()

    # Display games
    cols = st.columns(min(3, len(games)))

    for idx, game in enumerate(games):
        with cols[idx % 3]:
            status = game['status']
            status_emoji = "🔴" if status == "live" else ("✅" if status == "final" else "⏰")

            home = game['home_team']
            away = game['away_team']

            # Create game card
            st.markdown(f"""
            <div class="game-card">
                <div style="text-align: center; margin-bottom: 0.5rem;">
                    {status_emoji} <strong>{status.upper()}</strong>
                    {f" - Q{game.get('period', '')} {game.get('clock', '')}" if status == 'live' else ''}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="text-align: center; flex: 1;">
                        <div style="font-size: 1.2rem; font-weight: bold;">{away['abbr']}</div>
                        <div style="font-size: 1.8rem; font-weight: bold;">{away['score']}</div>
                    </div>
                    <div style="text-align: center; padding: 0 1rem;">
                        <div style="font-size: 1.2rem; color: #718096;">@</div>
                    </div>
                    <div style="text-align: center; flex: 1;">
                        <div style="font-size: 1.2rem; font-weight: bold;">{home['abbr']}</div>
                        <div style="font-size: 1.8rem; font-weight: bold;">{home['score']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.write("")  # Spacing


def render_leaders():
    """Render the statistical leaders page."""
    st.markdown('<h2 class="sub-header">Statistical Leaders</h2>', unsafe_allow_html=True)

    # Stat category selector
    col1, col2 = st.columns([1, 3])
    with col1:
        stat_category = st.selectbox(
            "Category",
            ["points", "rebounds", "assists", "steals", "blocks"],
            format_func=lambda x: x.title()
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
    display_df = df.rename(columns={
        'player_name': 'Player',
        'team_abbr': 'Team',
        'minutes': 'MPG',
        'points': 'PPG',
        'rebounds': 'RPG',
        'assists': 'APG',
        'steals': 'SPG',
        'blocks': 'BPG',
        'turnovers': 'TOV',
        'fg_pct': 'FG%',
        'three_pct': '3P%',
        'ft_pct': 'FT%',
        'plus_minus': '+/-'
    })

    # Select columns based on category
    base_cols = ['Player', 'Team', 'MPG']
    stat_cols = {
        'points': ['PPG', 'FG%', '3P%', 'FT%'],
        'rebounds': ['RPG', 'PPG', 'MPG'],
        'assists': ['APG', 'PPG', 'TOV'],
        'steals': ['SPG', 'PPG', 'MPG'],
        'blocks': ['BPG', 'PPG', 'MPG'],
    }
    cols_to_show = base_cols + stat_cols[stat_category]

    # Display table
    st.dataframe(
        display_df[cols_to_show],
        use_container_width=True,
        hide_index=True
    )

    # Visualization
    st.markdown(f"### Top {num_leaders} in {stat_category.title()}")

    stat_map = {
        'points': 'PPG',
        'rebounds': 'RPG',
        'assists': 'APG',
        'steals': 'SPG',
        'blocks': 'BPG'
    }

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

    # Get teams
    teams = get_teams()

    if not teams:
        st.warning("No team data available.", icon="⚠️")
        return

    # Team selector
    team_options = {f"{t['abbreviation']} - {t['name']}": t['id'] for t in teams}
    selected_team = st.selectbox("Select Team", options=list(team_options.keys()))
    team_id = team_options[selected_team]

    # Get team's recent games
    recent_games = get_recent_games(days=30, team_id=team_id)

    if recent_games:
        st.markdown("### Recent Games")

        # Create games DataFrame
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

        # Display stats
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

        # Display games table
        st.dataframe(
            games_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Result': st.column_config.TextColumn(
                    'Result',
                    width='small',
                )
            }
        )

        # Margin chart
        if len(games_df) > 1:
            st.markdown("### Point Differential Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(games_df))),
                y=games_df['Margin'],
                mode='lines+markers',
                name='Margin',
                line=dict(color='#4299e1'),
                marker=dict(
                    color=['green' if m > 0 else 'red' for m in games_df['Margin']],
                    size=10
                )
            ))
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_layout(
                xaxis_title="Game",
                yaxis_title="Point Margin",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recent games found for this team.", icon="ℹ️")


# Main application
def main():
    """Main application entry point."""
    render_header()
    render_status_widget()

    # Add spacing after header
    st.write("")

    # Route to appropriate page based on session state
    if st.session_state.current_page == "Standings":
        render_standings()
    elif st.session_state.current_page == "Today's Games":
        render_todays_games()
    elif st.session_state.current_page == "Leaders":
        render_leaders()
    elif st.session_state.current_page == "Team Analysis":
        render_team_analysis()


if __name__ == "__main__":
    main()
