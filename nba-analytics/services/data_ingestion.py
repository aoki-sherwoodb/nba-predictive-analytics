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
    boxscoretraditionalv3,
    teamgamelog,
    commonplayerinfo,
    playergamelog,
    leaguegamefinder,
)
from nba_api.live.nba.endpoints import scoreboard as scoreboard_live
from nba_api.live.nba.endpoints import boxscore as boxscore_live
from nba_api.stats.static import teams as nba_teams
from nba_api.stats.static import players as nba_players
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from config import config
from models.database_models import (
    Team,
    Player,
    Game,
    PlayerGameStats,
    TeamStanding,
    IngestionLog,
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

    def _log_ingestion_start(
        self, session: Session, ingestion_type: str
    ) -> IngestionLog:
        """Create an ingestion log entry."""
        log = IngestionLog(ingestion_type=ingestion_type, status="running")
        session.add(log)
        session.flush()
        return log

    def _log_ingestion_complete(
        self, session: Session, log: IngestionLog, records: int, error: str = None
    ):
        """Update ingestion log with completion status."""
        log.completed_at = datetime.utcnow()
        log.records_processed = records
        log.status = "success" if error is None else "failed"
        log.error_message = error

    def _parse_game_clock(self, clock_str: str) -> str:
        """
        Parse ISO 8601 duration format to MM:SS format.
        Example: 'PT11M58.00S' -> '11:58'
        """
        if not clock_str or not isinstance(clock_str, str):
            return "     "  # 5 spaces for empty clock

        try:
            # Remove 'PT' prefix and split by 'M' and 'S'
            if clock_str.startswith('PT'):
                clock_str = clock_str[2:]  # Remove 'PT'

            minutes = 0
            seconds = 0

            if 'M' in clock_str:
                parts = clock_str.split('M')
                minutes = int(parts[0])
                if len(parts) > 1 and parts[1]:
                    # Get seconds part (remove 'S' if present)
                    sec_str = parts[1].replace('S', '').strip()
                    if sec_str:
                        seconds = int(float(sec_str))
            elif 'S' in clock_str:
                # Only seconds, no minutes
                sec_str = clock_str.replace('S', '').strip()
                if sec_str:
                    seconds = int(float(sec_str))

            return f"{minutes:02d}:{seconds:02d}"
        except Exception:
            return "     "  # Return empty clock on parse error

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
                    east_teams = [
                        "BOS",
                        "BKN",
                        "NYK",
                        "PHI",
                        "TOR",
                        "CHI",
                        "CLE",
                        "DET",
                        "IND",
                        "MIL",
                        "ATL",
                        "CHA",
                        "MIA",
                        "ORL",
                        "WAS",
                    ]
                    conference = (
                        "East" if team_data["abbreviation"] in east_teams else "West"
                    )

                    # Upsert team
                    stmt = (
                        insert(Team)
                        .values(
                            nba_id=team_data["id"],
                            abbreviation=team_data["abbreviation"],
                            name=team_data["nickname"],
                            city=team_data["city"],
                            conference=conference,
                        )
                        .on_conflict_do_update(
                            index_elements=["nba_id"],
                            set_={
                                "abbreviation": team_data["abbreviation"],
                                "name": team_data["nickname"],
                                "city": team_data["city"],
                                "conference": conference,
                                "updated_at": datetime.utcnow(),
                            },
                        )
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
                    team_id=team_id, season=season
                )
                roster_data = roster.get_normalized_dict()

                count = 0
                for player_data in roster_data.get("CommonTeamRoster", []):
                    # Parse birth date
                    birth_date = None
                    if player_data.get("BIRTH_DATE"):
                        try:
                            birth_date = datetime.strptime(
                                player_data["BIRTH_DATE"], "%b %d, %Y"
                            ).date()
                        except ValueError:
                            pass

                    # Parse years_pro - convert 'R' (rookie) to 0
                    years_pro_raw = player_data.get("EXP")
                    if years_pro_raw == 'R':
                        years_pro = 0
                    elif years_pro_raw:
                        try:
                            years_pro = int(years_pro_raw)
                        except (ValueError, TypeError):
                            years_pro = 0
                    else:
                        years_pro = 0

                    # Upsert player
                    stmt = (
                        insert(Player)
                        .values(
                            nba_id=player_data["PLAYER_ID"],
                            first_name=player_data.get("PLAYER"),
                            last_name="",
                            full_name=player_data.get("PLAYER", ""),
                            team_id=team.id,
                            jersey_number=player_data.get("NUM"),
                            position=player_data.get("POSITION"),
                            height=player_data.get("HEIGHT"),
                            weight=player_data.get("WEIGHT"),
                            birth_date=birth_date,
                            years_pro=years_pro,
                            is_active=True,
                        )
                        .on_conflict_do_update(
                            index_elements=["nba_id"],
                            set_={
                                "full_name": player_data.get("PLAYER", ""),
                                "team_id": team.id,
                                "jersey_number": player_data.get("NUM"),
                                "position": player_data.get("POSITION"),
                                "is_active": True,
                                "updated_at": datetime.utcnow(),
                            },
                        )
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
                    season=season, league_id="00"  # NBA
                )
                standings_data = standings.get_normalized_dict()

                count = 0
                standings_list = []

                for row in standings_data.get("Standings", []):
                    team_id = row["TeamID"]

                    # Get team from database
                    team = session.query(Team).filter(Team.nba_id == team_id).first()
                    if not team:
                        logger.warning(f"Team {team_id} not found, skipping standings")
                        continue

                    # Parse streak
                    streak_str = None
                    if row.get("strCurrentStreak"):
                        streak_str = row["strCurrentStreak"]

                    # Parse last 10
                    last_10 = None
                    if row.get("L10"):
                        last_10 = row["L10"]

                    # Upsert standing
                    stmt = (
                        insert(TeamStanding)
                        .values(
                            team_id=team.id,
                            season=season,
                            wins=row.get("WINS", 0),
                            losses=row.get("LOSSES", 0),
                            win_percentage=row.get("WinPCT", 0.0),
                            conference_rank=row.get("PlayoffRank"),
                            games_back=row.get("ConferenceGamesBack", 0.0),
                            current_streak=streak_str,
                            last_10=last_10,
                            home_wins=(
                                row.get("HOME").split("-")[0] if row.get("HOME") else 0
                            ),
                            home_losses=(
                                row.get("HOME").split("-")[1] if row.get("HOME") else 0
                            ),
                            away_wins=(
                                row.get("ROAD").split("-")[0] if row.get("ROAD") else 0
                            ),
                            away_losses=(
                                row.get("ROAD").split("-")[1] if row.get("ROAD") else 0
                            ),
                        )
                        .on_conflict_do_update(
                            constraint="uq_team_season_standing",
                            set_={
                                "wins": row.get("WINS", 0),
                                "losses": row.get("LOSSES", 0),
                                "win_percentage": row.get("WinPCT", 0.0),
                                "conference_rank": row.get("PlayoffRank"),
                                "games_back": row.get("ConferenceGamesBack", 0.0),
                                "current_streak": streak_str,
                                "last_10": last_10,
                                "updated_at": datetime.utcnow(),
                            },
                        )
                    )
                    session.execute(stmt)

                    # Build cache data
                    standings_list.append(
                        {
                            "team_id": team.id,
                            "team_name": team.name,
                            "team_abbr": team.abbreviation,
                            "conference": team.conference,
                            "wins": row.get("WINS", 0),
                            "losses": row.get("LOSSES", 0),
                            "win_pct": row.get("WinPCT", 0.0),
                            "conf_rank": row.get("PlayoffRank"),
                            "games_back": row.get("ConferenceGamesBack", 0.0),
                            "streak": streak_str,
                            "last_10": last_10,
                        }
                    )
                    count += 1

                # Update cache
                cache_manager.set_standings(
                    season,
                    {
                        "season": season,
                        "updated_at": datetime.utcnow().isoformat(),
                        "standings": standings_list,
                    },
                )

                self._log_ingestion_complete(session, log, count)
                logger.info(f"Ingested {count} standings records")
                return count

            except Exception as e:
                logger.error(f"Standings ingestion failed: {e}")
                self._log_ingestion_complete(session, log, 0, str(e))
                raise

    def ingest_todays_games(self) -> int:
        """
        Ingest today's games from live.nba scoreboard.
        Returns number of games ingested.
        """
        logger.info("Ingesting today's games...")

        self._rate_limit()

        with db_manager.get_session() as session:
            log = self._log_ingestion_start(session, "games_today")

            try:
                # Fetch today's scoreboard using live.nba endpoint
                scoreboard_obj = scoreboard_live.ScoreBoard()
                live_data = scoreboard_obj.get_dict()

                games = live_data.get('scoreboard', {}).get('games', [])
                logger.info(f"Found {len(games)} games for today")

                if len(games) == 0:
                    logger.info("No games scheduled for today")
                    self._log_ingestion_complete(session, log, 0)
                    return 0

                count = 0
                games_list = []

                for game_data in games:
                    game_id = game_data.get('gameId')
                    if not game_id:
                        logger.warning("Game data missing gameId, skipping")
                        continue

                    # Get team data
                    home_team_data = game_data.get('homeTeam', {})
                    away_team_data = game_data.get('awayTeam', {})

                    home_team_id = home_team_data.get('teamId')
                    away_team_id = away_team_data.get('teamId')

                    if not home_team_id or not away_team_id:
                        logger.warning(f"Game {game_id} missing team IDs, skipping")
                        continue

                    home_team = (
                        session.query(Team).filter(Team.nba_id == home_team_id).first()
                    )
                    away_team = (
                        session.query(Team).filter(Team.nba_id == away_team_id).first()
                    )

                    if not home_team or not away_team:
                        logger.warning(f"Teams not found for game {game_id}")
                        continue

                    # Parse game status (live.nba format: 1=scheduled, 2=live, 3=final)
                    status_code = game_data.get('gameStatus', 1)
                    status = 'scheduled'
                    if status_code == 2:
                        status = 'live'
                    elif status_code == 3:
                        status = 'final'

                    # Get scores directly from live.nba format
                    home_score = home_team_data.get('score', 0) or 0
                    away_score = away_team_data.get('score', 0) or 0

                    # Upsert game
                    stmt = (
                        insert(Game)
                        .values(
                            nba_game_id=game_id,
                            season=config.ingestion.current_season,
                            season_type='Regular Season',
                            game_date=date.today(),
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            home_score=home_score,
                            away_score=away_score,
                            status=status,
                            period=game_data.get('period'),
                            game_clock=self._parse_game_clock(game_data.get('gameClock')),
                        )
                        .on_conflict_do_update(
                            index_elements=['nba_game_id'],
                            set_={
                                'home_score': home_score,
                                'away_score': away_score,
                                'status': status,
                                'period': game_data.get('period'),
                                'game_clock': self._parse_game_clock(game_data.get('gameClock')),
                                'updated_at': datetime.utcnow(),
                            },
                        )
                    )
                    session.execute(stmt)

                    # Build cache data
                    games_list.append(
                        {
                            'game_id': game_id,
                            'home_team': {
                                'id': home_team.id,
                                'name': home_team.name,
                                'abbr': home_team.abbreviation,
                                'score': home_score,
                            },
                            'away_team': {
                                'id': away_team.id,
                                'name': away_team.name,
                                'abbr': away_team.abbreviation,
                                'score': away_score,
                            },
                            'status': status,
                            'period': game_data.get('period'),
                            'clock': self._parse_game_clock(game_data.get('gameClock')),
                            'game_date': str(date.today()),
                        }
                    )
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
                # Fetch box score from v3 API
                box_score = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
                player_stats_df = box_score.get_data_frames()[0]

                # Get game from database
                game = session.query(Game).filter(Game.nba_game_id == game_id).first()
                if not game:
                    logger.warning(f"Game {game_id} not found in database")
                    return 0

                if player_stats_df.empty:
                    logger.warning(f"No player stats found for game {game_id}")
                    return 0

                count = 0
                for _, player_data in player_stats_df.iterrows():
                    # Get player and team IDs (v3 format)
                    player_id = player_data.get("personId")
                    team_id = player_data.get("teamId")

                    if not player_id or not team_id:
                        continue

                    # Get or create player
                    player = (
                        session.query(Player)
                        .filter(Player.nba_id == player_id)
                        .first()
                    )

                    if not player:
                        # Create player if not exists
                        team = (
                            session.query(Team)
                            .filter(Team.nba_id == team_id)
                            .first()
                        )
                        if not team:
                            continue

                        # Build full name from v3 fields
                        first_name = player_data.get("firstName", "")
                        last_name = player_data.get("familyName", "")
                        full_name = f"{first_name} {last_name}".strip()

                        player = Player(
                            nba_id=player_id,
                            first_name=first_name,
                            last_name=last_name,
                            full_name=full_name,
                            team_id=team.id,
                            is_active=True,
                        )
                        session.add(player)
                        session.flush()

                    # Get team
                    team = (
                        session.query(Team)
                        .filter(Team.nba_id == team_id)
                        .first()
                    )
                    if not team:
                        continue

                    # Parse minutes (v3 format: "25:07" string)
                    minutes = 0.0
                    min_str = player_data.get("minutes")
                    if min_str and isinstance(min_str, str) and ':' in min_str:
                        try:
                            min_parts = min_str.split(":")
                            minutes = float(min_parts[0]) + float(min_parts[1]) / 60
                        except:
                            pass

                    # Upsert player game stats (v3 column names)
                    stmt = (
                        insert(PlayerGameStats)
                        .values(
                            player_id=player.id,
                            game_id=game.id,
                            team_id=team.id,
                            minutes_played=minutes,
                            points=player_data.get("points", 0) or 0,
                            field_goals_made=player_data.get("fieldGoalsMade", 0) or 0,
                            field_goals_attempted=player_data.get("fieldGoalsAttempted", 0) or 0,
                            three_pointers_made=player_data.get("threePointersMade", 0) or 0,
                            three_pointers_attempted=player_data.get("threePointersAttempted", 0) or 0,
                            free_throws_made=player_data.get("freeThrowsMade", 0) or 0,
                            free_throws_attempted=player_data.get("freeThrowsAttempted", 0) or 0,
                            offensive_rebounds=player_data.get("reboundsOffensive", 0) or 0,
                            defensive_rebounds=player_data.get("reboundsDefensive", 0) or 0,
                            total_rebounds=player_data.get("reboundsTotal", 0) or 0,
                            assists=player_data.get("assists", 0) or 0,
                            steals=player_data.get("steals", 0) or 0,
                            blocks=player_data.get("blocks", 0) or 0,
                            turnovers=player_data.get("turnovers", 0) or 0,
                            personal_fouls=player_data.get("foulsPersonal", 0) or 0,
                            plus_minus=player_data.get("plusMinusPoints", 0) or 0,
                        )
                        .on_conflict_do_update(
                            constraint="uq_player_game",
                            set_={
                                "minutes_played": minutes,
                                "points": player_data.get("points", 0) or 0,
                                "field_goals_made": player_data.get("fieldGoalsMade", 0) or 0,
                                "field_goals_attempted": player_data.get("fieldGoalsAttempted", 0) or 0,
                                "three_pointers_made": player_data.get("threePointersMade", 0) or 0,
                                "three_pointers_attempted": player_data.get("threePointersAttempted", 0) or 0,
                                "free_throws_made": player_data.get("freeThrowsMade", 0) or 0,
                                "free_throws_attempted": player_data.get("freeThrowsAttempted", 0) or 0,
                                "offensive_rebounds": player_data.get("reboundsOffensive", 0) or 0,
                                "defensive_rebounds": player_data.get("reboundsDefensive", 0) or 0,
                                "total_rebounds": player_data.get("reboundsTotal", 0) or 0,
                                "assists": player_data.get("assists", 0) or 0,
                                "steals": player_data.get("steals", 0) or 0,
                                "blocks": player_data.get("blocks", 0) or 0,
                                "turnovers": player_data.get("turnovers", 0) or 0,
                                "personal_fouls": player_data.get("foulsPersonal", 0) or 0,
                                "plus_minus": player_data.get("plusMinusPoints", 0) or 0,
                                "updated_at": datetime.utcnow(),
                            },
                        )
                    )
                    session.execute(stmt)
                    count += 1

                logger.info(f"Ingested {count} player stats for game {game_id}")
                return count

            except Exception as e:
                logger.error(f"Box score ingestion failed for game {game_id}: {e}")
                raise

    def ingest_recent_games(self, days: int = 7, season: str = None) -> int:
        """
        Ingest games from the past N days using LeagueGameFinder.
        Also ingests box scores for completed games.
        Returns number of games ingested.
        """
        season = season or config.ingestion.current_season
        logger.info(f"Ingesting games from past {days} days for season {season}")

        self._rate_limit()

        with db_manager.get_session() as session:
            log = self._log_ingestion_start(session, "recent_games")

            try:
                # Calculate date range
                end_date = date.today()
                start_date = end_date - timedelta(days=days)

                # Fetch games from API
                game_finder = leaguegamefinder.LeagueGameFinder(
                    date_from_nullable=start_date.strftime("%m/%d/%Y"),
                    date_to_nullable=end_date.strftime("%m/%d/%Y"),
                    league_id_nullable="00",
                    season_nullable=season,
                    season_type_nullable="Regular Season",
                )
                games_data = game_finder.get_normalized_dict()

                # Process games - each row is one team's perspective
                # So we need to pair them up
                games_by_id = {}
                for row in games_data.get("LeagueGameFinderResults", []):
                    game_id = row.get("GAME_ID")
                    if not game_id:
                        continue

                    if game_id not in games_by_id:
                        games_by_id[game_id] = []
                    games_by_id[game_id].append(row)

                count = 0
                game_ids_to_get_boxscore = []

                for game_id, team_rows in games_by_id.items():
                    if len(team_rows) != 2:
                        continue

                    # Determine home and away teams
                    home_row = None
                    away_row = None
                    for row in team_rows:
                        matchup = row.get("MATCHUP", "")
                        if " vs. " in matchup:
                            home_row = row
                        elif " @ " in matchup:
                            away_row = row

                    if not home_row or not away_row:
                        continue

                    # Get teams from database
                    home_team = (
                        session.query(Team)
                        .filter(Team.nba_id == home_row["TEAM_ID"])
                        .first()
                    )
                    away_team = (
                        session.query(Team)
                        .filter(Team.nba_id == away_row["TEAM_ID"])
                        .first()
                    )

                    if not home_team or not away_team:
                        continue

                    # Parse game date
                    game_date_str = home_row.get("GAME_DATE")
                    try:
                        game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                    except:
                        game_date = date.today()

                    # Determine status based on scores
                    home_score = home_row.get("PTS", 0) or 0
                    away_score = away_row.get("PTS", 0) or 0
                    status = (
                        "final" if home_score > 0 or away_score > 0 else "scheduled"
                    )

                    # Upsert game
                    stmt = (
                        insert(Game)
                        .values(
                            nba_game_id=game_id,
                            season=season,
                            season_type="Regular Season",
                            game_date=game_date,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            home_score=home_score,
                            away_score=away_score,
                            status=status,
                        )
                        .on_conflict_do_update(
                            index_elements=["nba_game_id"],
                            set_={
                                "home_score": home_score,
                                "away_score": away_score,
                                "status": status,
                                "updated_at": datetime.utcnow(),
                            },
                        )
                    )
                    session.execute(stmt)
                    count += 1

                    # Track completed games for box score ingestion
                    if status == "final":
                        game_ids_to_get_boxscore.append(game_id)

                session.commit()
                logger.info(f"Ingested {count} games from past {days} days")

                # Now ingest box scores for completed games (with rate limiting)
                box_score_count = 0
                for game_id in game_ids_to_get_boxscore[
                    :20
                ]:  # Limit to 20 to avoid rate limits
                    try:
                        self._rate_limit()
                        box_count = self.ingest_game_box_score(game_id)
                        box_score_count += box_count
                    except Exception as e:
                        logger.warning(f"Failed to ingest box score for {game_id}: {e}")
                        continue

                logger.info(f"Ingested {box_score_count} player stats from box scores")

                self._log_ingestion_complete(session, log, count)
                return count

            except Exception as e:
                logger.error(f"Recent games ingestion failed: {e}", exc_info=True)
                self._log_ingestion_complete(session, log, 0, str(e))
                return 0

    def ingest_all_season_games(self, season: str = None) -> int:
        """
        Ingest all games for an entire season.
        Uses a full season date range (Oct 1 - Jun 30).
        Returns number of games ingested.
        """
        season = season or config.ingestion.current_season
        logger.info(f"Ingesting all games for season {season}")

        # For NBA season format "2025-26", start year is 2025
        start_year = int(season.split("-")[0])

        # NBA season runs from October to June
        start_date = date(start_year, 10, 1)
        end_date = date(start_year + 1, 6, 30)

        logger.info(f"Date range: {start_date} to {end_date}")

        self._rate_limit()

        with db_manager.get_session() as session:
            log = self._log_ingestion_start(session, "all_season_games")

            try:
                # Fetch games from API for entire season
                game_finder = leaguegamefinder.LeagueGameFinder(
                    date_from_nullable=start_date.strftime("%m/%d/%Y"),
                    date_to_nullable=end_date.strftime("%m/%d/%Y"),
                    league_id_nullable="00",
                    season_nullable=season,
                    season_type_nullable="Regular Season",
                )
                games_data = game_finder.get_normalized_dict()

                # Process games - same logic as ingest_recent_games
                games_by_id = {}
                for row in games_data.get("LeagueGameFinderResults", []):
                    game_id = row.get("GAME_ID")
                    if not game_id:
                        continue

                    if game_id not in games_by_id:
                        games_by_id[game_id] = []
                    games_by_id[game_id].append(row)

                count = 0
                box_score_count = 0

                for game_id, team_rows in games_by_id.items():
                    if len(team_rows) != 2:
                        continue

                    # Determine home and away teams
                    home_row = away_row = None
                    for row in team_rows:
                        matchup = row.get("MATCHUP", "")
                        if " vs. " in matchup:
                            home_row = row
                        elif " @ " in matchup:
                            away_row = row

                    if not home_row or not away_row:
                        continue

                    # Get teams from database
                    home_team = session.query(Team).filter(Team.nba_id == home_row["TEAM_ID"]).first()
                    away_team = session.query(Team).filter(Team.nba_id == away_row["TEAM_ID"]).first()

                    if not home_team or not away_team:
                        continue

                    # Parse game date
                    game_date_str = home_row.get("GAME_DATE")
                    try:
                        game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                    except:
                        continue

                    # Determine if game is completed
                    wl = home_row.get("WL")
                    status = "final" if wl else "scheduled"

                    # Upsert game
                    stmt = (
                        insert(Game)
                        .values(
                            nba_game_id=game_id,
                            season=season,
                            game_date=game_date,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            home_score=home_row.get("PTS") if wl else 0,
                            away_score=away_row.get("PTS") if wl else 0,
                            status=status,
                        )
                        .on_conflict_do_update(
                            index_elements=["nba_game_id"],
                            set_=dict(
                                home_score=home_row.get("PTS") if wl else 0,
                                away_score=away_row.get("PTS") if wl else 0,
                                status=status,
                            ),
                        )
                    )
                    session.execute(stmt)
                    count += 1

                    # Ingest box score for completed games
                    if status == "final":
                        try:
                            stats_count = self.ingest_game_box_score(game_id)
                            if stats_count > 0:
                                box_score_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to ingest box score for {game_id}: {e}")

                session.commit()
                self._log_ingestion_complete(session, log, count)

                logger.info(f"Ingested {count} games, {box_score_count} with box scores")
                return count

            except Exception as e:
                logger.error(f"Error ingesting season games: {e}")
                session.rollback()
                self._log_ingestion_complete(session, log, 0, str(e))
                return 0

    def run_incremental_refresh(self, season: str = None):
        """
        Run an incremental refresh - only fetch recent data and updates.
        This is much faster than full ingestion and avoids re-downloading historical data.
        """
        season = season or config.ingestion.current_season
        logger.info(f"Starting incremental refresh for season {season}")

        # 1. Ingest teams (quick, uses upsert)
        self.ingest_teams()

        # 2. Ingest standings (current standings only)
        self.ingest_standings(season)

        # 3. Ingest rosters (updates only)
        self.ingest_all_rosters(season)

        # 4. Ingest today's games (for live updates)
        self.ingest_todays_games()

        # 5. Ingest only recent games (last 7 days) to catch newly completed games
        # This avoids re-downloading all historical games
        self.ingest_recent_games(days=7, season=season)

        logger.info("Incremental refresh complete!")

    def run_full_ingestion(self, season: str = None):
        """
        Run a full data ingestion cycle for the entire current season.
        WARNING: This re-downloads ALL games from Oct-Jun. Use run_incremental_refresh() for updates.
        """
        season = season or config.ingestion.current_season
        logger.info(f"Starting full ingestion for season {season}")

        # 1. Ingest teams
        self.ingest_teams()

        # 2. Ingest standings
        self.ingest_standings(season)

        # 3. Ingest rosters
        self.ingest_all_rosters(season)

        # 4. Ingest today's games (for live updates)
        self.ingest_todays_games()

        # 5. Ingest ALL games for the season (including box scores)
        self.ingest_all_season_games(season)

        logger.info("Full ingestion complete!")


# Create global instance
ingestion_service = NBADataIngestionService()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run full ingestion
    from models.database import init_database

    init_database()

    ingestion_service.run_full_ingestion()
