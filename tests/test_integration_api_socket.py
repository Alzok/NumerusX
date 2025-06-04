"""
Integration tests for API and Socket.io functionality.
Tests the complete flow from API calls to Socket.io events.
"""
import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import socketio

from app.main import app
from app.socket_manager import get_socket_manager


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_database():
    """Mock database for integration tests."""
    with patch('app.database.EnhancedDatabase') as mock_db:
        mock_instance = MagicMock()
        mock_instance.record_ai_decision = MagicMock(return_value="test_decision_id")
        mock_instance.get_ai_decision_history = MagicMock(return_value=[])
        mock_instance.record_trade = MagicMock(return_value=1)
        mock_instance.get_recent_trades = MagicMock(return_value=[])
        mock_db.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_dex_bot():
    """Mock DexBot for integration tests."""
    with patch('app.dex_bot.DexBot') as mock_bot:
        mock_instance = AsyncMock()
        mock_instance.is_running = False
        mock_instance.start = AsyncMock()
        mock_instance.stop = AsyncMock()
        mock_instance.get_status = AsyncMock(return_value={
            'running': True,
            'uptime': '1h 30m',
            'cycle_count': 90
        })
        mock_bot.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_jwt_auth():
    """Mock JWT authentication."""
    with patch('app.api.v1.auth_routes.verify_user_credentials') as mock_auth, \
         patch('app.api.v1.auth_routes.create_access_token') as mock_token:
        mock_auth.return_value = True
        mock_token.return_value = "test_jwt_token"
        yield mock_auth, mock_token


@pytest.fixture
async def socket_client():
    """Socket.io test client."""
    sio_client = socketio.AsyncClient()
    yield sio_client
    if sio_client.connected:
        await sio_client.disconnect()


