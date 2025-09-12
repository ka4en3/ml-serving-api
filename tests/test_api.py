"""Tests for the ML serving API."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.ml_service import get_ml_service


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data
    assert "version" in data


def test_model_info_endpoint(client):
    """Test the model info endpoint."""
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "device" in data
    assert "loaded" in data


def test_model_is_loaded(client):
    """Test the model is loaded."""
    client.post(
        "/predict",
        json={"text": "warm-up"}
    )
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert data["loaded"] == True


def test_predict_positive_sentiment(client):
    """Test prediction with positive sentiment."""
    response = client.post(
        "/predict",
        json={"text": "I absolutely love this product! It's amazing!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert "score" in data
    assert "text" in data
    assert data["label"] in ["POSITIVE", "NEGATIVE"]
    assert 0 <= data["score"] <= 1


def test_predict_negative_sentiment(client):
    """Test prediction with negative sentiment."""
    response = client.post(
        "/predict",
        json={"text": "This is terrible. I hate it."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] in ["POSITIVE", "NEGATIVE"]


def test_predict_empty_text(client):
    """Test prediction with empty text."""
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422  # Validation error


def test_predict_missing_text(client):
    """Test prediction with missing text field."""
    response = client.post("/predict", json={})
    assert response.status_code == 422  # Validation error


def test_predict_long_text(client):
    """Test prediction with text exceeding max length."""
    long_text = "a" * 1000  # Exceeds 512 character limit
    response = client.post("/predict", json={"text": long_text})
    assert response.status_code == 422  # Validation error


def test_predict_whitespace_text(client):
    """Test prediction with only whitespace."""
    response = client.post("/predict", json={"text": "   \n\t   "})
    assert response.status_code == 422  # Should fail validation

