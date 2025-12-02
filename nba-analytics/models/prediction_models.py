"""
Prediction models for NBA Analytics LSTM-based forecasting.
Stores historical team statistics, model predictions, and metadata.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean,
    ForeignKey, Text, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.database_models import Base


class TeamSeasonStats(Base):
    """
    Aggregated team statistics for a season.
    Used as training data for LSTM predictions.
    """
    __tablename__ = "team_season_stats"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    season = Column(String(10), nullable=False, index=True)  # "2024-25"
    games_played = Column(Integer, default=0)

    # Record
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_percentage = Column(Float, default=0.0)

    # Offensive stats (per game)
    points_per_game = Column(Float)
    field_goal_pct = Column(Float)
    three_point_pct = Column(Float)
    free_throw_pct = Column(Float)
    offensive_rebounds_pg = Column(Float)
    assists_per_game = Column(Float)
    turnovers_per_game = Column(Float)

    # Defensive stats (per game)
    opponent_points_per_game = Column(Float)
    defensive_rebounds_pg = Column(Float)
    steals_per_game = Column(Float)
    blocks_per_game = Column(Float)

    # Advanced metrics
    pace = Column(Float)  # Possessions per 48 minutes
    offensive_rating = Column(Float)  # Points per 100 possessions
    defensive_rating = Column(Float)  # Opponent points per 100 possessions
    net_rating = Column(Float)  # Offensive rating - Defensive rating

    # Standings
    conference_rank = Column(Integer)
    division_rank = Column(Integer)
    playoff_seed = Column(Integer)  # NULL if missed playoffs

    # Timestamps
    recorded_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    team = relationship("Team")

    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uq_team_season_stats"),
        Index("ix_team_season_stats_season", "season"),
    )

    def __repr__(self):
        return f"<TeamSeasonStats {self.team_id} {self.season}: {self.wins}-{self.losses}>"


class TeamPrediction(Base):
    """
    LSTM model predictions for end-of-season team statistics.
    Stores predicted values with confidence bounds.
    """
    __tablename__ = "team_predictions"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    season = Column(String(10), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False)
    model_version = Column(String(50), nullable=False)  # e.g., "lstm_v1.0"

    # Predicted record
    predicted_wins = Column(Float)
    predicted_losses = Column(Float)
    predicted_win_pct = Column(Float)

    # Predicted rankings
    predicted_conference_rank = Column(Integer)
    playoff_probability = Column(Float)  # 0.0 to 1.0

    # Predicted per-game stats
    predicted_ppg = Column(Float)
    predicted_oppg = Column(Float)
    predicted_pace = Column(Float)
    predicted_defensive_rating = Column(Float)

    # Confidence intervals
    wins_lower_bound = Column(Float)
    wins_upper_bound = Column(Float)

    # Timestamp
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    team = relationship("Team")

    __table_args__ = (
        Index("ix_team_predictions_date", "prediction_date"),
        Index("ix_team_predictions_season_team", "season", "team_id"),
    )

    def __repr__(self):
        return f"<TeamPrediction {self.team_id} {self.season}: {self.predicted_wins:.1f} wins>"


class ModelMetadata(Base):
    """
    Track LSTM model training runs and performance metrics.
    Used for model versioning and monitoring.
    """
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True)
    model_version = Column(String(50), nullable=False, unique=True)
    model_type = Column(String(50), default="lstm")  # lstm, gru, etc.

    # Training info
    trained_at = Column(DateTime, server_default=func.now())
    training_seasons = Column(JSON)  # ["2020-21", "2021-22", ...]
    epochs_trained = Column(Integer)
    batch_size = Column(Integer)
    sequence_length = Column(Integer)  # Number of time steps

    # Architecture
    hidden_units = Column(JSON)  # [64, 32] for 2 LSTM layers
    dropout_rate = Column(Float)
    learning_rate = Column(Float)

    # Performance metrics
    training_loss = Column(Float)
    validation_loss = Column(Float)
    mae_wins = Column(Float)  # Mean Absolute Error for wins prediction
    mae_ppg = Column(Float)  # Mean Absolute Error for PPG prediction

    # Model storage paths
    model_path = Column(String(500))  # Path to saved model weights
    scaler_path = Column(String(500))  # Path to saved feature scaler

    # Deployment status
    is_active = Column(Boolean, default=False)  # Currently deployed model

    def __repr__(self):
        return f"<ModelMetadata {self.model_version} active={self.is_active}>"
