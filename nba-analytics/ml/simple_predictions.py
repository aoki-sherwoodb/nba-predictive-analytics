"""
Simple Prediction Generator for NBA Analytics.
Generates predictions based on historical TeamSeasonStats without requiring game-level data.
Uses statistical trends from past seasons to project current season outcomes.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
import numpy as np

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import desc

from config import config
from models.database import db_manager
from models.database_models import Team
from models.prediction_models import TeamSeasonStats, TeamPrediction, ModelMetadata

logger = logging.getLogger(__name__)


class SimplePredictionGenerator:
    """
    Generates predictions using historical TeamSeasonStats averages.
    A simpler alternative when game-level data isn't available for LSTM training.
    """

    def __init__(self):
        self.model_version = f"simple_v{datetime.now().strftime('%Y%m%d_%H%M')}"

    def _calculate_team_projection(
        self,
        team_id: int,
        target_season: str,
        session
    ) -> Optional[Dict]:
        """
        Calculate projected stats for a team based on historical data.
        Uses weighted average of recent seasons.
        """
        # Get historical stats for this team
        historical = session.query(TeamSeasonStats).filter(
            TeamSeasonStats.team_id == team_id,
            TeamSeasonStats.season != target_season
        ).order_by(desc(TeamSeasonStats.season)).limit(4).all()

        if not historical:
            logger.warning(f"No historical data for team {team_id}")
            return None

        # Get current season stats if available
        current = session.query(TeamSeasonStats).filter(
            TeamSeasonStats.team_id == team_id,
            TeamSeasonStats.season == target_season
        ).first()

        # Calculate weighted averages (more recent seasons weighted higher)
        weights = [0.4, 0.3, 0.2, 0.1][:len(historical)]
        weights = [w / sum(weights) for w in weights]  # Normalize

        # Project wins
        hist_wins = [h.wins or 0 for h in historical]
        projected_wins = sum(w * v for w, v in zip(weights, hist_wins))

        # If current season has games, blend with projection
        if current and current.games_played and current.games_played > 10:
            # Extrapolate current pace
            games_remaining = 82 - current.games_played
            current_pace_wins = (current.wins / current.games_played) * 82
            # Blend: 60% current pace, 40% historical projection
            projected_wins = 0.6 * current_pace_wins + 0.4 * projected_wins

        projected_losses = 82 - projected_wins
        projected_win_pct = projected_wins / 82

        # Project other stats
        def weighted_avg(attr):
            vals = [getattr(h, attr) or 0 for h in historical]
            return sum(w * v for w, v in zip(weights, vals))

        ppg = weighted_avg('points_per_game')
        oppg = weighted_avg('opponent_points_per_game') or weighted_avg('defensive_rating')
        pace = weighted_avg('pace')
        def_rating = weighted_avg('defensive_rating')

        # Calculate playoff probability based on projected wins
        # Historically, ~42 wins is playoff threshold
        if projected_wins >= 50:
            playoff_prob = 0.95
        elif projected_wins >= 45:
            playoff_prob = 0.85
        elif projected_wins >= 42:
            playoff_prob = 0.70
        elif projected_wins >= 38:
            playoff_prob = 0.45
        elif projected_wins >= 35:
            playoff_prob = 0.25
        else:
            playoff_prob = 0.10

        # Conference rank estimate (will be refined after all teams projected)
        conf_rank = int(16 - projected_wins / 5.5)  # Rough estimate
        conf_rank = max(1, min(15, conf_rank))

        return {
            'predicted_wins': round(projected_wins, 1),
            'predicted_losses': round(projected_losses, 1),
            'predicted_win_pct': round(projected_win_pct, 3),
            'predicted_conference_rank': conf_rank,
            'playoff_probability': round(playoff_prob, 2),
            'predicted_ppg': round(ppg, 1) if ppg else 110.0,
            'predicted_oppg': round(oppg, 1) if oppg else 110.0,
            'predicted_pace': round(pace, 1) if pace else 100.0,
            'predicted_defensive_rating': round(def_rating, 1) if def_rating else 110.0,
        }

    def generate_predictions(
        self,
        season: str,
        prediction_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Generate predictions for all teams for the specified season.
        """
        prediction_date = prediction_date or date.today()

        with db_manager.get_session() as session:
            # First, save model metadata
            self._save_model_metadata(session)

            teams = session.query(Team).all()
            all_predictions = []

            # Generate projections for each team
            for team in teams:
                proj = self._calculate_team_projection(team.id, season, session)
                if proj is None:
                    continue

                prediction = {
                    'team_id': team.id,
                    'team_name': team.name,
                    'team_abbr': team.abbreviation,
                    'conference': team.conference,
                    'season': season,
                    'prediction_date': str(prediction_date),
                    'model_version': self.model_version,
                    **proj
                }
                all_predictions.append(prediction)

            # Refine conference ranks based on all projections
            self._refine_conference_ranks(all_predictions)

            # Save all predictions to database
            for pred in all_predictions:
                self._save_prediction(session, pred, prediction_date)

            session.commit()

        logger.info(f"Generated {len(all_predictions)} predictions for {season}")
        return all_predictions

    def _refine_conference_ranks(self, predictions: List[Dict]):
        """Sort teams by projected wins within each conference and assign ranks."""
        # Split by conference
        east = [p for p in predictions if p.get('conference') == 'East']
        west = [p for p in predictions if p.get('conference') == 'West']

        # Sort by projected wins (descending)
        east.sort(key=lambda x: x['predicted_wins'], reverse=True)
        west.sort(key=lambda x: x['predicted_wins'], reverse=True)

        # Assign ranks
        for i, p in enumerate(east):
            p['predicted_conference_rank'] = i + 1
        for i, p in enumerate(west):
            p['predicted_conference_rank'] = i + 1

    def _save_model_metadata(self, session):
        """Save model metadata to database."""
        # Deactivate any currently active models
        session.query(ModelMetadata).filter(
            ModelMetadata.is_active == True
        ).update({"is_active": False})

        # Insert new metadata
        metadata = ModelMetadata(
            model_version=self.model_version,
            model_type="simple_weighted_avg",
            training_seasons=["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"],
            epochs_trained=0,
            batch_size=0,
            sequence_length=0,
            hidden_units=[],
            dropout_rate=0.0,
            learning_rate=0.0,
            training_loss=0.0,
            validation_loss=0.0,
            mae_wins=None,
            mae_ppg=None,
            model_path=None,
            scaler_path=None,
            is_active=True,
        )
        session.add(metadata)
        session.flush()  # Get the ID without committing
        logger.info(f"Saved model metadata for {self.model_version}")

    def _save_prediction(self, session, pred: Dict, prediction_date: date):
        """Save a single team prediction to database."""
        stmt = insert(TeamPrediction).values(
            team_id=pred["team_id"],
            season=pred["season"],
            prediction_date=prediction_date,
            model_version=self.model_version,
            predicted_wins=pred["predicted_wins"],
            predicted_losses=pred["predicted_losses"],
            predicted_win_pct=pred["predicted_win_pct"],
            predicted_conference_rank=pred["predicted_conference_rank"],
            playoff_probability=pred["playoff_probability"],
            predicted_ppg=pred["predicted_ppg"],
            predicted_oppg=pred["predicted_oppg"],
            predicted_pace=pred["predicted_pace"],
            predicted_defensive_rating=pred["predicted_defensive_rating"],
        ).on_conflict_do_update(
            index_elements=["season", "team_id", "prediction_date"],
            set_={
                "model_version": self.model_version,
                "predicted_wins": pred["predicted_wins"],
                "predicted_losses": pred["predicted_losses"],
                "predicted_win_pct": pred["predicted_win_pct"],
                "predicted_conference_rank": pred["predicted_conference_rank"],
                "playoff_probability": pred["playoff_probability"],
                "predicted_ppg": pred["predicted_ppg"],
                "predicted_oppg": pred["predicted_oppg"],
                "predicted_pace": pred["predicted_pace"],
                "predicted_defensive_rating": pred["predicted_defensive_rating"],
            }
        )
        session.execute(stmt)


# Create global instance
simple_predictor = SimplePredictionGenerator()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize database
    from models.database import init_database
    init_database()

    # Generate predictions for current season
    predictions = simple_predictor.generate_predictions(config.ingestion.current_season)

    print(f"\nGenerated {len(predictions)} predictions for {config.ingestion.current_season}")
    print("\nTop 5 projected teams:")
    sorted_preds = sorted(predictions, key=lambda x: x['predicted_wins'], reverse=True)
    for p in sorted_preds[:5]:
        print(f"  {p['team_abbr']}: {p['predicted_wins']:.1f} wins ({p['playoff_probability']*100:.0f}% playoff)")
