"""FastAPI application for ML model serving."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .models import PredictionRequest, PredictionResponse, HealthResponse, ErrorResponse
from .ml_service import get_ml_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Load model on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("Starting ML API service...")
    ml_service = get_ml_service()

    try:
        # Pre-load the model
        _ = ml_service.model
        logger.info("Model pre-loaded successfully")
    except Exception as e:
        logger.error(f"Failed to pre-load model: {str(e)}")
        # Continue running even if model fails to load initially

    yield

    # Shutdown
    logger.info("Shutting down ML API service...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="REST API for ML model inference",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=False,
    allow_methods=["GET","POST"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and model status."""
    ml_service = get_ml_service()

    return HealthResponse(
        status="healthy",
        model_loaded=ml_service.is_model_loaded(),
        version=settings.version
    )


@app.get("/model/info", response_model=dict)
async def model_info():
    """Get information about the loaded model."""
    ml_service = get_ml_service()

    try:
        return ml_service.get_model_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses={ # only for documentation
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Model error"}
    }
)
async def predict(request: PredictionRequest):
    """
    Make a prediction on the input text.

    - **text**: The text to analyze (1-512 characters)

    Returns sentiment prediction with confidence score.
    """
    ml_service = get_ml_service()

    try:
        result = ml_service.predict(request.text)
        return PredictionResponse(**result)
    except RuntimeError as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Prediction failed", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "detail": str(e)}
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


# Custom exception handler for general exceptions, used for unhandled exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Custom exception handler for general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )