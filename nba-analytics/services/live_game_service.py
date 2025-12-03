"""
Live Game Service for NBA Analytics Platform.
Fetches real-time game data including play-by-play and shot charts from NBA API.
"""
import logging
import time
from datetime import datetime, date
from typing import List, Dict, Optional, Any

from nba_api.live.nba.endpoints import scoreboard as live_scoreboard
from nba_api.live.nba.endpoints import boxscore as live_boxscore
from nba_api.live.nba.endpoints import playbyplay as live_playbyplay
from nba_api.stats.endpoints import (
    scoreboardv2,
    playbyplayv2,
    shotchartdetail,
    boxscoretraditionalv2,
)
from nba_api.stats.static import teams as nba_teams

logger = logging.getLogger(__name__)


class LiveGameService:
    """
    Service for fetching real-time NBA game data.
    Provides play-by-play events, shot chart locations, and live scores.
    """

    REQUEST_DELAY = 0.6  # Seconds between API requests

    def __init__(self):
        self.last_request_time = 0
        self._team_lookup = {t['id']: t for t in nba_teams.get_teams()}

    def _rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def _get_team_abbr(self, team_id: int) -> str:
        """Get team abbreviation from team ID."""
        team = self._team_lookup.get(team_id)
        return team['abbreviation'] if team else 'UNK'

    def _get_team_name(self, team_id: int) -> str:
        """Get team name from team ID."""
        team = self._team_lookup.get(team_id)
        return team['full_name'] if team else 'Unknown'

    def get_live_games(self) -> List[Dict]:
        """
        Get all currently live games from today's scoreboard.
        Uses the live NBA API for real-time data.
        Returns list of games with their current status.
        """
        try:
            self._rate_limit()
            # Use the live scoreboard API
            board = live_scoreboard.ScoreBoard()
            scoreboard_data = board.get_dict()

            games = []
            games_data = scoreboard_data.get('scoreboard', {}).get('games', [])

            for game in games_data:
                game_id = game.get('gameId', '')
                game_status = game.get('gameStatusText', '')
                game_status_id = game.get('gameStatus', 1)  # 1=scheduled, 2=in progress, 3=final

                home_team = game.get('homeTeam', {})
                away_team = game.get('awayTeam', {})

                home_score = home_team.get('score', 0) or 0
                away_score = away_team.get('score', 0) or 0

                # Determine if game is live (status 2 = In Progress)
                is_live = game_status_id == 2

                # Get period info
                period = game.get('period', 0)
                game_clock = game.get('gameClock', '')

                games.append({
                    'game_id': game_id,
                    'home_team_id': home_team.get('teamId', 0),
                    'away_team_id': away_team.get('teamId', 0),
                    'home_team_abbr': home_team.get('teamTricode', 'UNK'),
                    'away_team_abbr': away_team.get('teamTricode', 'UNK'),
                    'home_team_name': home_team.get('teamName', 'Unknown'),
                    'away_team_name': away_team.get('teamName', 'Unknown'),
                    'home_score': int(home_score) if home_score else 0,
                    'away_score': int(away_score) if away_score else 0,
                    'status': game_status,
                    'status_id': game_status_id,
                    'is_live': is_live,
                    'period': period,
                    'game_clock': game_clock,
                    'start_time': game.get('gameTimeUTC', ''),
                })

            return games

        except Exception as e:
            logger.error(f"Error fetching live games: {e}")
            return []

    def get_play_by_play(self, game_id: str, last_event_id: int = 0) -> List[Dict]:
        """
        Fetch play-by-play events for a specific game using the live API.

        Args:
            game_id: NBA game ID (e.g., "0022400123")
            last_event_id: Only return events after this ID (for incremental fetching)

        Returns:
            List of play events with details
        """
        try:
            self._rate_limit()
            # Use the live play-by-play API
            pbp = live_playbyplay.PlayByPlay(game_id)
            pbp_data = pbp.get_dict()

            plays = []
            actions = pbp_data.get('game', {}).get('actions', [])

            for action in actions:
                event_id = action.get('actionNumber', 0)

                # Skip events we've already seen
                if event_id <= last_event_id:
                    continue

                # Get event type from actionType
                action_type = action.get('actionType', 'other').upper()
                event_type = self._map_live_action_type(action_type)

                # Get description
                description = action.get('description', '')

                # Get team info
                team_tricode = action.get('teamTricode', '')

                # Get player name
                player_name = action.get('playerNameI', '') or action.get('playerName', '')

                # Get scores
                score_home = action.get('scoreHome', '0')
                score_away = action.get('scoreAway', '0')

                # Check if shot was made
                shot_made = None
                if action_type in ['2PT', '3PT', 'SHOT']:
                    shot_made = action.get('shotResult') == 'Made'

                # Get period and clock
                period = action.get('period', 1)
                clock = action.get('clock', '')

                plays.append({
                    'event_id': event_id,
                    'period': period,
                    'clock': clock,
                    'event_type': event_type,
                    'description': description,
                    'player_name': player_name,
                    'team_abbr': team_tricode,
                    'home_score': int(score_home) if score_home else 0,
                    'away_score': int(score_away) if score_away else 0,
                    'shot_made': shot_made,
                })

            return plays

        except Exception as e:
            logger.error(f"Error fetching play-by-play for game {game_id}: {e}")
            return []

    def _map_live_action_type(self, action_type: str) -> str:
        """Map live API action types to our standard event types."""
        type_mapping = {
            '2PT': 'SHOT_MADE',
            '3PT': 'SHOT_MADE',
            'MISS': 'SHOT_MISSED',
            'REBOUND': 'REBOUND',
            'TURNOVER': 'TURNOVER',
            'FOUL': 'FOUL',
            'FREETHROW': 'FREE_THROW',
            'FREE_THROW': 'FREE_THROW',
            'SUBSTITUTION': 'SUBSTITUTION',
            'TIMEOUT': 'TIMEOUT',
            'JUMPBALL': 'JUMP_BALL',
            'VIOLATION': 'VIOLATION',
            'PERIOD': 'PERIOD_BEGIN',
            'GAME': 'OTHER',
            'STEAL': 'STEAL',
            'BLOCK': 'BLOCK',
            'ASSIST': 'ASSIST',
        }
        return type_mapping.get(action_type, 'OTHER')

    def _get_event_type(self, event_msg_type: int) -> str:
        """Convert NBA event message type to readable string."""
        event_types = {
            1: 'SHOT_MADE',
            2: 'SHOT_MISSED',
            3: 'FREE_THROW',
            4: 'REBOUND',
            5: 'TURNOVER',
            6: 'FOUL',
            7: 'VIOLATION',
            8: 'SUBSTITUTION',
            9: 'TIMEOUT',
            10: 'JUMP_BALL',
            11: 'EJECTION',
            12: 'PERIOD_BEGIN',
            13: 'PERIOD_END',
        }
        return event_types.get(event_msg_type, 'OTHER')

    def get_shot_chart(self, game_id: str, team_id: int = 0) -> List[Dict]:
        """
        Fetch shot chart data for a specific game using the live play-by-play API.
        Extracts shot locations from play-by-play actions.

        Args:
            game_id: NBA game ID
            team_id: Optional team ID to filter shots (0 = all teams)

        Returns:
            List of shot locations with details
        """
        try:
            self._rate_limit()

            # Use the live play-by-play API which includes shot coordinates
            pbp = live_playbyplay.PlayByPlay(game_id)
            pbp_data = pbp.get_dict()

            shots = []
            actions = pbp_data.get('game', {}).get('actions', [])

            for action in actions:
                # Only process field goal attempts
                if not action.get('isFieldGoal'):
                    continue

                action_type = action.get('actionType', '')
                team_action_id = action.get('teamId', 0)

                # Filter by team if specified
                if team_id and team_action_id != team_id:
                    continue

                # Get legacy coordinates (in 10ths of feet, like the stats API)
                x = action.get('xLegacy', 0)
                y = action.get('yLegacy', 0)

                # Determine if shot was made
                shot_result = action.get('shotResult', '')
                made = shot_result == 'Made'

                # Get shot type
                shot_type = '3PT' if action_type == '3pt' else '2PT'

                shots.append({
                    'x': x,
                    'y': y,
                    'player_id': action.get('personId', 0),
                    'player_name': action.get('playerNameI', '') or action.get('playerName', ''),
                    'team_id': team_action_id,
                    'team_abbr': action.get('teamTricode', ''),
                    'shot_type': shot_type,
                    'made': made,
                    'distance': int(action.get('shotDistance', 0) or 0),
                    'zone': action.get('area', 'Unknown'),
                    'action_type': action.get('subType', ''),
                    'period': action.get('period', 1),
                    'clock': action.get('clock', ''),
                })

            return shots

        except Exception as e:
            logger.error(f"Error fetching shot chart for game {game_id}: {e}")
            return []

    def get_live_box_score(self, game_id: str) -> Dict:
        """
        Fetch current box score for a game using the live API.

        Args:
            game_id: NBA game ID

        Returns:
            Dictionary with player stats for both teams
        """
        try:
            self._rate_limit()
            # Use the live box score API
            box = live_boxscore.BoxScore(game_id)
            box_data = box.get_dict()

            player_stats = []
            team_stats = []

            game_data = box_data.get('game', {})
            home_team = game_data.get('homeTeam', {})
            away_team = game_data.get('awayTeam', {})

            # Process both teams' players
            for team_data_item in [home_team, away_team]:
                team_abbr = team_data_item.get('teamTricode', '')
                team_id = team_data_item.get('teamId', 0)
                players = team_data_item.get('players', [])

                for player in players:
                    stats = player.get('statistics', {})
                    player_stats.append({
                        'player_id': player.get('personId', 0),
                        'player_name': player.get('name', ''),
                        'team_id': team_id,
                        'team_abbr': team_abbr,
                        'minutes': stats.get('minutesCalculated', '0:00') or stats.get('minutes', '0:00'),
                        'points': stats.get('points', 0) or 0,
                        'rebounds': stats.get('reboundsTotal', 0) or 0,
                        'assists': stats.get('assists', 0) or 0,
                        'steals': stats.get('steals', 0) or 0,
                        'blocks': stats.get('blocks', 0) or 0,
                        'turnovers': stats.get('turnovers', 0) or 0,
                        'fg_made': stats.get('fieldGoalsMade', 0) or 0,
                        'fg_attempted': stats.get('fieldGoalsAttempted', 0) or 0,
                        'fg_pct': stats.get('fieldGoalsPercentage', 0) or 0,
                        'three_made': stats.get('threePointersMade', 0) or 0,
                        'three_attempted': stats.get('threePointersAttempted', 0) or 0,
                        'plus_minus': stats.get('plusMinusPoints', 0) or 0,
                    })

                # Team totals
                team_totals = team_data_item.get('statistics', {})
                team_stats.append({
                    'team_id': team_id,
                    'team_abbr': team_abbr,
                    'points': team_totals.get('points', 0) or 0,
                    'rebounds': team_totals.get('reboundsTotal', 0) or 0,
                    'assists': team_totals.get('assists', 0) or 0,
                    'fg_pct': team_totals.get('fieldGoalsPercentage', 0) or 0,
                    'three_pct': team_totals.get('threePointersPercentage', 0) or 0,
                })

            return {
                'player_stats': player_stats,
                'team_stats': team_stats,
            }

        except Exception as e:
            logger.error(f"Error fetching box score for game {game_id}: {e}")
            return {'player_stats': [], 'team_stats': []}

    def get_upcoming_games(self) -> List[Dict]:
        """
        Get upcoming/scheduled games for today.
        Returns games that haven't started yet.
        """
        all_games = self.get_live_games()
        return [g for g in all_games if g['status_id'] == 1]  # status_id 1 = Scheduled

    def get_live_game_data(self, game_id: str) -> Dict:
        """
        Get comprehensive live data for a specific game.
        Combines plays, shots, and box score.

        Args:
            game_id: NBA game ID

        Returns:
            Dictionary with all game data
        """
        # Get all live games to find this game's info
        all_games = self.get_live_games()
        game_info = next((g for g in all_games if g['game_id'] == game_id), None)

        # Fetch all data
        plays = self.get_play_by_play(game_id)
        shots = self.get_shot_chart(game_id)
        box_score = self.get_live_box_score(game_id)

        return {
            'game_info': game_info,
            'plays': plays,
            'shots': shots,
            'box_score': box_score,
        }


# Create global instance
live_game_service = LiveGameService()
