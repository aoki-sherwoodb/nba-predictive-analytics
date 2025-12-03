"""
Model storage abstraction for local filesystem and GCS.
"""
import io
import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import torch

from config import config

logger = logging.getLogger(__name__)


class ModelStorage(ABC):
    """Abstract base class for model storage backends."""

    @abstractmethod
    def save_model(self, model: Any, name: str, metadata: dict = None) -> str:
        """Save a PyTorch model with optional metadata."""
        pass

    @abstractmethod
    def load_model(self, name: str, model_class: type = None) -> tuple[Any, dict]:
        """Load a PyTorch model and its metadata."""
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """List all available models."""
        pass

    @abstractmethod
    def delete_model(self, name: str) -> bool:
        """Delete a model."""
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if a model exists."""
        pass


class LocalModelStorage(ModelStorage):
    """Local filesystem storage for models."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or config.storage.local_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _model_path(self, name: str) -> Path:
        return self.base_path / f"{name}.pt"

    def _metadata_path(self, name: str) -> Path:
        return self.base_path / f"{name}_metadata.json"

    def save_model(self, model: Any, name: str, metadata: dict = None) -> str:
        model_path = self._model_path(name)
        torch.save(model.state_dict(), model_path)
        logger.info(f"Saved model to {model_path}")

        if metadata:
            metadata_path = self._metadata_path(name)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2, default=str)
            logger.info(f"Saved metadata to {metadata_path}")

        return str(model_path)

    def load_model(self, name: str, model_class: type = None) -> tuple[Any, dict]:
        model_path = self._model_path(name)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        state_dict = torch.load(model_path, map_location="cpu")

        metadata = {}
        metadata_path = self._metadata_path(name)
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

        return state_dict, metadata

    def list_models(self) -> list[str]:
        models = []
        for f in self.base_path.glob("*.pt"):
            models.append(f.stem)
        return models

    def delete_model(self, name: str) -> bool:
        model_path = self._model_path(name)
        metadata_path = self._metadata_path(name)

        deleted = False
        if model_path.exists():
            model_path.unlink()
            deleted = True
        if metadata_path.exists():
            metadata_path.unlink()

        return deleted

    def exists(self, name: str) -> bool:
        return self._model_path(name).exists()


class GCSModelStorage(ModelStorage):
    """Google Cloud Storage backend for models."""

    def __init__(self, bucket_name: str = None, prefix: str = None):
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError("google-cloud-storage is required for GCS backend")

        self.bucket_name = bucket_name or config.storage.gcs_bucket
        self.prefix = prefix or config.storage.gcs_prefix
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def _blob_path(self, name: str, suffix: str = ".pt") -> str:
        return f"{self.prefix}/{name}{suffix}"

    def save_model(self, model: Any, name: str, metadata: dict = None) -> str:
        # Save model to bytes buffer
        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)
        buffer.seek(0)

        # Upload to GCS
        blob_path = self._blob_path(name)
        blob = self.bucket.blob(blob_path)
        blob.upload_from_file(buffer, content_type="application/octet-stream")
        logger.info(f"Saved model to gs://{self.bucket_name}/{blob_path}")

        # Save metadata
        if metadata:
            meta_blob_path = self._blob_path(name, "_metadata.json")
            meta_blob = self.bucket.blob(meta_blob_path)
            meta_blob.upload_from_string(
                json.dumps(metadata, indent=2, default=str),
                content_type="application/json"
            )
            logger.info(f"Saved metadata to gs://{self.bucket_name}/{meta_blob_path}")

        return f"gs://{self.bucket_name}/{blob_path}"

    def load_model(self, name: str, model_class: type = None) -> tuple[Any, dict]:
        blob_path = self._blob_path(name)
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            raise FileNotFoundError(f"Model not found: gs://{self.bucket_name}/{blob_path}")

        # Download model
        buffer = io.BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)
        state_dict = torch.load(buffer, map_location="cpu")

        # Load metadata
        metadata = {}
        meta_blob_path = self._blob_path(name, "_metadata.json")
        meta_blob = self.bucket.blob(meta_blob_path)
        if meta_blob.exists():
            metadata = json.loads(meta_blob.download_as_string())

        return state_dict, metadata

    def list_models(self) -> list[str]:
        models = []
        blobs = self.client.list_blobs(self.bucket_name, prefix=self.prefix)
        for blob in blobs:
            if blob.name.endswith(".pt"):
                name = blob.name[len(self.prefix) + 1:-3]  # Remove prefix and .pt
                models.append(name)
        return models

    def delete_model(self, name: str) -> bool:
        blob_path = self._blob_path(name)
        blob = self.bucket.blob(blob_path)

        deleted = False
        if blob.exists():
            blob.delete()
            deleted = True

        meta_blob_path = self._blob_path(name, "_metadata.json")
        meta_blob = self.bucket.blob(meta_blob_path)
        if meta_blob.exists():
            meta_blob.delete()

        return deleted

    def exists(self, name: str) -> bool:
        blob_path = self._blob_path(name)
        blob = self.bucket.blob(blob_path)
        return blob.exists()


def get_model_storage() -> ModelStorage:
    """Factory function to get the appropriate storage backend."""
    backend = config.storage.backend.lower()

    if backend == "gcs":
        logger.info(f"Using GCS storage: {config.storage.gcs_bucket}/{config.storage.gcs_prefix}")
        return GCSModelStorage()
    else:
        logger.info(f"Using local storage: {config.storage.local_path}")
        return LocalModelStorage()


# Global storage instance
model_storage = get_model_storage()
