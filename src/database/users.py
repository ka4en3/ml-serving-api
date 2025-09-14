"""User database management (in-memory for simplicity)."""

import uuid
from typing import Optional, Dict, List
from datetime import datetime

from ..auth.models import UserRole
from ..auth.security import get_password_hash, verify_password

# In-memory user storage (in production -> real database)
users_db: Dict[str, dict] = {
    "admin_id": {
        "id": "admin_id",
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": get_password_hash("Admin123!"),
        "role": UserRole.ADMIN,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    "user_id": {
        "id": "user_id",
        "username": "testuser",
        "email": "user@example.com",
        "full_name": "Test User",
        "hashed_password": get_password_hash("User123!"),
        "role": UserRole.USER,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
}


def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username."""
    for user in users_db.values():
        if user["username"] == username:
            return user
    return None


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    for user in users_db.values():
        if user["email"] == email:
            return user
    return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    return users_db.get(user_id)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate user by username/email and password.

    Args:
        username: Username or email
        password: Plain password

    Returns:
        User data if authentication successful, None otherwise
    """
    # Try to find user by username or email
    user = get_user_by_username(username)
    if not user:
        user = get_user_by_email(username)

    if not user:
        return None

    if not verify_password(password, user["hashed_password"]):
        return None

    return user


def create_user(user_data: dict) -> dict:
    """
    Create a new user.

    Args:
        user_data: User data dictionary

    Returns:
        Created user data

    Raises:
        ValueError: If username or email already exists
    """
    # Check if username exists
    if get_user_by_username(user_data["username"]):
        raise ValueError("Username already registered")

    # Check if email exists
    if get_user_by_email(user_data["email"]):
        raise ValueError("Email already registered")

    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.utcnow()

    user = {
        "id": user_id,
        "username": user_data["username"],
        "email": user_data["email"],
        "full_name": user_data.get("full_name"),
        "hashed_password": get_password_hash(user_data["password"]),
        "role": user_data.get("role", UserRole.USER),
        "is_active": user_data.get("is_active", True),
        "created_at": now,
        "updated_at": now
    }

    users_db[user_id] = user
    return user


def update_user_password(user_id: str, new_password: str) -> bool:
    """Update user password."""
    user = users_db.get(user_id)
    if not user:
        return False

    user["hashed_password"] = get_password_hash(new_password)
    user["updated_at"] = datetime.utcnow()
    return True


def list_users(skip: int = 0, limit: int = 100) -> List[dict]:
    """List all users with pagination."""
    users = list(users_db.values())
    return users[skip: skip + limit]


def delete_user(user_id: str) -> bool:
    """Delete user by ID."""
    if user_id in users_db:
        del users_db[user_id]
        return True
    return False