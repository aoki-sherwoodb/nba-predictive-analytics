"""
PyTorch LSTM Model for NBA End-of-Season Predictions.
Predicts team statistics including wins, playoff probability, PPG, etc.
"""
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

logger = logging.getLogger(__name__)


class NBALSTMPredictor(nn.Module):
    """
    LSTM-based neural network for predicting end-of-season NBA team statistics.

    Architecture:
    - Input: (batch, sequence_length, num_features)
    - 2-layer LSTM with dropout
    - Fully connected layers for multi-output regression

    Outputs 9 predictions:
    - Wins, Losses, Win%
    - Conference Rank, Playoff Probability
    - PPG, OPPG, Pace, Defensive Rating
    """

    def __init__(
        self,
        num_features: int = 20,
        hidden_size: int = 64,
        num_layers: int = 2,
        num_targets: int = 9,
        dropout_rate: float = 0.2,
    ):
        """
        Initialize the LSTM model.

        Args:
            num_features: Number of input features per time step
            hidden_size: Number of hidden units in LSTM layers
            num_layers: Number of stacked LSTM layers
            num_targets: Number of output predictions
            dropout_rate: Dropout probability for regularization
        """
        super(NBALSTMPredictor, self).__init__()

        self.num_features = num_features
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_targets = num_targets

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=num_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout_rate if num_layers > 1 else 0,
        )

        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(32, num_targets)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.

        Args:
            x: Input tensor of shape (batch, sequence_length, num_features)

        Returns:
            Predictions tensor of shape (batch, num_targets)
        """
        # LSTM forward pass
        # lstm_out shape: (batch, seq_len, hidden_size)
        # h_n shape: (num_layers, batch, hidden_size)
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Take the last hidden state from the final layer
        last_hidden = h_n[-1]  # Shape: (batch, hidden_size)

        # Fully connected layers
        out = self.fc1(last_hidden)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)

        return out


class LSTMTrainer:
    """
    Training and inference utilities for the LSTM model.
    Handles training loop, evaluation, and model persistence.
    """

    def __init__(
        self,
        model: NBALSTMPredictor,
        learning_rate: float = 0.001,
        device: Optional[str] = None,
    ):
        """
        Initialize the trainer.

        Args:
            model: NBALSTMPredictor model instance
            learning_rate: Learning rate for optimizer
            device: Device to use ('cuda', 'mps', or 'cpu'). Auto-detected if None.
        """
        self.model = model

        # Auto-detect device
        if device is None:
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        self.model.to(self.device)
        logger.info(f"Using device: {self.device}")

        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        self.learning_rate = learning_rate

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 100,
        patience: int = 15,
    ) -> Dict:
        """
        Train the LSTM model with early stopping.

        Args:
            train_loader: DataLoader for training data
            val_loader: DataLoader for validation data
            epochs: Maximum number of training epochs
            patience: Early stopping patience

        Returns:
            Dictionary with training history and metrics
        """
        history = {
            "train_loss": [],
            "val_loss": [],
            "best_epoch": 0,
            "best_val_loss": float("inf"),
        }

        best_model_state = None
        patience_counter = 0

        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_losses = []

            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)

                self.optimizer.zero_grad()
                predictions = self.model(batch_X)
                loss = self.criterion(predictions, batch_y)
                loss.backward()
                self.optimizer.step()

                train_losses.append(loss.item())

            avg_train_loss = np.mean(train_losses)
            history["train_loss"].append(avg_train_loss)

            # Validation phase
            self.model.eval()
            val_losses = []

            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device)

                    predictions = self.model(batch_X)
                    loss = self.criterion(predictions, batch_y)
                    val_losses.append(loss.item())

            avg_val_loss = np.mean(val_losses)
            history["val_loss"].append(avg_val_loss)

            # Early stopping check
            if avg_val_loss < history["best_val_loss"]:
                history["best_val_loss"] = avg_val_loss
                history["best_epoch"] = epoch
                best_model_state = self.model.state_dict().copy()
                patience_counter = 0
            else:
                patience_counter += 1

            if epoch % 10 == 0 or epoch == epochs - 1:
                logger.info(
                    f"Epoch {epoch + 1}/{epochs} - "
                    f"Train Loss: {avg_train_loss:.4f}, "
                    f"Val Loss: {avg_val_loss:.4f}"
                )

            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch + 1}")
                break

        # Restore best model
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)

        return history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Generate predictions for input data.

        Args:
            X: Input array of shape (samples, sequence_length, num_features)

        Returns:
            Predictions array of shape (samples, num_targets)
        """
        self.model.eval()

        X_tensor = torch.FloatTensor(X).to(self.device)

        with torch.no_grad():
            predictions = self.model(X_tensor)

        return predictions.cpu().numpy()

    def evaluate(self, test_loader: DataLoader) -> Dict:
        """
        Evaluate model on test data.

        Args:
            test_loader: DataLoader for test data

        Returns:
            Dictionary with evaluation metrics
        """
        self.model.eval()
        all_predictions = []
        all_targets = []

        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                batch_X = batch_X.to(self.device)
                predictions = self.model(batch_X)
                all_predictions.append(predictions.cpu().numpy())
                all_targets.append(batch_y.numpy())

        predictions = np.concatenate(all_predictions, axis=0)
        targets = np.concatenate(all_targets, axis=0)

        # Calculate metrics
        mse = np.mean((predictions - targets) ** 2)
        mae = np.mean(np.abs(predictions - targets))

        # Per-target MAE
        target_names = [
            "wins", "losses", "win_pct", "conf_rank", "playoff_prob",
            "ppg", "oppg", "pace", "def_rating"
        ]
        per_target_mae = {}
        for i, name in enumerate(target_names):
            per_target_mae[name] = np.mean(np.abs(predictions[:, i] - targets[:, i]))

        return {
            "mse": mse,
            "mae": mae,
            "per_target_mae": per_target_mae,
        }

    def save(self, model_path: str):
        """
        Save model weights to file.

        Args:
            model_path: Path to save the model
        """
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "model_config": {
                "num_features": self.model.num_features,
                "hidden_size": self.model.hidden_size,
                "num_layers": self.model.num_layers,
                "num_targets": self.model.num_targets,
            },
        }, model_path)
        logger.info(f"Model saved to {model_path}")

    def load(self, model_path: str):
        """
        Load model weights from file.

        Args:
            model_path: Path to the saved model
        """
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        logger.info(f"Model loaded from {model_path}")


def create_data_loaders(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    batch_size: int = 16,
) -> Tuple[DataLoader, DataLoader]:
    """
    Create PyTorch DataLoaders from numpy arrays.

    Args:
        X_train: Training features
        y_train: Training targets
        X_val: Validation features
        y_val: Validation targets
        batch_size: Batch size for training

    Returns:
        Tuple of (train_loader, val_loader)
    """
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.FloatTensor(y_train)
    )
    val_dataset = TensorDataset(
        torch.FloatTensor(X_val),
        torch.FloatTensor(y_val)
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False
    )

    return train_loader, val_loader
