"""FastAPI application for ML model serving with authentication."""

import logging
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from .config import get_settings
from .models import PredictionRequest, PredictionResponse, HealthResponse, ErrorResponse
from .ml_service import get_ml_service
from .auth.models import (
    UserCreate, UserResponse, Token,
    PasswordChange, UserRole
)
from .auth.security import create_access_token
from .auth.dependencies import (
    get_current_active_user, require_admin, require_user
)
from .database.users import (
    authenticate_user, create_user, list_users,
    update_user_password, delete_user
)

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

    logger.info("Default users created: admin (Admin123!), testuser (User123!)")

    yield

    # Shutdown
    logger.info("Shutting down ML API service...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="REST API for ML model inference with JWT authentication and RBAC",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Public Endpoints ====================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
        "authentication": "JWT Bearer token required for protected endpoints"
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


# ==================== Authentication Endpoints ====================

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    """
    Register a new user.

    Default role is 'user'. Only admins can create users with different roles.
    """
    try:
        user_data = user.model_dump()
        # Force regular user role for self-registration
        user_data["role"] = UserRole.USER

        created_user = create_user(user_data)
        return UserResponse(**created_user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with username/email and password.

    Returns JWT access token.
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "user_id": user["id"],
            "role": user["role"]
        },
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


# ==================== User Management Endpoints ====================

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: dict = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse(**current_user)


@app.put("/users/me/password")
async def change_password(
        password_change: PasswordChange,
        current_user: dict = Depends(get_current_active_user)
):
    """Change current user password."""
    # Verify current password
    if not authenticate_user(current_user["username"], password_change.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update password
    if update_user_password(current_user["id"], password_change.new_password):
        return {"message": "Password updated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )


# ==================== Admin Endpoints ====================

@app.get("/admin/users", response_model=list[UserResponse])
async def get_all_users(
        skip: int = 0,
        limit: int = 100,
        current_user: dict = Depends(require_admin)
):
    """
    Get all users (admin only).

    Requires admin role.
    """
    users = list_users(skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]


@app.post("/admin/users", response_model=UserResponse)
async def create_user_admin(
        user: UserCreate,
        current_user: dict = Depends(require_admin)
):
    """
    Create a new user with any role (admin only).

    Requires admin role.
    """
    try:
        created_user = create_user(user.model_dump())
        return UserResponse(**created_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/admin/users/{user_id}")
async def delete_user_admin(
        user_id: str,
        current_user: dict = Depends(require_admin)
):
    """
    Delete a user (admin only).

    Requires admin role.
    """
    user_id = user_id.strip()

    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    if delete_user(user_id):
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# ==================== ML Endpoints (Protected) ====================

@app.get("/model/info", response_model=dict)
async def model_info(
        current_user: dict = Depends(get_current_active_user)
):
    """
    Get information about the loaded model.

    Requires authentication.
    """
    ml_service = get_ml_service()

    try:
        return ml_service.get_model_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses={  # only for documentation
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Model error"}
    }
)
async def predict(
        request: PredictionRequest,
        current_user: dict = Depends(require_user)
):
    """
    Make a prediction on the input text.

    - **text**: The text to analyze (1-512 characters)
    - Requires user or admin role

    Returns sentiment prediction with confidence score.
    """
    ml_service = get_ml_service()

    # Log prediction request
    logger.info(f"Prediction request from user: {current_user['username']}")

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


# ==================== Exception Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


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
