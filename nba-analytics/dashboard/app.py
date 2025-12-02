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

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="NBA Analytics Dashboard",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2C5282;
        margin-top: 1rem;
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
        st.error(f"API Error: {e}")
        return None


def api_post(endpoint: str):
    """Make POST request to API."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
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
    health = api_get("/health")
    return health and health.get("status") in ["healthy", "degraded"]


# Dashboard components
def render_header():
    """Render the main header."""
    st.markdown('<h1 class="main-header">🏀 NBA Analytics Dashboard</h1>', unsafe_allow_html=True)
    
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
            ["📊 Standings", "🎮 Today's Games", "🏆 Leaders", "📈 Team Analysis"],
            label_visibility="collapsed"
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
    st.markdown('<h2 class="sub-header">Conference Standings</h2>', unsafe_allow_html=True)
    
    standings = get_standings()
    
    if not standings:
        st.warning("No standings data available. Try refreshing.")
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
        st.info("No games scheduled for today.")
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
        st.warning("No statistical data available.")
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
        st.warning("No team data available.")
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
        st.info("No recent games found for this team.")


# Main application
def main():
    """Main application entry point."""
    render_header()
    page = render_sidebar()
    
    if page == "📊 Standings":
        render_standings()
    elif page == "🎮 Today's Games":
        render_todays_games()
    elif page == "🏆 Leaders":
        render_leaders()
    elif page == "📈 Team Analysis":
        render_team_analysis()


if __name__ == "__main__":
    main()
