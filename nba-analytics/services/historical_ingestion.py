"""
Historical Data Ingestion Service for LSTM Training.
Fetches 5 seasons of historical NBA team data for model training.
"""
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd

from nba_api.stats.endpoints import (
    leaguedashteamstats,
    teamgamelog,
    leaguestandings,
)
from nba_api.stats.static import teams as nba_teams
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from config import config
from models.database_models import Team
from models.prediction_models import TeamSeasonStats
from models.database import db_manager

logger = logging.getLogger(__name__)


class HistoricalDataIngestionService:
    """
    Service for ingesting historical NBA data for LSTM training.
    Fetches team statistics from multiple seasons.
    """

    # Rate limiting: NBA API has strict rate limits
    REQUEST_DELAY = 0.6  # Seconds between API requests

    # Historical seasons for training (5 seasons)
    TRAINING_SEASONS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

    def __init__(self):
        self.last_request_time = 0

    def _rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def ingest_team_season_stats(self, season: str) -> int:
        """
        Fetch and store aggregated team stats for a complete season.
        Uses leaguedashteamstats endpoint.

        Args:
            season: Season string (e.g., "2024-25")

        Returns:
            Number of team records ingested
        """
        logger.info(f"Ingesting team season stats for {season}")
        self._rate_limit()

        with db_manager.get_session() as session:
            try:
                # Fetch team stats from NBA API
                stats = leaguedashteamstats.LeagueDashTeamStats(
                    season=season,
                    season_type_all_star="Regular Season",
                    per_mode_detailed="PerGame"
                )
                stats_data = stats.get_normalized_dict()

                # Fetch standings for rankings
                self._rate_limit()
                standings = leaguestandings.LeagueStandings(
                    season=season,
                    league_id="00"
                )
                standings_data = standings.get_normalized_dict()

                # Create lookup for standings by team ID
                standings_lookup = {}
                for row in standings_data.get("Standings", []):
                    standings_lookup[row["TeamID"]] = {
                        "wins": row.get("WINS", 0),
                        "losses": row.get("LOSSES", 0),
                        "win_pct": row.get("WinPCT", 0.0),
                        "conf_rank": row.get("PlayoffRank"),
                        "div_rank": row.get("DivisionRank"),
                        "playoff_seed": row.get("PlayoffRank") if row.get("PlayoffRank", 99) <= 10 else None,
                    }

                count = 0
                for row in stats_data.get("LeagueDashTeamStats", []):
                    team_nba_id = row["TEAM_ID"]

                    # Get team from database
                    team = session.query(Team).filter(Team.nba_id == team_nba_id).first()
                    if not team:
                        logger.warning(f"Team {team_nba_id} not found in database")
                        continue

                    # Get standings info
                    standing = standings_lookup.get(team_nba_id, {})

                    # Calculate advanced metrics
                    pace = row.get("PACE", 0) or 100.0
                    off_rating = row.get("OFF_RATING", 0) or 110.0
                    def_rating = row.get("DEF_RATING", 0) or 110.0

                    # Upsert team season stats
                    stmt = insert(TeamSeasonStats).values(
                        team_id=team.id,
                        season=season,
                        games_played=row.get("GP", 0),
                        wins=standing.get("wins", 0),
                        losses=standing.get("losses", 0),
                        win_percentage=standing.get("win_pct", 0.0),
                        points_per_game=row.get("PTS", 0),
                        field_goal_pct=row.get("FG_PCT", 0) * 100 if row.get("FG_PCT") else 0,
                        three_point_pct=row.get("FG3_PCT", 0) * 100 if row.get("FG3_PCT") else 0,
                        free_throw_pct=row.get("FT_PCT", 0) * 100 if row.get("FT_PCT") else 0,
                        offensive_rebounds_pg=row.get("OREB", 0),
                        assists_per_game=row.get("AST", 0),
                        turnovers_per_game=row.get("TOV", 0),
                        opponent_points_per_game=row.get("OPP_PTS", 0) if row.get("OPP_PTS") else def_rating,
                        defensive_rebounds_pg=row.get("DREB", 0),
                        steals_per_game=row.get("STL", 0),
                        blocks_per_game=row.get("BLK", 0),
                        pace=pace,
                        offensive_rating=off_rating,
                        defensive_rating=def_rating,
                        net_rating=off_rating - def_rating,
                        conference_rank=standing.get("conf_rank"),
                        division_rank=standing.get("div_rank"),
                        playoff_seed=standing.get("playoff_seed"),
                    ).on_conflict_do_update(
                        constraint="uq_team_season_stats",
                        set_={
                            "games_played": row.get("GP", 0),
                            "wins": standing.get("wins", 0),
                            "losses": standing.get("losses", 0),
                            "win_percentage": standing.get("win_pct", 0.0),
                            "points_per_game": row.get("PTS", 0),
                            "field_goal_pct": row.get("FG_PCT", 0) * 100 if row.get("FG_PCT") else 0,
                            "three_point_pct": row.get("FG3_PCT", 0) * 100 if row.get("FG3_PCT") else 0,
                            "free_throw_pct": row.get("FT_PCT", 0) * 100 if row.get("FT_PCT") else 0,
                            "offensive_rebounds_pg": row.get("OREB", 0),
                            "assists_per_game": row.get("AST", 0),
                            "turnovers_per_game": row.get("TOV", 0),
                            "offensive_rating": off_rating,
                            "defensive_rating": def_rating,
                            "net_rating": off_rating - def_rating,
                            "pace": pace,
                            "conference_rank": standing.get("conf_rank"),
                            "division_rank": standing.get("div_rank"),
                            "playoff_seed": standing.get("playoff_seed"),
                            "updated_at": datetime.utcnow(),
                        }
                    )
                    session.execute(stmt)
                    count += 1

                session.commit()
                logger.info(f"Ingested {count} team stats for season {season}")
                return count

            except Exception as e:
                logger.error(f"Failed to ingest team stats for {season}: {e}")
                session.rollback()
                raise

    def ingest_team_game_logs(self, team_nba_id: int, season: str) -> List[Dict]:
        """
        Fetch game-by-game logs for a team.
        Used for building LSTM training sequences.

        Args:
            team_nba_id: NBA team ID
            season: Season string

        Returns:
            List of game records with stats
        """
        logger.debug(f"Fetching game logs for team {team_nba_id}, season {season}")
        self._rate_limit()

        try:
            game_log = teamgamelog.TeamGameLog(
                team_id=team_nba_id,
                season=season,
                season_type_all_star="Regular Season"
            )
            data = game_log.get_normalized_dict()

            games = []
            for row in data.get("TeamGameLog", []):
                games.append({
                    "game_id": row.get("Game_ID"),
                    "game_date": row.get("GAME_DATE"),
                    "matchup": row.get("MATCHUP"),
                    "wl": row.get("WL"),
                    "wins": row.get("W", 0),
                    "losses": row.get("L", 0),
                    "points": row.get("PTS", 0),
                    "fg_pct": row.get("FG_PCT", 0),
                    "fg3_pct": row.get("FG3_PCT", 0),
                    "ft_pct": row.get("FT_PCT", 0),
                    "oreb": row.get("OREB", 0),
                    "dreb": row.get("DREB", 0),
                    "reb": row.get("REB", 0),
                    "ast": row.get("AST", 0),
                    "stl": row.get("STL", 0),
                    "blk": row.get("BLK", 0),
                    "tov": row.get("TOV", 0),
                    "plus_minus": row.get("PLUS_MINUS", 0),
                })

            return games

        except Exception as e:
            logger.error(f"Failed to fetch game logs for team {team_nba_id}: {e}")
            return []

    def ingest_all_historical_data(self) -> Dict[str, int]:
        """
        Main method to ingest all historical seasons of data.
        Iterates through seasons with rate limiting.

        Returns:
            Dict with counts per season
        """
        logger.info("Starting full historical data ingestion...")
        results = {}

        for season in self.TRAINING_SEASONS:
            try:
                count = self.ingest_team_season_stats(season)
                results[season] = count
                logger.info(f"Completed {season}: {count} teams")
            except Exception as e:
                logger.error(f"Failed to ingest {season}: {e}")
                results[season] = 0

        logger.info(f"Historical ingestion complete: {results}")
        return results

    def build_training_sequences(
        self,
        team_id: int,
        season: str,
        sequence_length: int = 10,
        step_size: int = 5
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Build LSTM-compatible sequences from game logs.

        The sequence represents team performance evolution through the season.
        Each time step aggregates `step_size` games worth of stats.

        Args:
            team_id: Database team ID
            season: Season string
            sequence_length: Number of time steps in sequence
            step_size: Number of games to aggregate per step

        Returns:
            Tuple of (features array, targets array) or (None, None) if insufficient data
        """
        with db_manager.get_session() as session:
            # Get team's NBA ID
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                return None, None

            # Fetch game logs
            game_logs = self.ingest_team_game_logs(team.nba_id, season)
            if len(game_logs) < sequence_length * step_size:
                logger.warning(
                    f"Insufficient games for team {team_id} in {season}: "
                    f"{len(game_logs)} < {sequence_length * step_size}"
                )
                return None, None

            # Convert to DataFrame for easier processing
            df = pd.DataFrame(game_logs)

            # Reverse to chronological order (game logs come newest first)
            df = df.iloc[::-1].reset_index(drop=True)

            # Calculate rolling statistics for each time step
            sequences = []
            for i in range(sequence_length):
                start_idx = i * step_size
                end_idx = start_idx + step_size
                window = df.iloc[start_idx:end_idx]

                # Aggregate stats for this window
                step_features = [
                    end_idx,  # games_played
                    window["wl"].apply(lambda x: 1 if x == "W" else 0).sum(),  # wins in window
                    window["wl"].apply(lambda x: 1 if x == "L" else 0).sum(),  # losses in window
                    df.iloc[:end_idx]["wl"].apply(lambda x: 1 if x == "W" else 0).mean(),  # running win_pct
                    window["points"].mean(),  # avg ppg
                    window["fg_pct"].mean() * 100,  # fg%
                    window["fg3_pct"].mean() * 100,  # 3p%
                    window["ft_pct"].mean() * 100,  # ft%
                    window["ast"].mean(),  # assists
                    window["reb"].mean(),  # rebounds
                    window["tov"].mean(),  # turnovers
                    window["stl"].mean(),  # steals
                    window["blk"].mean(),  # blocks
                    window["oreb"].mean(),  # offensive rebounds
                    window["dreb"].mean(),  # defensive rebounds
                    window["plus_minus"].mean(),  # plus/minus
                    100.0,  # placeholder for pace (would need more data)
                    110.0,  # placeholder for off_rating
                    110.0,  # placeholder for def_rating
                    0.0,  # placeholder for net_rating
                ]
                sequences.append(step_features)

            # Get end-of-season targets from TeamSeasonStats
            season_stats = session.query(TeamSeasonStats).filter(
                TeamSeasonStats.team_id == team_id,
                TeamSeasonStats.season == season
            ).first()

            if not season_stats:
                return None, None

            targets = np.array([
                season_stats.wins or 0,
                season_stats.losses or 0,
                season_stats.win_percentage or 0,
                season_stats.conference_rank or 15,
                1.0 if (season_stats.playoff_seed and season_stats.playoff_seed <= 10) else 0.0,
                season_stats.points_per_game or 110,
                season_stats.opponent_points_per_game or 110,
                season_stats.pace or 100,
                season_stats.defensive_rating or 110,
            ])

            features = np.array(sequences)
            return features, targets

    def get_all_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build training data from all historical seasons and teams.

        Returns:
            Tuple of (X, y) arrays for model training
        """
        logger.info("Building training data from all historical seasons...")

        all_features = []
        all_targets = []

        with db_manager.get_session() as session:
            teams = session.query(Team).all()

            for season in self.TRAINING_SEASONS:
                for team in teams:
                    features, targets = self.build_training_sequences(
                        team.id, season
                    )
                    if features is not None and targets is not None:
                        all_features.append(features)
                        all_targets.append(targets)

        if not all_features:
            raise ValueError("No training data available")

        X = np.array(all_features)
        y = np.array(all_targets)

        logger.info(f"Built training data: X shape={X.shape}, y shape={y.shape}")
        return X, y


# Create global instance
historical_ingestion_service = HistoricalDataIngestionService()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run historical ingestion
    from models.database import init_database
    init_database()

    historical_ingestion_service.ingest_all_historical_data()
