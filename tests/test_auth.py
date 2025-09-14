"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for test user."""
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "User123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    """Get authentication headers for admin user."""
    response = client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "Admin123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUser123!",
            "full_name": "New User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"


def test_register_duplicate_username(client):
    """Test registration with duplicate username."""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "Password123!"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["error"]


def test_login_success(client):
    """Test successful login."""
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "User123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_with_email(client):
    """Test login with email instead of username."""
    response = client.post(
        "/auth/login",
        data={
            "username": "user@example.com",
            "password": "User123!"
        }
    )
    assert response.status_code == 200


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "WrongPassword!"
        }
    )
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "user@example.com"


def test_get_current_user_unauthorized(client):
    """Test getting current user without auth."""
    response = client.get("/users/me")
    assert response.status_code == 401


def test_user_cannot_access_admin_endpoint(client, auth_headers):
    """Test that regular user cannot access admin endpoints."""
    response = client.get("/admin/users", headers=auth_headers)
    assert response.status_code == 403


def test_predict_with_auth(client, auth_headers):
    """Test prediction with authentication."""
    response = client.post(
        "/predict",
        json={"text": "This is amazing!"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "label" in response.json()


def test_change_password(client, auth_headers):
    """Test password change."""
    response = client.put(
        "/users/me/password",
        json={
            "current_password": "User123!",
            "new_password": "NewUser123!"
        },
        headers=auth_headers
    )
    assert response.status_code == 200

    # Try login with new password
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "NewUser123!"
        }
    )
    assert response.status_code == 200


def test_admin_get_users(client, admin_headers):
    """Test admin getting all users."""
    response = client.get("/admin/users", headers=admin_headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2  # At least admin and testuser


def test_predict_without_auth(client):
    """Test prediction without authentication."""
    response = client.post(
        "/predict",
        json={"text": "This is amazing!"}
    )
    assert response.status_code == 401