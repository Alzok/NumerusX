import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    """Mock authentication service."""
    with patch('app.api.v1.auth_routes.verify_user_credentials') as mock:
        yield mock


@pytest.fixture
def mock_jwt_service():
    """Mock JWT service."""
    with patch('app.api.v1.auth_routes.create_access_token') as mock:
        yield mock


@pytest.fixture
def valid_credentials():
    """Valid user credentials."""
    return {
        "username": "admin",
        "password": "correct_password"
    }


@pytest.fixture
def invalid_credentials():
    """Invalid user credentials."""
    return {
        "username": "admin",
        "password": "wrong_password"
    }


class TestAuthRoutes:
    """Test cases for authentication routes."""

    def test_login_success(self, client, mock_auth_service, mock_jwt_service, valid_credentials):
        """Test successful login."""
        # Mock authentication
        mock_auth_service.return_value = True
        mock_jwt_service.return_value = "fake_jwt_token"

        # Make request
        response = client.post("/api/v1/auth/login", data=valid_credentials)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["access_token"] == "fake_jwt_token"
        assert response_data["token_type"] == "bearer"
        assert response_data["user"]["username"] == "admin"

        # Verify mocks were called
        mock_auth_service.assert_called_once_with("admin", "correct_password")
        mock_jwt_service.assert_called_once()

    def test_login_invalid_credentials(self, client, mock_auth_service, invalid_credentials):
        """Test login with invalid credentials."""
        # Mock authentication failure
        mock_auth_service.return_value = False

        # Make request
        response = client.post("/api/v1/auth/login", data=invalid_credentials)

        # Assertions
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["detail"] == "Invalid credentials"

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        # Make request without credentials
        response = client.post("/api/v1/auth/login", data={})

        # Assertions
        assert response.status_code == 422  # Unprocessable Entity

    def test_login_partial_credentials(self, client):
        """Test login with partial credentials."""
        # Make request with only username
        response = client.post("/api/v1/auth/login", data={"username": "admin"})

        # Assertions
        assert response.status_code == 422

    @patch('app.api.v1.auth_routes.get_current_user')
    def test_logout_success(self, mock_get_user, client):
        """Test successful logout."""
        # Mock current user
        mock_user = MagicMock()
        mock_user.username = "admin"
        mock_get_user.return_value = mock_user

        # Mock JWT token
        headers = {"Authorization": "Bearer fake_jwt_token"}

        # Make request
        response = client.post("/api/v1/auth/logout", headers=headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Successfully logged out"

    def test_logout_unauthorized(self, client):
        """Test logout without authentication."""
        # Make request without token
        response = client.post("/api/v1/auth/logout")

        # Assertions
        assert response.status_code == 401

    @patch('app.api.v1.auth_routes.get_current_user')
    def test_profile_success(self, mock_get_user, client):
        """Test successful profile retrieval."""
        # Mock current user
        mock_user = MagicMock()
        mock_user.username = "admin"
        mock_user.email = "admin@example.com"
        mock_user.created_at = "2024-01-01T00:00:00Z"
        mock_get_user.return_value = mock_user

        # Mock JWT token
        headers = {"Authorization": "Bearer fake_jwt_token"}

        # Make request
        response = client.get("/api/v1/auth/profile", headers=headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["username"] == "admin"
        assert response_data["email"] == "admin@example.com"

    def test_profile_unauthorized(self, client):
        """Test profile retrieval without authentication."""
        # Make request without token
        response = client.get("/api/v1/auth/profile")

        # Assertions
        assert response.status_code == 401

    @patch('app.api.v1.auth_routes.verify_token')
    def test_verify_token_valid(self, mock_verify, client):
        """Test token verification with valid token."""
        # Mock token verification
        mock_verify.return_value = {"username": "admin", "exp": 1234567890}

        # Mock JWT token
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Make request
        response = client.get("/api/v1/auth/verify", headers=headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["valid"] is True
        assert response_data["username"] == "admin"

    @patch('app.api.v1.auth_routes.verify_token')
    def test_verify_token_invalid(self, mock_verify, client):
        """Test token verification with invalid token."""
        # Mock token verification failure
        mock_verify.side_effect = Exception("Invalid token")

        # Mock JWT token
        headers = {"Authorization": "Bearer invalid_jwt_token"}

        # Make request
        response = client.get("/api/v1/auth/verify", headers=headers)

        # Assertions
        assert response.status_code == 401

    def test_verify_token_missing(self, client):
        """Test token verification without token."""
        # Make request without token
        response = client.get("/api/v1/auth/verify")

        # Assertions
        assert response.status_code == 401 