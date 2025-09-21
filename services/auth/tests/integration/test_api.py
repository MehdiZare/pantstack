"""Integration tests for auth API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestAuthAPI:
    """Integration tests for auth API."""

    def test_register_user_success(self, api_client, mock_dynamodb, mock_sqs):
        """Test successful user registration."""
        # Arrange
        mock_dynamodb.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        request_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User"
        }

        # Act
        response = api_client.post("/auth/register", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_register_user_duplicate_email(self, api_client, mock_dynamodb):
        """Test registration with duplicate email."""
        # Arrange
        mock_dynamodb.query.return_value = {
            "Items": [{"email": "existing@example.com"}]
        }

        request_data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "name": "User"
        }

        # Act
        response = api_client.post("/auth/register", json=request_data)

        # Assert
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_login_success(self, api_client, mock_dynamodb):
        """Test successful login."""
        # Arrange
        with patch("bcrypt.checkpw", return_value=True):
            mock_dynamodb.query.return_value = {
                "Items": [{
                    "userId": "user-123",
                    "email": "test@example.com",
                    "password_hash": "hashed",
                    "is_active": True
                }]
            }

            request_data = {
                "email": "test@example.com",
                "password": "password123"
            }

            # Act
            response = api_client.post("/auth/login", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_login_invalid_credentials(self, api_client, mock_dynamodb):
        """Test login with invalid credentials."""
        # Arrange
        mock_dynamodb.query.return_value = {"Items": []}

        request_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }

        # Act
        response = api_client.post("/auth/login", json=request_data)

        # Assert
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_refresh_token_success(self, api_client):
        """Test successful token refresh."""
        # Arrange
        with patch("jwt.decode", return_value={"sub": "user-123", "type": "refresh"}):
            with patch("jwt.encode", return_value="new-access-token"):
                request_data = {"refresh_token": "valid-refresh-token"}

                # Act
                response = api_client.post("/auth/refresh", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-access-token"
        assert data["token_type"] == "Bearer"

    def test_refresh_token_invalid(self, api_client):
        """Test refresh with invalid token."""
        # Arrange
        with patch("jwt.decode", side_effect=Exception("Invalid token")):
            request_data = {"refresh_token": "invalid-token"}

            # Act
            response = api_client.post("/auth/refresh", json=request_data)

        # Assert
        assert response.status_code == 401

    def test_get_profile_authenticated(self, api_client, auth_headers, mock_dynamodb):
        """Test getting user profile when authenticated."""
        # Arrange
        with patch("services.auth.src.api.dependencies.verify_token", return_value={"sub": "user-123"}):
            mock_dynamodb.get_item.return_value = {
                "Item": {
                    "userId": "user-123",
                    "email": "test@example.com",
                    "name": "Test User"
                }
            }

            # Act
            response = api_client.get("/auth/profile", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_profile_unauthenticated(self, api_client):
        """Test getting profile without authentication."""
        # Act
        response = api_client.get("/auth/profile")

        # Assert
        assert response.status_code == 401

    def test_update_profile(self, api_client, auth_headers, mock_dynamodb):
        """Test updating user profile."""
        # Arrange
        with patch("services.auth.src.api.dependencies.verify_token", return_value={"sub": "user-123"}):
            mock_dynamodb.update_item.return_value = {
                "Attributes": {
                    "userId": "user-123",
                    "name": "Updated Name"
                }
            }

            request_data = {"name": "Updated Name"}

            # Act
            response = api_client.patch("/auth/profile", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_logout(self, api_client, auth_headers):
        """Test logout endpoint."""
        # Arrange
        with patch("services.auth.src.api.dependencies.verify_token", return_value={"sub": "user-123"}):
            # Act
            response = api_client.post("/auth/logout", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    def test_password_reset_request(self, api_client, mock_dynamodb, mock_sqs):
        """Test password reset request."""
        # Arrange
        mock_dynamodb.query.return_value = {
            "Items": [{"userId": "user-123", "email": "test@example.com"}]
        }
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        request_data = {"email": "test@example.com"}

        # Act
        response = api_client.post("/auth/password-reset", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "email sent" in data["message"].lower()

    def test_health_check(self, api_client):
        """Test health check endpoint."""
        # Act
        response = api_client.get("/auth/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "auth"