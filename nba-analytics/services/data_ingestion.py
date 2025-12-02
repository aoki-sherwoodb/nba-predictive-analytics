"""
Data Ingestion Service for NBA Analytics Platform.
Fetches data from NBA API and stores in PostgreSQL.
"""
import logging
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import json

from nba_api.stats.endpoints import (
    commonteamroster,
    leaguestandings,
    scoreboardv2,
    boxscoretraditionalv2,
    teamgamelog,
    commonplayerinfo,
    playergamelog,
    leaguegamefinder,
)
from nba_api.stats.static import teams as nba_teams
from nba_api.stats.static import players as nba_players
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from config import config
from models.database_models import (
    Team, Player, Game, PlayerGameStats, TeamStanding, IngestionLog
)
from models.database import db_manager
from services.cache import cache_manager

logger = logging.getLogger(__name__)


class NBADataIngestionService:
    """
    Service for ingesting NBA data from the NBA API.
    Handles rate limiting and error recovery.
    """
    
    # Rate limiting: NBA API has strict rate limits
    REQUEST_DELAY = 0.6  # Seconds between API requests
    
    def __init__(self):
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _log_ingestion_start(self, session: Session, ingestion_type: str) -> IngestionLog:
        """Create an ingestion log entry."""
        log = IngestionLog(
            ingestion_type=ingestion_type,
            status="running"
        )
        session.add(log)
        session.flush()
        return log
    
    def _log_ingestion_complete(
        self, 
        session: Session, 
        log: IngestionLog, 
        records: int, 
        error: str = None
    ):
        """Update ingestion log with completion status."""
        log.completed_at = datetime.utcnow()
        log.records_processed = records
        log.status = "success" if error is None else "failed"
        log.error_message = error
    
    def ingest_teams(self) -> int:
        """
        Ingest all NBA teams from static data.
        Returns number of teams ingested.
        """
        logger.info("Starting team ingestion...")
        
        with db_manager.get_session() as session:
            log = self._log_ingestion_start(session, "teams")
            
            try:
                # Get all NBA teams from static data
                all_teams = nba_teams.get_teams()
                count = 0
                
                for team_data in all_teams:
                    # Map conference
                    east_teams = ['BOS', 'BKN', 'NYK', 'PHI', 'TOR', 'CHI', 'CLE', 'DET', 'IND', 'MIL', 'ATL', 'CHA', 'MIA', 'ORL', 'WAS']
                    conference = 'East' if team_data['abbreviation'] in east_teams else 'West'
                    
                    # Upsert team
                    stmt = insert(Team).values(
                        nba_id=team_data['id'],
                        abbreviation=team_data['abbreviation'],
                        name=team_data['nickname'],
                        city=team_data['city'],
                        conference=conference,
                    ).on_conflict_do_update(
                        index_elements=['nba_id'],
                        set_={
                            'abbreviation': team_data['abbreviation'],
                            'name': team_data['nickname'],
                            'city': team_data['city'],
                            'conference': conference,
                            'updated_at': datetime.utcnow()
                        }
                    )
                    session.execute(stmt)
                    count += 1
                
                self._log_ingestion_complete(session, log, count)
                logger.info(f"Ingested {count} teams")
                return count
                
            except Exception as e:
                logger.error(f"Team ingestion failed: {e}")
                self._log_ingestion_complete(session, log, 0, str(e))
                raise
    
    def ingest_team_roster(self, team_id: int, season: str) -> int:
        """
        Ingest roster for a specific team.
        Returns number of players ingested.
        """
        logger.info(f"Ingesting roster for team {team_id}, season {season}")
        
        self._rate_limit()
        
        with db_manager.get_session() as session:
            try:
                # Get team from database
                team = session.query(Team).filter(Team.nba_id == team_id).first()
                if not team:
                    logger.warning(f"Team {team_id} not found in database")
                    return 0
                
                # Fetch roster from API
                roster = commonteamroster.CommonTeamRoster(
                    team_id=team_id,
                    season=season
                )
                roster_data = roster.get_normalized_dict()
                
                count = 0
                for player_data in roster_data.get('CommonTeamRoster', []):
                    # Parse birth date
                    birth_date = None
                    if player_data.get('BIRTH_DATE'):
                        try:
                            birth_date = datetime.strptime(
                                player_data['BIRTH_DATE'], 
                                '%b %d, %Y'
                            ).date()
                        except ValueError:
                            pass
                    
                    # Upsert player
                    stmt = insert(Player).values(
                        nba_id=player_data['PLAYER_ID'],
                        first_name=player_data.get('PLAYER'),
                        last_name='',
                        full_name=player_data.get('PLAYER', ''),
                        team_id=team.id,
                        jersey_number=player_data.get('NUM'),
                        position=player_data.get('POSITION'),
                        height=player_data.get('HEIGHT'),
                        weight=player_data.get('WEIGHT'),
                        birth_date=birth_date,
                        years_pro=player_data.get('EXP'),
                        is_active=True
                    ).on_conflict_do_update(
                        index_elements=['nba_id'],
                        set_={
                            'full_name': player_data.get('PLAYER', ''),
                            'team_id': team.id,
                            'jersey_number': player_data.get('NUM'),
                            'position': player_data.get('POSITION'),
                            'is_active': True,
                            'updated_at': datetime.utcnow()
                        }
                    )
                    session.execute(stmt)
                    count += 1
                
                logger.info(f"Ingested {count} players for team {team_id}")
                return count
                
            except Exception as e:
                logger.error(f"Roster ingestion failed for team {team_id}: {e}")
                raise
    
    def ingest_all_rosters(self, season: str) -> int:
        """Ingest rosters for all teams."""
        logger.info(f"Ingesting all rosters for season {season}")
        
        with db_manager.get_session() as session:
            log = self._log_ingestion_start(session, "players")
            
            try:
                teams = session.query(Team).all()
                total_count = 0
                
                for team in teams:
                    try:
                        count = self.ingest_team_roster(team.nba_id, season)
                        total_count += count
                    except Exception as e:
                        logger.warning(f"Failed to ingest roster for {team.name}: {e}")
                        continue
                
                self._log_ingestion_complete(session, log, total_count)
                logger.info(f"Ingested {total_count} total players")
                return total_count
                
            except Exception as e:
                logger.error(f"All rosters ingestion failed: {e}")
                self._log_ingestion_complete(session, log, 0, str(e))
                raise
    
    def ingest_standings(self, season: str) -> int:
        """
        Ingest current standings for a season.
        Returns number of standings records ingested.
        """
        logger.info(f"Ingesting standings for season {season}")
        
        self._rate_limit()
        
        with db_manager.get_session() as session:
            log = self._log_ingestion_start(session, "standings")
            
            try:
                # Fetch standings from API
                standings = leaguestandings.LeagueStandings(
                    season=season,
                    league_id='00'  # NBA
                )
                standings_data = standings.get_normalized_dict()
                
                count = 0
                standings_list = []
                
                for row in standings_data.get('Standings', []):
                    team_id = row['TeamID']
                    
                    # Get team from database
                    team = session.query(Team).filter(Team.nba_id == team_id).first()
                    if not team:
                        logger.warning(f"Team {team_id} not found, skipping standings")
                        continue
                    
                    # Parse streak
                    streak_str = None
                    if row.get('strCurrentStreak'):
                        streak_str = row['strCurrentStreak']
                    
                    # Parse last 10
                    last_10 = None
                    if row.get('L10'):
                        last_10 = row['L10']
                    
                    # Upsert standing
                    stmt = insert(TeamStanding).values(
                        team_id=team.id,
                        season=season,
                        wins=row.get('WINS', 0),
                        losses=row.get('LOSSES', 0),
                        win_percentage=row.get('WinPCT', 0.0),
                        conference_rank=row.get('PlayoffRank'),
                        games_back=row.get('ConferenceGamesBack', 0.0),
                        current_streak=streak_str,
                        last_10=last_10,
                        home_wins=row.get('HOME').split('-')[0] if row.get('HOME') else 0,
                        home_losses=row.get('HOME').split('-')[1] if row.get('HOME') else 0,
                        away_wins=row.get('ROAD').split('-')[0] if row.get('ROAD') else 0,
                        away_losses=row.get('ROAD').split('-')[1] if row.get('ROAD') else 0,
                    ).on_conflict_do_update(
                        constraint='uq_team_season_standing',
                        set_={
                            'wins': row.get('WINS', 0),
                            'losses': row.get('LOSSES', 0),
                            'win_percentage': row.get('WinPCT', 0.0),
                            'conference_rank': row.get('PlayoffRank'),
                            'games_back': row.get('ConferenceGamesBack', 0.0),
                            'current_streak': streak_str,
                            'last_10': last_10,
                            'updated_at': datetime.utcnow()
                        }
                    )
                    session.execute(stmt)
                    
                    # Build cache data
                    standings_list.append({
                        'team_id': team.id,
                        'team_name': team.name,
                        'team_abbr': team.abbreviation,
                        'conference': team.conference,
                        'wins': row.get('WINS', 0),
                        'losses': row.get('LOSSES', 0),
                        'win_pct': row.get('WinPCT', 0.0),
                        'conf_rank': row.get('PlayoffRank'),
                        'games_back': row.get('ConferenceGamesBack', 0.0),
                        'streak': streak_str,
                        'last_10': last_10,
                    })
                    count += 1
                
                # Update cache
                cache_manager.set_standings(season, {
                    'season': season,
                    'updated_at': datetime.utcnow().isoformat(),
                    'standings': standings_list
                })
                
                self._log_ingestion_complete(session, log, count)
                logger.info(f"Ingested {count} standings records")
                return count
                
            except Exception as e:
                logger.error(f"Standings ingestion failed: {e}")
                self._log_ingestion_complete(session, log, 0, str(e))
                raise
    
    def ingest_todays_games(self) -> int:
        """
        Ingest today's games from scoreboard.
        Returns number of games ingested.
        """
        logger.info("Ingesting today's games...")
        
        self._rate_limit()
        
        with db_manager.get_session() as session:
            log = self._log_ingestion_start(session, "games_today")
            
            try:
                # Fetch today's scoreboard
                # Note: The NBA API has a known bug where WinProbability field is sometimes missing
                # This causes the ScoreboardV2 constructor to fail during load_response()
                try:
                    scoreboard = scoreboardv2.ScoreboardV2(
                        game_date=date.today().strftime('%Y-%m-%d'),
                        league_id='00'
                    )
                    scoreboard_data = scoreboard.get_normalized_dict()
                except KeyError as ke:
                    # The NBA API library failed during initialization due to missing field
                    logger.warning(f"NBA API library bug: missing field '{ke}' in response. This is a known issue with the nba_api library.")
                    logger.info("Today's games ingestion skipped due to NBA API library limitation.")
                    logger.info("Workaround: The library needs to be patched or wait for NBA to fix their API response.")
                    self._log_ingestion_complete(session, log, 0, f"NBA API bug: missing {ke}")
                    return 0

                logger.debug(f"Scoreboard data keys: {scoreboard_data.keys()}")
                game_headers = scoreboard_data.get('GameHeader', [])
                logger.info(f"Found {len(game_headers)} games for today")

                if len(game_headers) == 0:
                    logger.info("No games scheduled for today")
                    self._log_ingestion_complete(session, log, 0)
                    return 0

                count = 0
                games_list = []

                for game_data in game_headers:
                    game_id = game_data.get('GAME_ID')
                    if not game_id:
                        logger.warning("Game data missing GAME_ID, skipping")
                        continue

                    # Get teams
                    home_team_id = game_data.get('HOME_TEAM_ID')
                    away_team_id = game_data.get('VISITOR_TEAM_ID')

                    if not home_team_id or not away_team_id:
                        logger.warning(f"Game {game_id} missing team IDs, skipping")
                        continue

                    home_team = session.query(Team).filter(
                        Team.nba_id == home_team_id
                    ).first()
                    away_team = session.query(Team).filter(
                        Team.nba_id == away_team_id
                    ).first()
                    
                    if not home_team or not away_team:
                        logger.warning(f"Teams not found for game {game_id}")
                        continue
                    
                    # Parse game status
                    status_code = game_data.get('GAME_STATUS_ID', 1)
                    status = 'scheduled'
                    if status_code == 2:
                        status = 'live'
                    elif status_code == 3:
                        status = 'final'
                    
                    # Get scores from line score data
                    home_score = 0
                    away_score = 0
                    for line in scoreboard_data.get('LineScore', []):
                        line_game_id = line.get('GAME_ID')
                        line_team_id = line.get('TEAM_ID')

                        if line_game_id == game_id and line_team_id:
                            if line_team_id == home_team_id:
                                home_score = line.get('PTS', 0) or 0
                            elif line_team_id == away_team_id:
                                away_score = line.get('PTS', 0) or 0
                    
                    # Upsert game
                    stmt = insert(Game).values(
                        nba_game_id=game_id,
                        season=config.ingestion.current_season,
                        season_type='Regular Season',
                        game_date=date.today(),
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        home_score=home_score,
                        away_score=away_score,
                        status=status,
                        period=game_data.get('LIVE_PERIOD'),
                        game_clock=game_data.get('LIVE_PC_TIME'),
                    ).on_conflict_do_update(
                        index_elements=['nba_game_id'],
                        set_={
                            'home_score': home_score,
                            'away_score': away_score,
                            'status': status,
                            'period': game_data.get('LIVE_PERIOD'),
                            'game_clock': game_data.get('LIVE_PC_TIME'),
                            'updated_at': datetime.utcnow()
                        }
                    )
                    session.execute(stmt)
                    
                    # Build cache data
                    games_list.append({
                        'game_id': game_id,
                        'home_team': {
                            'id': home_team.id,
                            'name': home_team.name,
                            'abbr': home_team.abbreviation,
                            'score': home_score
                        },
                        'away_team': {
                            'id': away_team.id,
                            'name': away_team.name,
                            'abbr': away_team.abbreviation,
                            'score': away_score
                        },
                        'status': status,
                        'period': game_data.get('LIVE_PERIOD'),
                        'clock': game_data.get('LIVE_PC_TIME'),
                    })
                    count += 1
                
                # Update cache
                cache_manager.set_todays_games(games_list)
                
                self._log_ingestion_complete(session, log, count)
                logger.info(f"Ingested {count} games for today")
                return count
                
            except Exception as e:
                logger.error(f"Today's games ingestion failed: {e}", exc_info=True)
                self._log_ingestion_complete(session, log, 0, str(e))
                # Don't raise - continue with ingestion even if no games today
                return 0
    
    def ingest_game_box_score(self, game_id: str) -> int:
        """
        Ingest box score statistics for a completed game.
        Returns number of player stats records ingested.
        """
        logger.info(f"Ingesting box score for game {game_id}")
        
        self._rate_limit()
        
        with db_manager.get_session() as session:
            try:
                # Fetch box score from API
                box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(
                    game_id=game_id
                )
                box_data = box_score.get_normalized_dict()
                
                # Get game from database
                game = session.query(Game).filter(Game.nba_game_id == game_id).first()
                if not game:
                    logger.warning(f"Game {game_id} not found in database")
                    return 0
                
                count = 0
                for player_data in box_data.get('PlayerStats', []):
                    # Get or create player
                    player = session.query(Player).filter(
                        Player.nba_id == player_data['PLAYER_ID']
                    ).first()
                    
                    if not player:
                        # Create player if not exists
                        team = session.query(Team).filter(
                            Team.nba_id == player_data['TEAM_ID']
                        ).first()
                        if not team:
                            continue
                        
                        player = Player(
                            nba_id=player_data['PLAYER_ID'],
                            full_name=player_data.get('PLAYER_NAME', ''),
                            team_id=team.id,
                            is_active=True
                        )
                        session.add(player)
                        session.flush()
                    
                    # Get team
                    team = session.query(Team).filter(
                        Team.nba_id == player_data['TEAM_ID']
                    ).first()
                    if not team:
                        continue
                    
                    # Parse minutes
                    minutes = 0.0
                    if player_data.get('MIN'):
                        try:
                            min_parts = str(player_data['MIN']).split(':')
                            minutes = float(min_parts[0]) + float(min_parts[1]) / 60 if len(min_parts) > 1 else float(min_parts[0])
                        except:
                            pass
                    
                    # Upsert player game stats
                    stmt = insert(PlayerGameStats).values(
                        player_id=player.id,
                        game_id=game.id,
                        team_id=team.id,
                        minutes_played=minutes,
                        points=player_data.get('PTS', 0) or 0,
                        field_goals_made=player_data.get('FGM', 0) or 0,
                        field_goals_attempted=player_data.get('FGA', 0) or 0,
                        three_pointers_made=player_data.get('FG3M', 0) or 0,
                        three_pointers_attempted=player_data.get('FG3A', 0) or 0,
                        free_throws_made=player_data.get('FTM', 0) or 0,
                        free_throws_attempted=player_data.get('FTA', 0) or 0,
                        offensive_rebounds=player_data.get('OREB', 0) or 0,
                        defensive_rebounds=player_data.get('DREB', 0) or 0,
                        total_rebounds=player_data.get('REB', 0) or 0,
                        assists=player_data.get('AST', 0) or 0,
                        steals=player_data.get('STL', 0) or 0,
                        blocks=player_data.get('BLK', 0) or 0,
                        turnovers=player_data.get('TO', 0) or 0,
                        personal_fouls=player_data.get('PF', 0) or 0,
                        plus_minus=player_data.get('PLUS_MINUS', 0) or 0,
                    ).on_conflict_do_update(
                        constraint='uq_player_game',
                        set_={
                            'minutes_played': minutes,
                            'points': player_data.get('PTS', 0) or 0,
                            'field_goals_made': player_data.get('FGM', 0) or 0,
                            'field_goals_attempted': player_data.get('FGA', 0) or 0,
                            'three_pointers_made': player_data.get('FG3M', 0) or 0,
                            'three_pointers_attempted': player_data.get('FG3A', 0) or 0,
                            'free_throws_made': player_data.get('FTM', 0) or 0,
                            'free_throws_attempted': player_data.get('FTA', 0) or 0,
                            'total_rebounds': player_data.get('REB', 0) or 0,
                            'assists': player_data.get('AST', 0) or 0,
                            'steals': player_data.get('STL', 0) or 0,
                            'blocks': player_data.get('BLK', 0) or 0,
                            'turnovers': player_data.get('TO', 0) or 0,
                            'plus_minus': player_data.get('PLUS_MINUS', 0) or 0,
                            'updated_at': datetime.utcnow()
                        }
                    )
                    session.execute(stmt)
                    count += 1
                
                logger.info(f"Ingested {count} player stats for game {game_id}")
                return count
                
            except Exception as e:
                logger.error(f"Box score ingestion failed for game {game_id}: {e}")
                raise
    
    def run_full_ingestion(self, season: str = None):
        """
        Run a full data ingestion cycle.
        """
        season = season or config.ingestion.current_season
        logger.info(f"Starting full ingestion for season {season}")
        
        # 1. Ingest teams
        self.ingest_teams()
        
        # 2. Ingest standings
        self.ingest_standings(season)
        
        # 3. Ingest rosters
        self.ingest_all_rosters(season)
        
        # 4. Ingest today's games
        self.ingest_todays_games()
        
        logger.info("Full ingestion complete!")


# Create global instance
ingestion_service = NBADataIngestionService()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run full ingestion
    from models.database import init_database
    init_database()
    
    ingestion_service.run_full_ingestion()
