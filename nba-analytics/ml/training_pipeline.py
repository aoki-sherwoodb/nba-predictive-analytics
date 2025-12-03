"""
LSTM Training Pipeline for NBA Predictions.
Orchestrates the full training workflow from data to saved model.
"""
import logging
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import numpy as np

from sqlalchemy.dialects.postgresql import insert

from config import config
from models.database import db_manager
from models.database_models import Team
from models.prediction_models import TeamSeasonStats, TeamPrediction, ModelMetadata
from services.historical_ingestion import historical_ingestion_service
from ml.lstm_model import NBALSTMPredictor, LSTMTrainer, create_data_loaders
from ml.data_preprocessor import (
    LSTMDataPreprocessor,
    train_val_split,
    clip_predictions,
)

logger = logging.getLogger(__name__)

# Default paths for model artifacts
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trained_models")


class LSTMTrainingPipeline:
    """
    End-to-end training pipeline for the NBA LSTM prediction model.

    Handles:
    - Loading and preparing training data
    - Model training with validation
    - Saving model artifacts
    - Generating predictions for current season
    - Storing predictions in database
    """

    def __init__(
        self,
        model_dir: str = MODEL_DIR,
        sequence_length: int = 10,
        num_features: int = 20,
        num_targets: int = 9,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
        batch_size: int = 16,
        epochs: int = 100,
    ):
        """
        Initialize the training pipeline.

        Args:
            model_dir: Directory to save model artifacts
            sequence_length: Number of time steps in each sequence
            num_features: Number of features per time step
            num_targets: Number of prediction targets
            hidden_size: LSTM hidden layer size
            num_layers: Number of LSTM layers
            dropout_rate: Dropout probability
            learning_rate: Learning rate for optimizer
            batch_size: Training batch size
            epochs: Maximum training epochs
        """
        self.model_dir = model_dir
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.num_targets = num_targets
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs

        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)

        # Initialize preprocessor
        self.preprocessor = LSTMDataPreprocessor()

        # Model and trainer will be created during training
        self.model = None
        self.trainer = None

    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load and prepare all historical data for training.

        Returns:
            Tuple of (X, y) arrays ready for training
        """
        logger.info("Preparing training data...")

        # Get training data from historical ingestion service
        X, y = historical_ingestion_service.get_all_training_data()

        logger.info(f"Loaded {len(X)} training samples")
        return X, y

    def train_and_save(self, model_version: str) -> Dict:
        """
        Full training pipeline: load data, train model, save artifacts.

        Args:
            model_version: Version identifier for the model (e.g., "lstm_v1.0")

        Returns:
            Dictionary with training results and metrics
        """
        logger.info(f"Starting training pipeline for {model_version}")

        # Prepare data
        X, y = self.prepare_training_data()

        # Split into train/validation
        X_train, X_val, y_train, y_val = train_val_split(
            X, y, val_ratio=0.2, random_state=42
        )

        # Fit preprocessor and transform data
        X_train_scaled, y_train_scaled = self.preprocessor.fit_transform(X_train, y_train)
        X_val_scaled, y_val_scaled = self.preprocessor.transform(X_val, y_val)

        # Create data loaders
        train_loader, val_loader = create_data_loaders(
            X_train_scaled, y_train_scaled,
            X_val_scaled, y_val_scaled,
            batch_size=self.batch_size
        )

        # Initialize model
        self.model = NBALSTMPredictor(
            num_features=self.num_features,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            num_targets=self.num_targets,
            dropout_rate=self.dropout_rate,
        )

        # Initialize trainer
        self.trainer = LSTMTrainer(
            model=self.model,
            learning_rate=self.learning_rate,
        )

        # Train model
        logger.info("Training model...")
        history = self.trainer.train(
            train_loader=train_loader,
            val_loader=val_loader,
            epochs=self.epochs,
            patience=15,
        )

        # Evaluate on validation set
        eval_metrics = self.trainer.evaluate(val_loader)

        # Save artifacts
        model_path = os.path.join(self.model_dir, f"{model_version}.pt")
        scaler_path = os.path.join(self.model_dir, f"{model_version}_scalers")

        self.trainer.save(model_path)
        self.preprocessor.save(scaler_path)

        # Save metadata to database
        self._save_model_metadata(
            model_version=model_version,
            model_path=model_path,
            scaler_path=f"{scaler_path}.joblib",
            history=history,
            eval_metrics=eval_metrics,
        )

        results = {
            "model_version": model_version,
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            "best_epoch": history["best_epoch"],
            "best_val_loss": history["best_val_loss"],
            "final_train_loss": history["train_loss"][-1],
            "eval_metrics": eval_metrics,
            "model_path": model_path,
            "scaler_path": f"{scaler_path}.joblib",
        }

        logger.info(f"Training complete: {results}")
        return results

    def _save_model_metadata(
        self,
        model_version: str,
        model_path: str,
        scaler_path: str,
        history: Dict,
        eval_metrics: Dict,
    ):
        """Save model metadata to database."""
        with db_manager.get_session() as session:
            # Deactivate any currently active models
            session.query(ModelMetadata).filter(
                ModelMetadata.is_active == True
            ).update({"is_active": False})

            # Insert new metadata
            metadata = ModelMetadata(
                model_version=model_version,
                model_type="lstm",
                training_seasons=historical_ingestion_service.TRAINING_SEASONS,
                epochs_trained=history["best_epoch"] + 1,
                batch_size=self.batch_size,
                sequence_length=self.sequence_length,
                hidden_units=[self.hidden_size, 32],  # LSTM hidden + FC layer
                dropout_rate=self.dropout_rate,
                learning_rate=self.learning_rate,
                training_loss=history["train_loss"][-1] if history["train_loss"] else None,
                validation_loss=history["best_val_loss"],
                mae_wins=eval_metrics["per_target_mae"].get("wins"),
                mae_ppg=eval_metrics["per_target_mae"].get("ppg"),
                model_path=model_path,
                scaler_path=scaler_path,
                is_active=True,
            )
            session.add(metadata)
            session.commit()

            logger.info(f"Saved model metadata for {model_version}")

    def load_model(self, model_version: Optional[str] = None):
        """
        Load a trained model from disk.

        Args:
            model_version: Specific version to load. If None, loads the active model.
        """
        with db_manager.get_session() as session:
            if model_version:
                metadata = session.query(ModelMetadata).filter(
                    ModelMetadata.model_version == model_version
                ).first()
            else:
                # Load active model
                metadata = session.query(ModelMetadata).filter(
                    ModelMetadata.is_active == True
                ).first()

            if not metadata:
                raise ValueError(f"No model found for version: {model_version or 'active'}")

            # Initialize model with saved config
            self.model = NBALSTMPredictor(
                num_features=self.num_features,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                num_targets=self.num_targets,
                dropout_rate=self.dropout_rate,
            )

            # Initialize trainer and load weights
            self.trainer = LSTMTrainer(
                model=self.model,
                learning_rate=self.learning_rate,
            )
            self.trainer.load(metadata.model_path)

            # Load preprocessor
            scaler_path = metadata.scaler_path.replace(".joblib", "")
            self.preprocessor.load(scaler_path)

            logger.info(f"Loaded model {metadata.model_version}")

    def generate_predictions(
        self,
        season: str,
        prediction_date: Optional[date] = None,
    ) -> List[Dict]:
        """
        Generate predictions for all teams for the specified season.

        Args:
            season: Season to predict (e.g., "2025-26")
            prediction_date: Date of prediction. Defaults to today.

        Returns:
            List of prediction dictionaries
        """
        if self.model is None or self.trainer is None:
            self.load_model()

        prediction_date = prediction_date or date.today()

        with db_manager.get_session() as session:
            # Get active model version
            metadata = session.query(ModelMetadata).filter(
                ModelMetadata.is_active == True
            ).first()

            if not metadata:
                raise ValueError("No active model found")

            model_version = metadata.model_version

            # Get all teams
            teams = session.query(Team).all()

            predictions = []
            for team in teams:
                # Build sequence for this team
                features, _ = historical_ingestion_service.build_training_sequences(
                    team.id, season
                )

                if features is None:
                    logger.warning(f"No sequence data for team {team.abbreviation}")
                    continue

                # Prepare input
                X = np.array([features])  # Add batch dimension
                X_scaled, _ = self.preprocessor.transform(X)

                # Generate prediction
                y_scaled = self.trainer.predict(X_scaled)
                y = self.preprocessor.inverse_transform_targets(y_scaled)
                y = clip_predictions(y)[0]  # Remove batch dimension

                # Create prediction record
                pred = {
                    "team_id": team.id,
                    "team_name": team.name,
                    "team_abbr": team.abbreviation,
                    "conference": team.conference,
                    "season": season,
                    "prediction_date": str(prediction_date),
                    "model_version": model_version,
                    "predicted_wins": float(y[0]),
                    "predicted_losses": float(y[1]),
                    "predicted_win_pct": float(y[2]),
                    "predicted_conference_rank": int(y[3]),
                    "playoff_probability": float(y[4]),
                    "predicted_ppg": float(y[5]),
                    "predicted_oppg": float(y[6]),
                    "predicted_pace": float(y[7]),
                    "predicted_defensive_rating": float(y[8]),
                }
                predictions.append(pred)

                # Save to database
                self._save_prediction(session, pred, prediction_date, model_version)

            session.commit()

        logger.info(f"Generated {len(predictions)} predictions for {season}")
        return predictions

    def _save_prediction(
        self,
        session,
        pred: Dict,
        prediction_date: date,
        model_version: str,
    ):
        """Save a single team prediction to database."""
        stmt = insert(TeamPrediction).values(
            team_id=pred["team_id"],
            season=pred["season"],
            prediction_date=prediction_date,
            model_version=model_version,
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
                "model_version": model_version,
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


# Global pipeline instance
training_pipeline = LSTMTrainingPipeline()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize database
    from models.database import init_database
    init_database()

    # First, ingest historical data
    logger.info("Ingesting historical data...")
    historical_ingestion_service.ingest_all_historical_data()

    # Train model
    version = f"lstm_v{datetime.now().strftime('%Y%m%d_%H%M')}"
    results = training_pipeline.train_and_save(version)

    # Generate predictions for current season
    predictions = training_pipeline.generate_predictions(config.ingestion.current_season)

    print(f"\nTraining Results:")
    print(f"  Model Version: {results['model_version']}")
    print(f"  Best Validation Loss: {results['best_val_loss']:.4f}")
    print(f"  Wins MAE: {results['eval_metrics']['per_target_mae']['wins']:.2f}")

    print(f"\nGenerated {len(predictions)} predictions for {config.ingestion.current_season}")
