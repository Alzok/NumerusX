"""
Transaction Handler Interface and Implementations for NumerusX.
Supports Test (simulation) and Production (real transactions) modes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import time
import uuid
from datetime import datetime
from enum import Enum

from app.config import get_config
from app.database import EnhancedDatabase

logger = logging.getLogger(__name__)

class TransactionMode(str, Enum):
    """Transaction modes."""
    TEST = "test"
    PRODUCTION = "production"

class TransactionStatus(str, Enum):
    """Transaction status."""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    SIMULATED = "SIMULATED"

class TransactionHandler(ABC):
    """
    Abstract base class for transaction handlers.
    Implements the Strategy pattern for Test vs Production modes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = EnhancedDatabase()
    
    @abstractmethod
    async def execute_swap(
        self,
        input_token_mint: str,
        output_token_mint: str,
        amount_in_tokens: Optional[float] = None,
        amount_in_usd: Optional[float] = None,
        slippage_bps: Optional[int] = None,
        swap_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a token swap.
        
        Returns:
            Dict containing:
            - success: bool
            - signature: str (transaction signature or simulation ID)
            - details: dict with swap details
            - mode: str (test or production)
        """
        pass
    
    @abstractmethod
    async def check_balance(self, wallet_address: str, token_mint: str) -> Dict[str, Any]:
        """
        Check token balance for a wallet.
        
        Returns:
            Dict containing:
            - success: bool
            - balance: float
            - token_mint: str
            - mode: str
        """
        pass
    
    @abstractmethod
    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        """
        Get status of a transaction.
        
        Returns:
            Dict containing:
            - success: bool
            - status: TransactionStatus
            - details: dict
        """
        pass
    
    @abstractmethod
    def get_mode(self) -> TransactionMode:
        """Get the current transaction mode."""
        pass
    
    async def log_transaction(
        self,
        transaction_type: str,
        details: Dict[str, Any],
        status: TransactionStatus,
        signature: Optional[str] = None
    ) -> bool:
        """Log transaction to database."""
        try:
            log_data = {
                'transaction_type': transaction_type,
                'signature': signature,
                'status': status.value,
                'details': details,
                'mode': self.get_mode().value,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return self.db.record_system_log(
                level="INFO",
                module=self.__class__.__name__,
                message=f"Transaction {transaction_type}: {status.value}",
                extra_data=log_data
            )
        except Exception as e:
            self.logger.error(f"Failed to log transaction: {e}")
            return False

class LiveTransactionHandler(TransactionHandler):
    """
    Production transaction handler.
    Executes real transactions on the blockchain.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.mode = TransactionMode.PRODUCTION
        self._trading_engine = None
    
    async def _get_trading_engine(self):
        """Lazy load trading engine to avoid circular imports."""
        if self._trading_engine is None:
            from app.trading.trading_engine import TradingEngine
            wallet_path = get_config().solana.wallet_path
            self._trading_engine = TradingEngine(wallet_path)
        return self._trading_engine
    
    async def execute_swap(
        self,
        input_token_mint: str,
        output_token_mint: str,
        amount_in_tokens: Optional[float] = None,
        amount_in_usd: Optional[float] = None,
        slippage_bps: Optional[int] = None,
        swap_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute real swap using TradingEngine."""
        try:
            self.logger.info(f"[PRODUCTION] Executing swap: {input_token_mint} -> {output_token_mint}")
            
            trading_engine = await self._get_trading_engine()
            
            # Execute real swap
            async with trading_engine:
                result = await trading_engine.execute_swap(
                    input_token_mint_str=input_token_mint,
                    output_token_mint_str=output_token_mint,
                    amount_in_tokens_float=amount_in_tokens,
                    amount_in_usd=amount_in_usd,
                    slippage_bps=slippage_bps,
                    swap_mode=swap_mode
                )
            
            # Prepare response
            response = {
                'success': result.get('success', False),
                'signature': result.get('signature'),
                'error': result.get('error'),
                'mode': self.mode.value,
                'details': result.get('details', {})
            }
            
            # Log transaction
            status = TransactionStatus.EXECUTED if response['success'] else TransactionStatus.FAILED
            await self.log_transaction(
                'SWAP',
                {
                    'input_token': input_token_mint,
                    'output_token': output_token_mint,
                    'amount_in_tokens': amount_in_tokens,
                    'amount_in_usd': amount_in_usd,
                    'slippage_bps': slippage_bps
                },
                status,
                response['signature']
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"[PRODUCTION] Swap execution failed: {e}")
            
            error_response = {
                'success': False,
                'signature': None,
                'error': str(e),
                'mode': self.mode.value,
                'details': {}
            }
            
            await self.log_transaction(
                'SWAP',
                {'error': str(e)},
                TransactionStatus.FAILED
            )
            
            return error_response
    
    async def check_balance(self, wallet_address: str, token_mint: str) -> Dict[str, Any]:
        """Check real balance using TradingEngine."""
        try:
            trading_engine = await self._get_trading_engine()
            
            async with trading_engine:
                # Implementation would use Solana RPC to get real balance
                # For now, return a placeholder
                balance = await self._get_real_balance(wallet_address, token_mint)
            
            return {
                'success': True,
                'balance': balance,
                'token_mint': token_mint,
                'mode': self.mode.value
            }
            
        except Exception as e:
            self.logger.error(f"[PRODUCTION] Balance check failed: {e}")
            return {
                'success': False,
                'balance': 0.0,
                'token_mint': token_mint,
                'mode': self.mode.value,
                'error': str(e)
            }
    
    async def _get_real_balance(self, wallet_address: str, token_mint: str) -> float:
        """Get real balance from Solana network."""
        # This would implement actual Solana balance checking
        # Placeholder implementation
        return 1000.0
    
    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        """Get real transaction status from blockchain."""
        try:
            trading_engine = await self._get_trading_engine()
            
            async with trading_engine:
                # Check transaction status on blockchain
                status = await self._check_blockchain_status(signature)
            
            return {
                'success': True,
                'status': status,
                'signature': signature,
                'mode': self.mode.value
            }
            
        except Exception as e:
            self.logger.error(f"[PRODUCTION] Status check failed: {e}")
            return {
                'success': False,
                'status': TransactionStatus.FAILED,
                'signature': signature,
                'mode': self.mode.value,
                'error': str(e)
            }
    
    async def _check_blockchain_status(self, signature: str) -> TransactionStatus:
        """Check transaction status on blockchain."""
        # Placeholder - would check actual blockchain
        return TransactionStatus.EXECUTED
    
    def get_mode(self) -> TransactionMode:
        return self.mode

class MockTransactionHandler(TransactionHandler):
    """
    Test transaction handler.
    Simulates transactions without executing real ones.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.mode = TransactionMode.TEST
        self.simulated_balances = {}
        self.simulated_transactions = {}
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock data for simulation."""
        # Mock balances for common tokens
        self.simulated_balances = {
            get_config().solana.usdc_mint_address: 10000.0,  # 10k USDC
            get_config().solana.sol_mint_address: 100.0,     # 100 SOL
        }
        
        # Mock prices for simulation
        self.mock_prices = {
            get_config().solana.sol_mint_address: 100.0,  # $100 per SOL
            get_config().solana.usdc_mint_address: 1.0,   # $1 per USDC
        }
    
    async def execute_swap(
        self,
        input_token_mint: str,
        output_token_mint: str,
        amount_in_tokens: Optional[float] = None,
        amount_in_usd: Optional[float] = None,
        slippage_bps: Optional[int] = None,
        swap_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simulate swap execution."""
        try:
            self.logger.info(f"[TEST] Simulating swap: {input_token_mint} -> {output_token_mint}")
            
            # Generate simulation ID
            simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
            
            # Calculate simulated amounts
            if amount_in_usd and not amount_in_tokens:
                input_price = self.mock_prices.get(input_token_mint, 1.0)
                amount_in_tokens = amount_in_usd / input_price
            
            if amount_in_tokens and not amount_in_usd:
                input_price = self.mock_prices.get(input_token_mint, 1.0)
                amount_in_usd = amount_in_tokens * input_price
            
            # Simulate slippage and fees
            slippage_factor = (slippage_bps or 50) / 10000.0  # Convert bps to decimal
            fee_factor = 0.003  # 0.3% fee
            
            output_price = self.mock_prices.get(output_token_mint, 1.0)
            theoretical_output = amount_in_usd / output_price
            actual_output = theoretical_output * (1 - slippage_factor - fee_factor)
            
            # Check if sufficient balance
            current_balance = self.simulated_balances.get(input_token_mint, 0.0)
            if current_balance < amount_in_tokens:
                return {
                    'success': False,
                    'signature': None,
                    'error': f"Insufficient balance: {current_balance} < {amount_in_tokens}",
                    'mode': self.mode.value,
                    'details': {}
                }
            
            # Update simulated balances
            self.simulated_balances[input_token_mint] -= amount_in_tokens
            self.simulated_balances[output_token_mint] = (
                self.simulated_balances.get(output_token_mint, 0.0) + actual_output
            )
            
            # Store simulation details
            simulation_details = {
                'input_token': input_token_mint,
                'output_token': output_token_mint,
                'amount_in_tokens': amount_in_tokens,
                'amount_out_tokens': actual_output,
                'amount_in_usd': amount_in_usd,
                'slippage_bps': slippage_bps,
                'simulated_fee': amount_in_usd * fee_factor,
                'simulated_slippage': amount_in_usd * slippage_factor,
                'timestamp': time.time()
            }
            
            self.simulated_transactions[simulation_id] = simulation_details
            
            response = {
                'success': True,
                'signature': simulation_id,
                'error': None,
                'mode': self.mode.value,
                'details': {
                    'simulation_id': simulation_id,
                    'amount_out_tokens': actual_output,
                    'simulated': True,
                    **simulation_details
                }
            }
            
            # Log simulation
            await self.log_transaction(
                'SWAP_SIMULATION',
                simulation_details,
                TransactionStatus.SIMULATED,
                simulation_id
            )
            
            self.logger.info(f"[TEST] Swap simulated successfully: {simulation_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"[TEST] Swap simulation failed: {e}")
            
            error_response = {
                'success': False,
                'signature': None,
                'error': str(e),
                'mode': self.mode.value,
                'details': {}
            }
            
            await self.log_transaction(
                'SWAP_SIMULATION',
                {'error': str(e)},
                TransactionStatus.FAILED
            )
            
            return error_response
    
    async def check_balance(self, wallet_address: str, token_mint: str) -> Dict[str, Any]:
        """Return simulated balance."""
        balance = self.simulated_balances.get(token_mint, 0.0)
        
        self.logger.debug(f"[TEST] Balance check for {token_mint}: {balance}")
        
        return {
            'success': True,
            'balance': balance,
            'token_mint': token_mint,
            'mode': self.mode.value,
            'simulated': True
        }
    
    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        """Get simulated transaction status."""
        if signature in self.simulated_transactions:
            return {
                'success': True,
                'status': TransactionStatus.SIMULATED,
                'signature': signature,
                'mode': self.mode.value,
                'details': self.simulated_transactions[signature]
            }
        else:
            return {
                'success': False,
                'status': TransactionStatus.FAILED,
                'signature': signature,
                'mode': self.mode.value,
                'error': 'Simulation not found'
            }
    
    def get_mode(self) -> TransactionMode:
        return self.mode
    
    def reset_simulation(self):
        """Reset simulation state."""
        self._initialize_mock_data()
        self.simulated_transactions.clear()
        self.logger.info("[TEST] Simulation state reset")
    
    def set_mock_balance(self, token_mint: str, balance: float):
        """Set mock balance for testing."""
        self.simulated_balances[token_mint] = balance
        self.logger.info(f"[TEST] Set mock balance for {token_mint}: {balance}")
    
    def set_mock_price(self, token_mint: str, price: float):
        """Set mock price for testing."""
        self.mock_prices[token_mint] = price
        self.logger.info(f"[TEST] Set mock price for {token_mint}: ${price}")

# Factory function
def create_transaction_handler(mode: TransactionMode = None) -> TransactionHandler:
    """
    Factory function to create appropriate transaction handler based on mode.
    
    Args:
        mode: Transaction mode (if None, reads from system configuration)
    
    Returns:
        TransactionHandler instance
    """
    if mode is None:
        # Read from system configuration
        db = EnhancedDatabase()
        system_status = db.get_system_status()
        mode_str = system_status.get('operating_mode', 'test')
        mode = TransactionMode(mode_str)
    
    if mode == TransactionMode.TEST:
        logger.info("Creating MockTransactionHandler for TEST mode")
        return MockTransactionHandler()
    else:
        logger.info("Creating LiveTransactionHandler for PRODUCTION mode")
        return LiveTransactionHandler() 