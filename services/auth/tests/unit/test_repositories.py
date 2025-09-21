"""Unit tests for auth repository layer."""

from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import ClientError

from services.auth.lib.modules.users.repositories import UserRepository


class TestUserRepository:
    """Test cases for UserRepository."""

    def test_create_user_success(self, mock_dynamodb):
        """Test successful user creation in DynamoDB."""
        # Arrange
        repo = UserRepository()
        repo.table = mock_dynamodb
        mock_dynamodb.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password_hash": "hashed"
        }

        # Act
        result = repo.create(user_data)

        # Assert
        assert result["email"] == "test@example.com"
        assert "id" in result
        assert "created_at" in result
        mock_dynamodb.put_item.assert_called_once()

    def test_get_user_by_id_found(self, mock_dynamodb):
        """Test getting existing user by ID."""
        # Arrange
        repo = UserRepository()
        repo.table = mock_dynamodb
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "userId": "user-123",
                "email": "test@example.com",
                "name": "Test User"
            }
        }

        # Act
        result = repo.get("user-123")

        # Assert
        assert result["userId"] == "user-123"
        assert result["email"] == "test@example.com"
        mock_dynamodb.get_item.assert_called_once_with(Key={"userId": "user-123"})

    def test_get_user_by_id_not_found(self, mock_dynamodb):
        """Test getting non-existent user by ID."""
        # Arrange
        repo = UserRepository()
        repo.table = mock_dynamodb
        mock_dynamodb.get_item.return_value = {}

        # Act
        result = repo.get("nonexistent")

        # Assert
        assert result is None
        mock_dynamodb.get_item.assert_called_once()

    def test_get_user_by_email(self, mock_dynamodb):
        """Test getting user by email using GSI."""
        # Arrange
        repo = UserRepository()
        repo.table = mock_dynamodb
        mock_dynamodb.query.return_value = {
            "Items": [{
                "userId": "user-123",
                "email": "test@example.com",
                "name": "Test User"
            }]
        }

        # Act
        result = repo.get_by_email("test@example.com")

        # Assert
        assert result["email"] == "test@example.com"
        mock_dynamodb.query.assert_called_once()

    def test_update_user_success(self, mock_dynamodb):
        """Test successful user update."""
        # Arrange
        repo = UserRepository()
        repo.table = mock_dynamodb
        mock_dynamodb.update_item.return_value = {
            "Attributes": {
                "userId": "user-123",
                "name": "Updated Name",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }

        # Act
        result = repo.update("user-123", {"name": "Updated Name"})

        # Assert
        assert result["name"] == "Updated Name"
        assert "updated_at" in result
        mock_dynamodb.update_item.assert_called_once()

    def test_delete_user_success(self, mock_dynamodb):
        """Test successful user deletion."""
        # Arrange
        repo = UserRepository()
        repo.table = mock_dynamodb
        mock_dynamodb.delete_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Act
        result = repo.delete("user-123")

        # Assert
        assert result is True
        mock_dynamodb.delete_item.assert_called_once_with(Key={"userId": "user-123"})

    def test_delete_user_error(self, mock_dynamodb):
        """Test user deletion with error."""
        # Arrange
        repo = UserRepository()
        repo.table = mock_dynamodb
        mock_dynamodb.delete_item.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}}, "DeleteItem"
        )

        # Act & Assert
        with pytest.raises(ClientError):
            repo.delete("user-123")

    def test_list_users_with_pagination(self, mock_dynamodb):
        """Test listing users with pagination."""
        # Arrange
        repo = UserRepository()
        repo.table = mock_dynamodb
        mock_dynamodb.scan.return_value = {
            "Items": [
                {"userId": "user-1", "email": "user1@example.com"},
                {"userId": "user-2", "email": "user2@example.com"}
            ],
            "LastEvaluatedKey": {"userId": "user-2"}
        }

        # Act
        result = repo.list(limit=2)

        # Assert
        assert len(result["items"]) == 2
        assert result["last_key"] == {"userId": "user-2"}
        mock_dynamodb.scan.assert_called_once()

    def test_batch_get_users(self, mock_dynamodb):
        """Test batch getting multiple users."""
        # Arrange
        repo = UserRepository()
        repo.dynamodb = MagicMock()
        batch_response = {
            "Responses": {
                "users-test": [
                    {"userId": "user-1", "email": "user1@example.com"},
                    {"userId": "user-2", "email": "user2@example.com"}
                ]
            }
        }
        repo.dynamodb.batch_get_item.return_value = batch_response

        # Act
        result = repo.batch_get(["user-1", "user-2"])

        # Assert
        assert len(result) == 2
        assert result[0]["userId"] == "user-1"
        repo.dynamodb.batch_get_item.assert_called_once()