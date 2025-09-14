"""FastAPI dependencies for authentication and authorization."""

from typing import Optional, List
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from .security import decode_token
from .models import TokenData, UserRole
from ..database.users import get_user_by_id

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get current user from JWT token.

    Args:
        token: JWT token from Authorization header

    Returns:
        User data dictionary

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        payload = decode_token(token)
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        role: str = payload.get("role")

        if username is None or user_id is None:
            raise credentials_exception

        # token_data = TokenData(
        #     username=username,
        #     user_id=user_id,
        #     role=UserRole(role) if role else None
        # )

    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise credentials_exception
    except ValueError as e:
        logger.error(f"Invalid role in token: {str(e)}")
        raise credentials_exception

    # Get user from database
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


# async def get_current_active_user(
#         current_user: dict = Depends(get_current_user)
# ) -> dict:
#     """
#     Get current active user.
#
#     Args:
#         current_user: User data from token
#
#     Returns:
#         Active user data
#
#     Raises:
#         HTTPException: If user is inactive
#     """
#     if not current_user.get("is_active", False):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Inactive user"
#         )
#     return current_user


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control.

    Args:
        allowed_roles: List of allowed roles

    Returns:
        Dependency function that checks user role
    """

    async def role_checker(
            current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        """Check if user has required role."""
        user_role = UserRole(current_user.get("role", UserRole.GUEST))

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required roles: {allowed_roles}"
            )

        return current_user

    return role_checker


# Pre-defined role dependencies
require_admin = require_role([UserRole.ADMIN])
require_user = require_role([UserRole.ADMIN, UserRole.USER])
require_any = require_role([UserRole.ADMIN, UserRole.USER, UserRole.GUEST])