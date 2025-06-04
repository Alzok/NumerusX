import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_auth_dependency():
    """Mock authentication dependency."""
    with patch('app.api.v1.bot_routes.get_current_user') as mock:
        mock_user = MagicMock()
        mock_user.username = "admin"
        mock.return_value = mock_user
        yield mock


@pytest.fixture
def authorized_headers():
    """Headers with valid JWT token."""
    return {"Authorization": "Bearer fake_jwt_token"}


@pytest.fixture
def mock_dex_bot():
    """Mock DexBot instance."""
    with patch('app.api.v1.bot_routes.get_dex_bot') as mock:
        mock_bot = MagicMock()
        yield mock_bot


class TestBotRoutes:
    """Test cases for bot control routes."""

    def test_start_bot_success(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test successful bot start."""
        # Mock bot state
        mock_dex_bot.is_running = False
        mock_dex_bot.start = AsyncMock()

        # Make request
        response = client.post("/api/v1/bot/start", headers=authorized_headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "Bot started successfully"
        assert response_data["bot_running"] is True

        # Verify bot was started
        mock_dex_bot.start.assert_called_once()

    def test_start_bot_already_running(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test starting bot when already running."""
        # Mock bot state
        mock_dex_bot.is_running = True

        # Make request
        response = client.post("/api/v1/bot/start", headers=authorized_headers)

        # Assertions
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["detail"] == "Bot is already running"

    def test_stop_bot_success(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test successful bot stop."""
        # Mock bot state
        mock_dex_bot.is_running = True
        mock_dex_bot.stop = AsyncMock()

        # Make request
        response = client.post("/api/v1/bot/stop", headers=authorized_headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "Bot stopped successfully"
        assert response_data["bot_running"] is False

        # Verify bot was stopped
        mock_dex_bot.stop.assert_called_once()

    def test_stop_bot_not_running(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test stopping bot when not running."""
        # Mock bot state
        mock_dex_bot.is_running = False

        # Make request
        response = client.post("/api/v1/bot/stop", headers=authorized_headers)

        # Assertions
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["detail"] == "Bot is not running"

    def test_restart_bot_success(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test successful bot restart."""
        # Mock bot methods
        mock_dex_bot.stop = AsyncMock()
        mock_dex_bot.start = AsyncMock()

        # Make request
        response = client.post("/api/v1/bot/restart", headers=authorized_headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "Bot restarted successfully"

        # Verify bot was stopped and started
        mock_dex_bot.stop.assert_called_once()
        mock_dex_bot.start.assert_called_once()

    def test_get_bot_status(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test getting bot status."""
        # Mock bot status
        mock_dex_bot.is_running = True
        mock_dex_bot.start_time = "2024-01-15T10:00:00Z"
        mock_dex_bot.cycle_count = 150
        mock_dex_bot.last_trade_time = "2024-01-15T10:30:00Z"
        mock_dex_bot.profit_loss = 25.5
        mock_dex_bot.total_trades = 5

        # Make request
        response = client.get("/api/v1/bot/status", headers=authorized_headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["running"] is True
        assert response_data["uptime"] is not None
        assert response_data["cycle_count"] == 150
        assert response_data["last_trade_time"] == "2024-01-15T10:30:00Z"
        assert response_data["performance"]["profit_loss"] == 25.5
        assert response_data["performance"]["total_trades"] == 5

    def test_get_bot_status_not_running(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test getting bot status when not running."""
        # Mock bot status
        mock_dex_bot.is_running = False
        mock_dex_bot.start_time = None

        # Make request
        response = client.get("/api/v1/bot/status", headers=authorized_headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["running"] is False
        assert response_data["uptime"] is None

    def test_emergency_stop(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test emergency stop."""
        # Mock bot methods
        mock_dex_bot.emergency_stop = AsyncMock()
        mock_dex_bot.cancel_all_orders = AsyncMock()

        # Make request
        response = client.post("/api/v1/bot/emergency-stop", headers=authorized_headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "Emergency stop executed"

        # Verify emergency stop was called
        mock_dex_bot.emergency_stop.assert_called_once()
        mock_dex_bot.cancel_all_orders.assert_called_once()

    def test_get_bot_config(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test getting bot configuration."""
        # Mock bot config
        mock_config = {
            "trading_enabled": True,
            "risk_level": "medium",
            "max_position_size": 1000.0,
            "stop_loss_percentage": 5.0,
            "take_profit_percentage": 10.0
        }
        mock_dex_bot.get_config = MagicMock(return_value=mock_config)

        # Make request
        response = client.get("/api/v1/bot/config", headers=authorized_headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["trading_enabled"] is True
        assert response_data["risk_level"] == "medium"
        assert response_data["max_position_size"] == 1000.0

    def test_update_bot_config(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test updating bot configuration."""
        # Mock bot methods
        mock_dex_bot.update_config = AsyncMock()

        # New config data
        new_config = {
            "trading_enabled": False,
            "risk_level": "low",
            "max_position_size": 500.0
        }

        # Make request
        response = client.put(
            "/api/v1/bot/config",
            json=new_config,
            headers=authorized_headers
        )

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "Configuration updated successfully"

        # Verify config was updated
        mock_dex_bot.update_config.assert_called_once_with(new_config)

    def test_unauthorized_access(self, client):
        """Test unauthorized access to bot routes."""
        # Make request without authentication
        response = client.post("/api/v1/bot/start")

        # Assertions
        assert response.status_code == 401

    def test_bot_start_exception(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test bot start with exception."""
        # Mock bot state and exception
        mock_dex_bot.is_running = False
        mock_dex_bot.start = AsyncMock(side_effect=Exception("Bot start failed"))

        # Make request
        response = client.post("/api/v1/bot/start", headers=authorized_headers)

        # Assertions
        assert response.status_code == 500
        response_data = response.json()
        assert "Failed to start bot" in response_data["detail"]

    def test_bot_statistics(self, client, mock_auth_dependency, mock_dex_bot, authorized_headers):
        """Test getting bot statistics."""
        # Mock statistics
        mock_stats = {
            "total_runtime_hours": 24.5,
            "total_cycles": 1500,
            "successful_trades": 8,
            "failed_trades": 2,
            "average_cycle_time": 60.0,
            "profit_loss_usd": 125.75,
            "profit_loss_percentage": 2.5
        }
        mock_dex_bot.get_statistics = MagicMock(return_value=mock_stats)

        # Make request
        response = client.get("/api/v1/bot/statistics", headers=authorized_headers)

        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_runtime_hours"] == 24.5
        assert response_data["successful_trades"] == 8
        assert response_data["profit_loss_usd"] == 125.75 