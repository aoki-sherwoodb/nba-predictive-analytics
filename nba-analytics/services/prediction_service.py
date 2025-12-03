"""
Prediction Service for NBA Analytics.
Handles retrieval and generation of LSTM-based predictions.
"""
import logging
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from config import config
from models.database import db_manager
from models.database_models import Team
from models.prediction_models import TeamPrediction, ModelMetadata
from services.cache import cache_manager

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Service for generating and retrieving LSTM predictions.

    Provides caching and database access for team predictions.
    """

    # Cache TTL in seconds
    PREDICTION_CACHE_TTL = 3600  # 1 hour

    def __init__(self):
        self._training_pipeline = None

    @property
    def training_pipeline(self):
        """Lazy load training pipeline to avoid circular imports."""
        if self._training_pipeline is None:
            from ml.training_pipeline import training_pipeline
            self._training_pipeline = training_pipeline
        return self._training_pipeline

    def get_all_predictions(
        self,
        season: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Get predictions for all teams in a season.

        Args:
            season: Season string. Defaults to current season.

        Returns:
            Dictionary with predictions organized by conference,
            or None if no predictions available.
        """
        season = season or config.ingestion.current_season

        # Try cache first
        cache_key = f"predictions:all:{season}"
        cached = cache_manager.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for predictions:{season}")
            return cached

        # Query database
        with db_manager.get_session() as session:
            # Get latest prediction date for this season
            latest = session.query(TeamPrediction.prediction_date).filter(
                TeamPrediction.season == season
            ).order_by(desc(TeamPrediction.prediction_date)).first()

            if not latest:
                logger.info(f"No predictions found for season {season}")
                return None

            prediction_date = latest[0]

            # Get all predictions for latest date
            predictions = session.query(TeamPrediction, Team).join(Team).filter(
                TeamPrediction.season == season,
                TeamPrediction.prediction_date == prediction_date,
            ).order_by(TeamPrediction.predicted_conference_rank).all()

            # Get model metadata
            if predictions:
                model_version = predictions[0][0].model_version
                metadata = session.query(ModelMetadata).filter(
                    ModelMetadata.model_version == model_version
                ).first()
            else:
                metadata = None

            # Organize by conference
            east = []
            west = []

            for pred, team in predictions:
                pred_dict = {
                    "team_id": team.id,
                    "team_name": team.name,
                    "team_abbr": team.abbreviation,
                    "conference": team.conference,
                    "predicted_wins": pred.predicted_wins,
                    "predicted_losses": pred.predicted_losses,
                    "predicted_win_pct": pred.predicted_win_pct,
                    "predicted_conference_rank": pred.predicted_conference_rank,
                    "playoff_probability": pred.playoff_probability,
                    "predicted_ppg": pred.predicted_ppg,
                    "predicted_oppg": pred.predicted_oppg,
                    "predicted_pace": pred.predicted_pace,
                    "predicted_defensive_rating": pred.predicted_defensive_rating,
                    "wins_lower_bound": pred.wins_lower_bound,
                    "wins_upper_bound": pred.wins_upper_bound,
                }

                if team.conference == "East":
                    east.append(pred_dict)
                else:
                    west.append(pred_dict)

            # Sort by predicted rank
            east.sort(key=lambda x: x["predicted_conference_rank"])
            west.sort(key=lambda x: x["predicted_conference_rank"])

            result = {
                "season": season,
                "prediction_date": str(prediction_date),
                "model_version": predictions[0][0].model_version if predictions else None,
                "model_mae_wins": metadata.mae_wins if metadata else None,
                "east": east,
                "west": west,
            }

            # Cache result
            cache_manager.set(cache_key, result, self.PREDICTION_CACHE_TTL)

            return result

    def get_team_prediction(
        self,
        team_id: int,
        season: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Get predictions for a specific team.

        Args:
            team_id: Database team ID
            season: Season string. Defaults to current season.

        Returns:
            Prediction dictionary or None if not found.
        """
        season = season or config.ingestion.current_season

        # Try cache first
        cache_key = f"predictions:team:{season}:{team_id}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Query database
        with db_manager.get_session() as session:
            prediction = session.query(TeamPrediction, Team).join(Team).filter(
                TeamPrediction.team_id == team_id,
                TeamPrediction.season == season,
            ).order_by(desc(TeamPrediction.prediction_date)).first()

            if not prediction:
                return None

            pred, team = prediction

            result = {
                "team_id": team.id,
                "team_name": team.name,
                "team_abbr": team.abbreviation,
                "conference": team.conference,
                "season": pred.season,
                "prediction_date": str(pred.prediction_date),
                "model_version": pred.model_version,
                "predicted_wins": pred.predicted_wins,
                "predicted_losses": pred.predicted_losses,
                "predicted_win_pct": pred.predicted_win_pct,
                "predicted_conference_rank": pred.predicted_conference_rank,
                "playoff_probability": pred.playoff_probability,
                "predicted_ppg": pred.predicted_ppg,
                "predicted_oppg": pred.predicted_oppg,
                "predicted_pace": pred.predicted_pace,
                "predicted_defensive_rating": pred.predicted_defensive_rating,
                "wins_lower_bound": pred.wins_lower_bound,
                "wins_upper_bound": pred.wins_upper_bound,
            }

            # Cache result
            cache_manager.set(cache_key, result, self.PREDICTION_CACHE_TTL)

            return result

    def generate_fresh_predictions(
        self,
        season: Optional[str] = None,
    ) -> int:
        """
        Generate new predictions using the active model.

        Args:
            season: Season to predict. Defaults to current season.

        Returns:
            Number of predictions generated.
        """
        season = season or config.ingestion.current_season

        logger.info(f"Generating fresh predictions for {season}")

        try:
            predictions = self.training_pipeline.generate_predictions(
                season=season,
                prediction_date=date.today(),
            )

            # Invalidate cache
            self.invalidate_cache(season)

            logger.info(f"Generated {len(predictions)} predictions")
            return len(predictions)

        except Exception as e:
            logger.error(f"Failed to generate predictions: {e}")
            raise

    def get_predictions_vs_actual(
        self,
        season: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Compare predictions to actual current standings.

        Args:
            season: Season string. Defaults to current season.

        Returns:
            Dictionary with comparison data.
        """
        from models.database_models import TeamStanding

        season = season or config.ingestion.current_season

        predictions = self.get_all_predictions(season)
        if not predictions:
            return None

        with db_manager.get_session() as session:
            # Get current standings
            standings = session.query(TeamStanding, Team).join(Team).filter(
                TeamStanding.season == season
            ).all()

            standings_map = {}
            for standing, team in standings:
                standings_map[team.id] = {
                    "actual_wins": standing.wins,
                    "actual_losses": standing.losses,
                    "actual_win_pct": standing.win_percentage,
                    "actual_conference_rank": standing.conference_rank,
                }

        # Combine predictions with actuals
        comparisons = []
        for conf in ["east", "west"]:
            for pred in predictions.get(conf, []):
                actual = standings_map.get(pred["team_id"], {})
                comparisons.append({
                    "team_id": pred["team_id"],
                    "team_abbr": pred["team_abbr"],
                    "conference": pred["conference"],
                    "predicted_wins": pred["predicted_wins"],
                    "actual_wins": actual.get("actual_wins", 0),
                    "wins_diff": pred["predicted_wins"] - actual.get("actual_wins", 0),
                    "predicted_rank": pred["predicted_conference_rank"],
                    "actual_rank": actual.get("actual_conference_rank"),
                    "rank_diff": (pred["predicted_conference_rank"] or 0) - (actual.get("actual_conference_rank") or 0),
                    "playoff_probability": pred["playoff_probability"],
                })

        return {
            "season": season,
            "prediction_date": predictions.get("prediction_date"),
            "comparisons": comparisons,
        }

    def get_prediction_history(
        self,
        team_id: int,
        season: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get historical predictions for a team to show evolution.

        Args:
            team_id: Database team ID
            season: Season string
            limit: Maximum number of historical predictions

        Returns:
            List of prediction dictionaries ordered by date.
        """
        season = season or config.ingestion.current_season

        with db_manager.get_session() as session:
            predictions = session.query(TeamPrediction).filter(
                TeamPrediction.team_id == team_id,
                TeamPrediction.season == season,
            ).order_by(desc(TeamPrediction.prediction_date)).limit(limit).all()

            return [
                {
                    "prediction_date": str(p.prediction_date),
                    "model_version": p.model_version,
                    "predicted_wins": p.predicted_wins,
                    "predicted_losses": p.predicted_losses,
                    "predicted_win_pct": p.predicted_win_pct,
                    "predicted_conference_rank": p.predicted_conference_rank,
                    "playoff_probability": p.playoff_probability,
                }
                for p in predictions
            ]

    def invalidate_cache(self, season: Optional[str] = None):
        """
        Invalidate prediction caches for a season.

        Args:
            season: Season to invalidate. If None, invalidates all.
        """
        season = season or config.ingestion.current_season

        # Clear all prediction cache keys for this season
        patterns = [
            f"predictions:all:{season}",
            f"predictions:team:{season}:*",
        ]

        for pattern in patterns:
            try:
                cache_manager.delete(pattern)
            except Exception as e:
                logger.warning(f"Failed to invalidate cache for {pattern}: {e}")

        logger.info(f"Invalidated prediction cache for {season}")

    def get_model_info(self) -> Optional[Dict]:
        """
        Get information about the currently active model.

        Returns:
            Model metadata dictionary or None.
        """
        with db_manager.get_session() as session:
            metadata = session.query(ModelMetadata).filter(
                ModelMetadata.is_active == True
            ).first()

            if not metadata:
                return None

            return {
                "model_version": metadata.model_version,
                "model_type": metadata.model_type,
                "trained_at": str(metadata.trained_at) if metadata.trained_at else None,
                "training_seasons": metadata.training_seasons,
                "epochs_trained": metadata.epochs_trained,
                "validation_loss": metadata.validation_loss,
                "mae_wins": metadata.mae_wins,
                "mae_ppg": metadata.mae_ppg,
                "is_active": metadata.is_active,
            }


# Global service instance
prediction_service = PredictionService()
