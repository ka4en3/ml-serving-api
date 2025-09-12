"""Pydantic models for request and response validation."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    """Request model for text prediction."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Text to analyze sentiment",
        examples=["I love this product!", "This is terrible."]
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate and clean input text."""
        # Remove extra whitespace
        cleaned = " ".join(v.split())
        if not cleaned:
            raise ValueError("Text cannot be empty after cleaning")
        return cleaned


class PredictionResponse(BaseModel):
    """Response model for predictions."""

    label: str = Field(
        ...,
        description="Predicted sentiment label",
        examples=["POSITIVE", "NEGATIVE"]
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the prediction"
    )
    text: str = Field(
        ...,
        description="Original input text"
    )


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(default="healthy", description="Service health status")
    model_loaded: bool = Field(default=False, description="Whether ML model is loaded")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")