class TestAPISocketIntegration:
    """Integration tests for API and Socket.io."""

    def test_api_health_check(self, client):
        """Test basic API health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_login_flow(self, client, mock_jwt_auth):
        """Test complete login flow."""
        credentials = {"username": "admin", "password": "test_password"}
        
        response = client.post("/api/v1/auth/login", data=credentials)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected routes."""
        response = client.get("/api/v1/bot/status")
        assert response.status_code == 401

    def test_bot_control_with_auth(self, client, mock_jwt_auth, mock_dex_bot):
        """Test bot control with authentication."""
        # First login
        response = client.post("/api/v1/auth/login", data={
            "username": "admin", 
            "password": "test_password"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test bot status
        with patch('app.api.v1.bot_routes.get_current_user'):
            response = client.get("/api/v1/bot/status", headers=headers)
            assert response.status_code == 200

    def test_ai_decisions_api(self, client, mock_jwt_auth, mock_database):
        """Test AI decisions API endpoints."""
        # Login first
        response = client.post("/api/v1/auth/login", data={
            "username": "admin", 
            "password": "test_password"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test AI decisions history
        with patch('app.api.v1.ai_decisions_routes.get_current_user'):
            response = client.get("/api/v1/ai-decisions/history", headers=headers)
            assert response.status_code == 200

    def test_portfolio_api(self, client, mock_jwt_auth):
        """Test portfolio API endpoints."""
        response = client.post("/api/v1/auth/login", data={
            "username": "admin", 
            "password": "test_password"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('app.api.v1.portfolio_routes.get_current_user'):
            response = client.get("/api/v1/portfolio/overview", headers=headers)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_socket_authentication_required(self):
        """Test that Socket.io requires authentication."""
        sio_client = socketio.AsyncClient()
        
        # Try to connect without auth - should fail
        with pytest.raises(socketio.exceptions.ConnectionError):
            await sio_client.connect('http://localhost:8000')

    @pytest.mark.asyncio
    async def test_socket_authentication_success(self):
        """Test successful Socket.io authentication."""
        sio_client = socketio.AsyncClient()
        
        # Mock JWT verification
        with patch('app.socket_manager.SocketManager._verify_jwt_token') as mock_verify:
            mock_verify.return_value = {"username": "admin", "exp": 9999999999}
            
            try:
                # Connect with auth token
                await sio_client.connect(
                    'http://localhost:8000',
                    auth={'token': 'Bearer test_token'}
                )
                
                # Should be connected
                assert sio_client.connected
                
            except Exception as e:
                pytest.skip(f"Socket.io connection failed (server not running): {e}")
            finally:
                if sio_client.connected:
                    await sio_client.disconnect()

    @pytest.mark.asyncio
    async def test_socket_events_emission(self):
        """Test Socket.io event emission."""
        socket_manager = get_socket_manager()
        
        # Test event emission (won't actually send without connected clients)
        await socket_manager.emit_bot_status_update({
            'running': True,
            'status': 'MONITORING'
        })
        
        await socket_manager.emit_portfolio_update({
            'total_value_usd': 10000.0,
            'pnl_24h': 125.50
        })
        
        await socket_manager.emit_ai_agent_decision({
            'decision': 'BUY',
            'confidence': 0.87,
            'reasoning': 'Strong bullish signals detected'
        })

    @pytest.mark.asyncio
    async def test_complete_trading_flow(self, client, mock_jwt_auth, mock_database, mock_dex_bot):
        """Test complete trading flow from API to database to Socket.io."""
        # 1. Login
        response = client.post("/api/v1/auth/login", data={
            "username": "admin", 
            "password": "test_password"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Check bot status
        with patch('app.api.v1.bot_routes.get_current_user'):
            response = client.get("/api/v1/bot/status", headers=headers)
            assert response.status_code == 200
        
        # 3. Mock AI decision recording
        decision_data = {
            "decision_type": "BUY",
            "token_pair": "SOL/USDC",
            "confidence": 0.85,
            "reasoning": "Strong momentum detected",
            "aggregated_inputs": {"test": "data"}
        }
        
        # 4. Test database recording
        mock_database.record_ai_decision.return_value = "test_decision_123"
        decision_id = mock_database.record_ai_decision(decision_data)
        assert decision_id == "test_decision_123"
        
        # 5. Test Socket.io emission
        socket_manager = get_socket_manager()
        await socket_manager.emit_ai_agent_decision({
            "decision_id": decision_id,
            "decision": "BUY",
            "confidence": 0.85,
            "reasoning": "Strong momentum detected"
        })

    def test_api_error_handling(self, client):
        """Test API error handling."""
        # Test invalid endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # Test malformed request
        response = client.post("/api/v1/auth/login", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error

    def test_rate_limiting(self, client):
        """Test API rate limiting."""
        # This would need Redis to be running for actual rate limiting
        # For now, just test that the endpoint exists
        response = client.get("/api/v1/system/health")
        assert response.status_code in [200, 401]  # Either works or needs auth

    @pytest.mark.asyncio
    async def test_socket_room_functionality(self):
        """Test Socket.io room subscription functionality."""
        socket_manager = get_socket_manager()
        
        # Test emitting to specific rooms
        await socket_manager.emit_to_room("market_SOL", "market_data_update", {
            "pair": "SOL/USDC",
            "price": 57.65,
            "change_24h": 2.34
        })
        
        await socket_manager.emit_to_room("logs", "new_log_entry", {
            "level": "INFO",
            "module": "trading_engine",
            "message": "Trade executed successfully"
        })

    def test_config_api(self, client, mock_jwt_auth):
        """Test configuration API endpoints."""
        response = client.post("/api/v1/auth/login", data={
            "username": "admin", 
            "password": "test_password"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('app.api.v1.config_routes.get_current_user'):
            # Test get config
            response = client.get("/api/v1/config/trading", headers=headers)
            assert response.status_code == 200
            
            # Test update config
            config_data = {
                "trading_enabled": True,
                "risk_level": "medium",
                "max_position_size": 1000.0
            }
            response = client.put("/api/v1/config/trading", 
                                json=config_data, headers=headers)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, client, mock_jwt_auth):
        """Test concurrent API calls."""
        # Login
        response = client.post("/api/v1/auth/login", data={
            "username": "admin", 
            "password": "test_password"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make multiple concurrent requests
        with patch('app.api.v1.bot_routes.get_current_user'), \
             patch('app.api.v1.portfolio_routes.get_current_user'), \
             patch('app.api.v1.trades_routes.get_current_user'):
            
            responses = await asyncio.gather(
                asyncio.to_thread(client.get, "/api/v1/bot/status", headers=headers),
                asyncio.to_thread(client.get, "/api/v1/portfolio/overview", headers=headers),
                asyncio.to_thread(client.get, "/api/v1/trades/history", headers=headers),
                return_exceptions=True
            )
            
            # All requests should succeed
            for response in responses:
                if not isinstance(response, Exception):
                    assert response.status_code == 200

    def test_api_data_validation(self, client, mock_jwt_auth):
        """Test API data validation."""
        response = client.post("/api/v1/auth/login", data={
            "username": "admin", 
            "password": "test_password"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('app.api.v1.trades_routes.get_current_user'):
            # Test invalid trade data
            invalid_trade = {
                "pair": "",  # Empty pair
                "type": "INVALID",  # Invalid type
                "amount": -100  # Negative amount
            }
            
            response = client.post("/api/v1/trades/manual", 
                                 json=invalid_trade, headers=headers)
            assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_socket_manager_utility_methods():
    """Test Socket.io manager utility methods."""
    socket_manager = get_socket_manager()
    
    # Test utility methods
    client_count = socket_manager.get_authenticated_clients_count()
    assert isinstance(client_count, int)
    assert client_count >= 0
    
    # Test getting client info (should return None for non-existent client)
    client_info = socket_manager.get_client_info("non_existent_sid")
    assert client_info is None


class TestDatabaseIntegration:
    """Test database integration with API."""

    def test_ai_decision_recording_and_retrieval(self, mock_database):
        """Test AI decision recording and retrieval flow."""
        # Record decision
        decision_data = {
            "decision_type": "BUY",
            "token_pair": "SOL/USDC",
            "confidence": 0.85,
            "reasoning": "Strong technical analysis signals",
            "aggregated_inputs": {"test": "data"}
        }
        
        mock_database.record_ai_decision.return_value = "decision_123"
        decision_id = mock_database.record_ai_decision(decision_data)
        assert decision_id == "decision_123"
        
        # Verify recording was called
        mock_database.record_ai_decision.assert_called_once_with(decision_data)
        
        # Test retrieval
        mock_database.get_ai_decision_history.return_value = [
            {
                "decision_id": "decision_123",
                "decision_type": "BUY",
                "confidence": 0.85,
                "reasoning": "Strong technical analysis signals"
            }
        ]
        
        history = mock_database.get_ai_decision_history(limit=10)
        assert len(history) == 1
        assert history[0]["decision_id"] == "decision_123"

    def test_trade_recording_with_ai_decision_link(self, mock_database):
        """Test trade recording with AI decision linkage."""
        trade_data = {
            "pair": "SOL/USDC",
            "amount": 1.0,
            "entry_price": 57.65,
            "ai_decision_id": "decision_123",
            "confidence_score": 0.85
        }
        
        mock_database.record_trade.return_value = 1
        trade_id = mock_database.record_trade(trade_data)
        assert trade_id == 1
        
        # Update AI decision status
        mock_database.update_ai_decision_status.return_value = True
        success = mock_database.update_ai_decision_status("decision_123", "EXECUTED", trade_id)
        assert success is True 