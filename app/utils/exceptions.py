# app/utils/exceptions.py

class NumerusXBaseError(Exception):
    """Base exception for all custom errors in NumerusX."""
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message

    def __str__(self):
        if self.original_exception:
            return f"{self.message}: {type(self.original_exception).__name__} - {str(self.original_exception)}"
        return self.message

# --- API Specific Errors ---
class APIError(NumerusXBaseError):
    """Base class for API related errors."""
    def __init__(self, api_name: str, message: str, status_code: int = None, original_exception: Exception = None):
        super().__init__(f"[{api_name} API Error] {message}", original_exception)
        self.api_name = api_name
        self.status_code = status_code

class JupiterAPIError(APIError):
    """Custom exception for Jupiter API errors."""
    def __init__(self, message: str, status_code: int = None, original_exception: Exception = None):
        super().__init__(api_name="Jupiter", message=message, status_code=status_code, original_exception=original_exception)

class DexScreenerAPIError(APIError):
    """Custom exception for DexScreener API errors."""
    def __init__(self, message: str, status_code: int = None, original_exception: Exception = None):
        super().__init__(api_name="DexScreener", message=message, status_code=status_code, original_exception=original_exception)

class GeminiAPIError(APIError):
    """Custom exception for Gemini API errors."""
    def __init__(self, message: str, status_code: int = None, cost: float = None, original_exception: Exception = None):
        super().__init__(api_name="Gemini", message=message, status_code=status_code, original_exception=original_exception)
        self.cost = cost

# --- Application Logic Errors ---
class ConfigurationError(NumerusXBaseError):
    """Exception for configuration related errors."""
    pass

class InsufficientDataError(NumerusXBaseError):
    """Raised when not enough data is available for an operation."""
    pass

class TradingError(NumerusXBaseError):
    """Base class for trading related errors."""
    pass

class SwapExecutionError(TradingError):
    """Raised when a swap execution fails."""
    pass

class OrderPlacementError(TradingError):
    """Raised when placing an order (limit, DCA) fails."""
    pass

class RiskManagementError(NumerusXBaseError):
    """Raised for errors within the RiskManager."""
    pass

class AIAgentError(NumerusXBaseError):
    """Raised for errors specific to the AIAgent's operations."""
    pass

class DatabaseError(NumerusXBaseError):
    """Raised for database-related errors."""
    pass

# --- Transaction Specific Solana Errors (can wrap solders/solana errors) ---
class SolanaTransactionError(TradingError):
    """Base for Solana transaction errors."""
    def __init__(self, message: str, signature: str = None, original_exception: Exception = None):
        super().__init__(message, original_exception)
        self.signature = signature

class TransactionSimulationError(SolanaTransactionError):
    """Raised when a transaction simulation fails."""
    pass

class TransactionBroadcastError(SolanaTransactionError):
    """Raised when broadcasting a transaction fails."""
    pass

class TransactionConfirmationError(SolanaTransactionError):
    """Raised when a transaction confirmation times out or fails."""
    pass

class TransactionExpiredError(SolanaTransactionError):
    """Raised when a transaction expires due to blockhash or last valid block height issues."""
    pass 