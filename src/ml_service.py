"""ML model service for sentiment analysis."""

import logging
from typing import Dict, Any, Optional
from functools import lru_cache

from transformers import pipeline, Pipeline
import torch

from .config import get_settings

logger = logging.getLogger(__name__)


class MLService:
    """Service class for managing ML model operations."""

    def __init__(self):
        self.settings = get_settings()
        self._model: Optional[Pipeline] = None
        self._device = 0 if torch.cuda.is_available() else -1

    @property
    def model(self) -> Pipeline:
        """Lazy load and cache the model."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load the sentiment analysis model."""
        try:
            logger.info(f"Loading model: {self.settings.model_name}")

            self._model = pipeline(
                "sentiment-analysis",
                model=self.settings.model_name,
                device=self._device,
                model_kwargs={"cache_dir": self.settings.model_cache_dir}
            )

            logger.info("Model loaded successfully")

            # Warm up the model with a test prediction
            self._model("test")

        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise RuntimeError(f"Model loading failed: {str(e)}")

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Make a prediction on the input text.

        Args:
            text: Input text for sentiment analysis

        Returns:
            Dictionary with prediction results
        """
        try:
            # Get prediction from model
            result = self.model(text)[0]

            # Normalize label to uppercase
            label = result["label"].upper()

            return {
                "label": label,
                "score": round(result["score"], 4),
                "text": text
            }

        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise RuntimeError(f"Prediction failed: {str(e)}")

    def is_model_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.settings.model_name,
            "device": "GPU" if self._device >= 0 else "CPU",
            "loaded": self.is_model_loaded()
        }


@lru_cache()
def get_ml_service() -> MLService:
    """Get cached ML service instance."""
    return MLService()
