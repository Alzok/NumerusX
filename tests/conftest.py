"""
Global test configuration and fixtures for NumerusX tests.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Generator, AsyncGenerator

# Test configuration
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Mock application configuration."""
    config = {
        "SECRET_KEY": "test_secret_key",
        "JWT_SECRET_KEY": "test_jwt_secret",
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_HOURS": 24,
        "DATABASE_URL": "sqlite:///test.db",
        "REDIS_URL": "redis://localhost:6379/1",
        "REDIS_PASSWORD": "",
        "SOLANA_RPC_URL": "https://api.devnet.solana.com",
        "PRIVATE_KEY": "test_private_key",
        "JUPITER_API_URL": "https://quote-api.jup.ag/v6",
        "GEMINI_API_KEY": "test_gemini_key",
        "GEMINI_MODEL_NAME": "gemini-2.5-flash-preview-05-20",
        "LOG_LEVEL": "DEBUG",
        "TRADING_ENABLED": False,  # Disable trading in tests
        "ENABLE_UI": False
    }
    
    with patch.dict('os.environ', config):
        yield config


@pytest.fixture
def mock_database():
    """Mock database operations."""
    with patch('app.database.enhanced_database.EnhancedDatabase') as mock_db:
        mock_instance = MagicMock()
        mock_instance.add_trade = AsyncMock()
        mock_instance.get_recent_trades = AsyncMock(return_value=[])
        mock_instance.get_portfolio_balance = AsyncMock(return_value=1000.0)
        mock_instance.add_ai_decision = AsyncMock()
        mock_instance.get_ai_decisions = AsyncMock(return_value=[])
        mock_db.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('redis.asyncio.from_url') as mock_redis:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        mock_client.set = AsyncMock()
        mock_client.setex = AsyncMock()
        mock_client.delete = AsyncMock()
        mock_client.exists = AsyncMock(return_value=False)
        mock_redis.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_jupiter_client():
    """Mock Jupiter API client."""
    with patch('app.utils.jupiter_api_client.JupiterApiClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get_quote = AsyncMock(return_value={
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "inAmount": "1000000",
            "outAmount": "100000000",
            "priceImpactPct": "0.1"
        })
        mock_instance.execute_swap = AsyncMock(return_value={
            "txid": "test_transaction_id",
            "success": True
        })
        mock_instance.get_token_price = AsyncMock(return_value=100.0)
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ai_agent():
    """Mock AI Agent."""
    with patch('app.ai_agent.AIAgent') as mock_agent:
        mock_instance = AsyncMock()
        mock_instance.decide_trade = AsyncMock(return_value={
            "action": "hold",
            "confidence": 0.7,
            "reasoning": "Market conditions suggest holding position",
            "risk_assessment": "medium"
        })
        mock_agent.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini AI client."""
    with patch('app.ai_agent.GeminiClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.generate_content = AsyncMock(return_value={
            "action": "hold",
            "confidence": 0.7,
            "reasoning": "Market analysis suggests current position is optimal"
        })
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_socket_manager():
    """Mock Socket.io manager."""
    with patch('app.socket_manager.SocketManager') as mock_manager:
        mock_instance = MagicMock()
        mock_instance.emit = AsyncMock()
        mock_instance.broadcast = AsyncMock()
        mock_instance.connect_client = AsyncMock()
        mock_instance.disconnect_client = AsyncMock()
        mock_manager.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "id": 1,
        "timestamp": "2024-01-15T10:30:00Z",
        "action": "buy",
        "input_token": "SOL",
        "output_token": "USDC",
        "input_amount": 1.0,
        "output_amount": 100.0,
        "price": 100.0,
        "slippage": 0.5,
        "fee": 0.25,
        "profit_loss": 0.0,
        "success": True,
        "transaction_hash": "test_tx_hash"
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "SOL": {
            "price": 100.0,
            "change_24h": 5.0,
            "volume_24h": 1000000.0,
            "market_cap": 50000000000.0
        },
        "USDC": {
            "price": 1.0,
            "change_24h": 0.0,
            "volume_24h": 2000000.0,
            "market_cap": 55000000000.0
        }
    }


@pytest.fixture
def sample_ai_inputs():
    """Sample AI inputs for testing."""
    return {
        "market_data": {
            "current_price": 100.0,
            "price_change_24h": 5.0,
            "volume_24h": 1000000.0,
            "volatility": 0.15
        },
        "signals": {
            "rsi": 65.0,
            "macd": 0.5,
            "moving_average": 98.0,
            "bollinger_bands": {"upper": 105.0, "lower": 95.0}
        },
        "portfolio": {
            "total_value": 10000.0,
            "sol_balance": 50.0,
            "usdc_balance": 5000.0,
            "profit_loss": 500.0
        },
        "risk_metrics": {
            "portfolio_risk": 0.3,
            "market_risk": 0.4,
            "position_size_limit": 1000.0
        }
    }


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    test_env = {
        "SECRET_KEY": "test_secret",
        "JWT_SECRET_KEY": "test_jwt_secret",
        "DATABASE_URL": "sqlite:///test.db",
        "SOLANA_RPC_URL": "https://api.devnet.solana.com",
        "TRADING_ENABLED": "false",
        "ENABLE_UI": "false",
        "LOG_LEVEL": "DEBUG"
    }
    
    with patch.dict('os.environ', test_env):
        yield test_env


# Pytest marks for categorizing tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "bot: mark test as bot functionality related"
    )
    config.addinivalue_line(
        "markers", "ai: mark test as AI/ML related"
    )


# Test utilities
class TestHelpers:
    """Helper functions for tests."""
    
    @staticmethod
    def create_mock_response(status_code: int, json_data: dict = None):
        """Create a mock HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        return mock_response
    
    @staticmethod
    def create_mock_trade(trade_id: int = 1, **kwargs):
        """Create a mock trade object."""
        default_trade = {
            "id": trade_id,
            "timestamp": "2024-01-15T10:30:00Z",
            "action": "buy",
            "input_token": "SOL",
            "output_token": "USDC",
            "input_amount": 1.0,
            "output_amount": 100.0,
            "price": 100.0,
            "success": True
        }
        default_trade.update(kwargs)
        
        mock_trade = MagicMock()
        for key, value in default_trade.items():
            setattr(mock_trade, key, value)
        
        return mock_trade


@pytest.fixture
def test_helpers():
    """Provide test helper functions."""
    return TestHelpers 