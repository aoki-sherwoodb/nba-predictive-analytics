"""
Data Preprocessor for LSTM Training.
Handles feature scaling, sequence creation, and data transformation.
"""
import logging
from typing import Tuple, Optional
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler, StandardScaler

logger = logging.getLogger(__name__)


class LSTMDataPreprocessor:
    """
    Preprocessor for LSTM training data.

    Handles:
    - Feature scaling (MinMaxScaler for bounded features, StandardScaler for others)
    - Target scaling for normalized predictions
    - Train/validation splitting
    - Scaler persistence for inference
    """

    def __init__(self, feature_scaler_type: str = "minmax"):
        """
        Initialize the preprocessor.

        Args:
            feature_scaler_type: Type of scaler for features ('minmax' or 'standard')
        """
        if feature_scaler_type == "minmax":
            self.feature_scaler = MinMaxScaler()
        else:
            self.feature_scaler = StandardScaler()

        self.target_scaler = MinMaxScaler()
        self.is_fitted = False

        # Target variable names for reference
        self.target_names = [
            "wins", "losses", "win_pct", "conf_rank", "playoff_prob",
            "ppg", "oppg", "pace", "def_rating"
        ]

        # Feature names for reference
        self.feature_names = [
            "games_played", "window_wins", "window_losses", "running_win_pct",
            "ppg", "fg_pct", "fg3_pct", "ft_pct", "ast", "reb",
            "tov", "stl", "blk", "oreb", "dreb", "plus_minus",
            "pace", "off_rating", "def_rating", "net_rating"
        ]

    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Fit the scalers on training data.

        Args:
            X: Training features of shape (samples, sequence_length, num_features)
            y: Training targets of shape (samples, num_targets)
        """
        # Reshape X for fitting: (samples * sequence_length, num_features)
        n_samples, seq_len, n_features = X.shape
        X_reshaped = X.reshape(-1, n_features)

        self.feature_scaler.fit(X_reshaped)
        self.target_scaler.fit(y)
        self.is_fitted = True

        logger.info(
            f"Fitted scalers on {n_samples} samples with "
            f"sequence length {seq_len} and {n_features} features"
        )

    def transform(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Transform features and optionally targets using fitted scalers.

        Args:
            X: Features of shape (samples, sequence_length, num_features)
            y: Optional targets of shape (samples, num_targets)

        Returns:
            Tuple of (transformed_X, transformed_y or None)
        """
        if not self.is_fitted:
            raise RuntimeError("Scalers must be fitted before transform. Call fit() first.")

        n_samples, seq_len, n_features = X.shape

        # Transform features
        X_reshaped = X.reshape(-1, n_features)
        X_scaled = self.feature_scaler.transform(X_reshaped)
        X_scaled = X_scaled.reshape(n_samples, seq_len, n_features)

        # Transform targets if provided
        y_scaled = None
        if y is not None:
            y_scaled = self.target_scaler.transform(y)

        return X_scaled, y_scaled

    def fit_transform(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit scalers and transform data in one step.

        Args:
            X: Training features
            y: Training targets

        Returns:
            Tuple of (transformed_X, transformed_y)
        """
        self.fit(X, y)
        return self.transform(X, y)

    def inverse_transform_targets(self, y_scaled: np.ndarray) -> np.ndarray:
        """
        Convert scaled predictions back to original scale.

        Args:
            y_scaled: Scaled predictions of shape (samples, num_targets)

        Returns:
            Predictions in original scale
        """
        if not self.is_fitted:
            raise RuntimeError("Scalers must be fitted before inverse_transform.")

        return self.target_scaler.inverse_transform(y_scaled)

    def inverse_transform_features(self, X_scaled: np.ndarray) -> np.ndarray:
        """
        Convert scaled features back to original scale.

        Args:
            X_scaled: Scaled features of shape (samples, sequence_length, num_features)

        Returns:
            Features in original scale
        """
        if not self.is_fitted:
            raise RuntimeError("Scalers must be fitted before inverse_transform.")

        n_samples, seq_len, n_features = X_scaled.shape
        X_reshaped = X_scaled.reshape(-1, n_features)
        X_original = self.feature_scaler.inverse_transform(X_reshaped)
        return X_original.reshape(n_samples, seq_len, n_features)

    def save(self, path: str):
        """
        Save fitted scalers to file.

        Args:
            path: Path to save the scalers (without extension)
        """
        if not self.is_fitted:
            raise RuntimeError("Scalers must be fitted before saving.")

        data = {
            "feature_scaler": self.feature_scaler,
            "target_scaler": self.target_scaler,
            "target_names": self.target_names,
            "feature_names": self.feature_names,
        }
        joblib.dump(data, f"{path}.joblib")
        logger.info(f"Scalers saved to {path}.joblib")

    def load(self, path: str):
        """
        Load fitted scalers from file.

        Args:
            path: Path to the saved scalers (without extension)
        """
        data = joblib.load(f"{path}.joblib")
        self.feature_scaler = data["feature_scaler"]
        self.target_scaler = data["target_scaler"]
        self.target_names = data.get("target_names", self.target_names)
        self.feature_names = data.get("feature_names", self.feature_names)
        self.is_fitted = True
        logger.info(f"Scalers loaded from {path}.joblib")


def train_val_split(
    X: np.ndarray,
    y: np.ndarray,
    val_ratio: float = 0.2,
    shuffle: bool = True,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split data into training and validation sets.

    Args:
        X: Features array
        y: Targets array
        val_ratio: Proportion for validation set
        shuffle: Whether to shuffle before splitting
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (X_train, X_val, y_train, y_val)
    """
    n_samples = len(X)

    if shuffle:
        np.random.seed(random_state)
        indices = np.random.permutation(n_samples)
    else:
        indices = np.arange(n_samples)

    val_size = int(n_samples * val_ratio)
    train_indices = indices[val_size:]
    val_indices = indices[:val_size]

    X_train = X[train_indices]
    X_val = X[val_indices]
    y_train = y[train_indices]
    y_val = y[val_indices]

    logger.info(
        f"Split data: {len(X_train)} training samples, "
        f"{len(X_val)} validation samples"
    )

    return X_train, X_val, y_train, y_val


def normalize_conference_rank(ranks: np.ndarray) -> np.ndarray:
    """
    Normalize conference rank to 0-1 scale.
    Rank 1 = 1.0, Rank 15 = 0.0

    Args:
        ranks: Array of conference ranks (1-15)

    Returns:
        Normalized ranks (0-1)
    """
    return 1.0 - (ranks - 1) / 14


def denormalize_conference_rank(normalized: np.ndarray) -> np.ndarray:
    """
    Convert normalized rank back to 1-15 scale.

    Args:
        normalized: Normalized ranks (0-1)

    Returns:
        Conference ranks (1-15)
    """
    ranks = 1 + (1.0 - normalized) * 14
    return np.round(ranks).astype(int)


def clip_predictions(predictions: np.ndarray) -> np.ndarray:
    """
    Clip predictions to valid ranges.

    Args:
        predictions: Raw model predictions (samples, 9)

    Returns:
        Clipped predictions with valid values
    """
    clipped = predictions.copy()

    # wins: 0-82
    clipped[:, 0] = np.clip(predictions[:, 0], 0, 82)
    # losses: 0-82
    clipped[:, 1] = np.clip(predictions[:, 1], 0, 82)
    # win_pct: 0-1
    clipped[:, 2] = np.clip(predictions[:, 2], 0, 1)
    # conf_rank: 1-15
    clipped[:, 3] = np.clip(np.round(predictions[:, 3]), 1, 15)
    # playoff_prob: 0-1
    clipped[:, 4] = np.clip(predictions[:, 4], 0, 1)
    # ppg: 90-140
    clipped[:, 5] = np.clip(predictions[:, 5], 90, 140)
    # oppg: 90-140
    clipped[:, 6] = np.clip(predictions[:, 6], 90, 140)
    # pace: 90-110
    clipped[:, 7] = np.clip(predictions[:, 7], 90, 110)
    # def_rating: 95-125
    clipped[:, 8] = np.clip(predictions[:, 8], 95, 125)

    return clipped
