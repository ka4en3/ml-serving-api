# ML Model Serving API

REST API for serving ML models using FastAPI.

## Features

- FastAPI-based REST API
- Sentiment analysis using Hugging Face transformers
- Automatic model loading and caching
- Input validation with Pydantic
- Comprehensive error handling
- Health check endpoints
- Automatic API documentation

## Quick Start

### Prerequisites

- Python 3.9+
- UV package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ka4en3/ml-serving-api.git
```

2. Create virtual environment and install dependencies:
```bash
uv venv
uv sync
```

### Running the Application

1. Activate the virtual environment.

2. Start the server:
```bash
uv run uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Root
- `GET /` - API information

### Health Check
- `GET /health` - Service health status

### Model Information
- `GET /model/info` - Get model details

### Prediction
- `POST /predict` - Make sentiment prediction

Example request:
```json
{
  "text": "I love this product!"
}
```

Example response:
```json
{
  "label": "POSITIVE",
  "score": 0.9998,
  "text": "I love this product!"
}
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Project Structure

```
ml-serving-api/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point for FastAPI app
│   ├── models.py            # Pydantic models for request/response
│   ├── ml_service.py        # ML model logic
│   └── config.py            # Configuration settings
├── tests/
│   ├── __init__.py
│   └── test_api.py          # API tests
├── .env                     # Environment variables
├── .gitignore
├── pyproject.toml           # Project configuration for UV
└── README.md 
```

## Environment Variables

See `.env` file for configuration options:

- `DEBUG` - Enable debug mode
- `MODEL_NAME` - Hugging Face model name
- `API_PORT` - API server port

## License

MIT License © ka4en3
