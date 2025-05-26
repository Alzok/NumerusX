import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from app.trading.trading_engine import TradingEngine
from app.market.market_data import MarketDataProvider # For type hinting and mocking
from app.utils.jupiter_api_client import JupiterApiClient # For type hinting and mocking
from app.utils.exceptions import (
    JupiterAPIError, SolanaTransactionError, TransactionExpiredError,
    TransactionBroadcastError, TransactionConfirmationError, NumerusXBaseError
)
from app.config import Config
from solders.keypair import Keypair # For mocking wallet
from solders.pubkey import Pubkey

# Sample data
INPUT_MINT_SOL = "So11111111111111111111111111111111111111112"
OUTPUT_MINT_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SAMPLE_TX_SIGNATURE = "5Zdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1vSo11111111111111111111111111111111111111112"

class TestTradingEngine(unittest.IsolatedAsyncioTestCase):

    @patch('app.trading.trading_engine.Config')
    @patch('app.trading.trading_engine.JupiterApiClient')
    @patch('app.trading.trading_engine.TradingEngine._initialize_wallet')
    async def asyncSetUp(self, mock_init_wallet, MockJupiterApiClientClass, MockConfigClass):
        # Mock Config
        self.mock_config_instance = MockConfigClass.return_value
        self.mock_config_instance.SOLANA_PRIVATE_KEY_BS58 = "dummy_private_key_bs58"
        self.mock_config_instance.SOLANA_RPC_URL = "dummy_rpc_url"
        self.mock_config_instance.JUPITER_MAX_RETRIES = 3
        self.mock_config_instance.JUPITER_DEFAULT_SLIPPAGE_BPS = 50
        self.mock_config_instance.JUPITER_SWAP_MODE = "ExactIn"
        # Add other necessary config attributes used by TradingEngine or its components if any

        # Mock _initialize_wallet
        self.mock_wallet_keypair = MagicMock(spec=Keypair)
        self.mock_wallet_keypair.pubkey = Pubkey.from_string("11111111111111111111111111111111")
        mock_init_wallet.return_value = self.mock_wallet_keypair

        # Mock JupiterApiClient instance that TradingEngine will create
        self.mock_jup_api_client_instance = AsyncMock(spec=JupiterApiClient)
        MockJupiterApiClientClass.return_value = self.mock_jup_api_client_instance

        # Instantiate TradingEngine
        # It will use the mocked Config, _initialize_wallet, and create a mocked JupiterApiClient
        self.trading_engine = TradingEngine(wallet_path="dummy/path/to/wallet.json")

        # Assert JupiterApiClient was instantiated correctly by TradingEngine
        MockJupiterApiClientClass.assert_called_once_with(
            private_key_bs58=self.mock_config_instance.SOLANA_PRIVATE_KEY_BS58,
            rpc_url=self.mock_config_instance.SOLANA_RPC_URL,
            config=self.mock_config_instance
        )
        self.assertIs(self.trading_engine.jupiter_client, self.mock_jup_api_client_instance)

        # Mock MarketDataProvider instance and assign it
        self.mock_market_data_provider = AsyncMock(spec=MarketDataProvider)
        # We need to mock its __aenter__ and __aexit__ if used by TradingEngine explicitly
        # For execute_swap, it seems to use it directly if available.
        # TradingEngine.__aenter__ handles MDP lifecycle, but for unit testing execute_swap,
        # we can directly assign a mock MDP.
        self.trading_engine.market_data_provider = self.mock_market_data_provider
        # Ensure it has an async context manager if needed by TradingEngine internals, not strictly for these tests yet.
        # await self.mock_market_data_provider.__aenter__() 

    async def asyncTearDown(self):
        # If MarketDataProvider needs __aexit__ called by TradingEngine's __aexit__.
        # For these tests, we are not testing the full lifecycle via TradingEngine.__aexit__ typically.
        # If self.trading_engine.market_data_provider was set and has __aexit__:
        # await self.trading_engine.market_data_provider.__aexit__(None, None, None)
        pass

    async def test_execute_swap_success_with_tokens(self):
        input_mint = INPUT_MINT_SOL
        output_mint = OUTPUT_MINT_USDC
        amount_tokens = 1.0
        slippage = 100

        # 1. MarketDataProvider.get_jupiter_swap_quote response
        mock_quote_response_data = {"quote_key": "quote_value", "inAmountLamports": 10**9} # Raw quote from Jupiter SDK
        self.mock_market_data_provider.get_jupiter_swap_quote.return_value = {
            'success': True, 'data': mock_quote_response_data, 'error': None
        }

        # 2. JupiterApiClient.get_swap_transaction_data response
        mock_swap_tx_data = {
            "serialized_transaction_b64": "dummy_tx_b64",
            "last_valid_block_height": 12345
        }
        self.mock_jup_api_client_instance.get_swap_transaction_data.return_value = mock_swap_tx_data

        # 3. JupiterApiClient.sign_and_send_transaction response
        self.mock_jup_api_client_instance.sign_and_send_transaction.return_value = SAMPLE_TX_SIGNATURE

        result = await self.trading_engine.execute_swap(
            input_token_mint=input_mint,
            output_token_mint=output_mint,
            amount_in_tokens_float=amount_tokens,
            slippage_bps=slippage
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['signature'], SAMPLE_TX_SIGNATURE)
        self.assertIsNone(result['error'])

        self.mock_market_data_provider.get_jupiter_swap_quote.assert_awaited_once_with(
            input_mint_str=input_mint,
            output_mint_str=output_mint,
            amount_in_tokens=amount_tokens,
            slippage_bps=slippage
        )
        self.mock_jup_api_client_instance.get_swap_transaction_data.assert_awaited_once_with(quote_response=mock_quote_response_data)
        self.mock_jup_api_client_instance.sign_and_send_transaction.assert_awaited_once_with(
            serialized_transaction_b64=mock_swap_tx_data["serialized_transaction_b64"],
            last_valid_block_height=mock_swap_tx_data["last_valid_block_height"]
        )

    async def test_execute_swap_success_with_usd(self):
        input_mint = INPUT_MINT_SOL
        output_mint = OUTPUT_MINT_USDC
        amount_usd = 100.0
        token_price = 100.0 # 1 SOL = 100 USD
        expected_amount_tokens = 1.0 # 100 USD / 100 USD/SOL = 1 SOL
        slippage = 50

        # Mock MarketDataProvider.get_token_price
        self.mock_market_data_provider.get_token_price.return_value = {
            'success': True, 'data': {'price': token_price, 'symbol': 'SOL'}
        }
        # Mock subsequent calls as in test_execute_swap_success_with_tokens
        mock_quote_response_data = {"quote_key": "quote_value"}
        self.mock_market_data_provider.get_jupiter_swap_quote.return_value = {
            'success': True, 'data': mock_quote_response_data
        }
        mock_swap_tx_data = {"serialized_transaction_b64": "dummy_tx_b64", "last_valid_block_height": 12345}
        self.mock_jup_api_client_instance.get_swap_transaction_data.return_value = mock_swap_tx_data
        self.mock_jup_api_client_instance.sign_and_send_transaction.return_value = SAMPLE_TX_SIGNATURE

        result = await self.trading_engine.execute_swap(
            input_token_mint=input_mint,
            output_token_mint=output_mint,
            amount_in_usd=amount_usd,
            slippage_bps=slippage
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['signature'], SAMPLE_TX_SIGNATURE)
        self.mock_market_data_provider.get_token_price.assert_awaited_once_with(input_mint, "USD")
        self.mock_market_data_provider.get_jupiter_swap_quote.assert_awaited_once_with(
            input_mint_str=input_mint,
            output_mint_str=output_mint,
            amount_in_tokens=expected_amount_tokens, # Check if amount_in_tokens is correctly calculated
            slippage_bps=slippage
        )

    async def test_execute_swap_failure_get_token_price_fails(self):
        self.mock_market_data_provider.get_token_price.return_value = {
            'success': False, 'error': 'Failed to get price'
        }
        result = await self.trading_engine.execute_swap(
            input_token_mint=INPUT_MINT_SOL,
            output_token_mint=OUTPUT_MINT_USDC,
            amount_in_usd=100.0
        )
        self.assertFalse(result['success'])
        self.assertIn("Failed to get price for amount conversion", result['error'])
        self.mock_market_data_provider.get_jupiter_swap_quote.assert_not_awaited()

    async def test_execute_swap_failure_get_jupiter_quote_fails(self):
        self.mock_market_data_provider.get_jupiter_swap_quote.return_value = {
            'success': False, 'error': 'Failed to get quote'
        }
        result = await self.trading_engine.execute_swap(
            input_token_mint=INPUT_MINT_SOL,
            output_token_mint=OUTPUT_MINT_USDC,
            amount_in_tokens_float=1.0
        )
        self.assertFalse(result['success'])
        self.assertIn("Failed to get quote", result['error'])
        self.mock_jup_api_client_instance.get_swap_transaction_data.assert_not_awaited()

    async def test_execute_swap_failure_get_swap_tx_data_raises_jupiter_api_error(self):
        self.mock_market_data_provider.get_jupiter_swap_quote.return_value = {
            'success': True, 'data': {"quote_key": "value"}
        }
        error_msg = "Jupiter tx data error"
        self.mock_jup_api_client_instance.get_swap_transaction_data.side_effect = JupiterAPIError(error_msg)
        
        result = await self.trading_engine.execute_swap(
            input_token_mint=INPUT_MINT_SOL,
            output_token_mint=OUTPUT_MINT_USDC,
            amount_in_tokens_float=1.0
        )
        self.assertFalse(result['success'])
        self.assertIn(error_msg, result['error'])
        self.assertTrue(isinstance(result['details'], JupiterAPIError))
        self.mock_jup_api_client_instance.sign_and_send_transaction.assert_not_awaited()

    async def test_execute_swap_failure_sign_send_raises_solana_tx_error(self):
        self.mock_market_data_provider.get_jupiter_swap_quote.return_value = {
            'success': True, 'data': {"quote_key": "value"}
        }
        self.mock_jup_api_client_instance.get_swap_transaction_data.return_value = {
            "serialized_transaction_b64": "dummy_tx_b64", "last_valid_block_height": 123
        }
        error_msg = "Broadcast failed"
        # Using TransactionBroadcastError as an example sub-type of SolanaTransactionError
        self.mock_jup_api_client_instance.sign_and_send_transaction.side_effect = TransactionBroadcastError(error_msg, signature="test_sig")

        result = await self.trading_engine.execute_swap(
            input_token_mint=INPUT_MINT_SOL,
            output_token_mint=OUTPUT_MINT_USDC,
            amount_in_tokens_float=1.0
        )
        self.assertFalse(result['success'])
        self.assertIn(error_msg, result['error'])
        self.assertTrue(isinstance(result['details'], TransactionBroadcastError))

    async def test_execute_swap_retry_on_transaction_expired_then_success(self):
        # _execute_swap_attempt is retried on TransactionExpiredError
        # We need to mock what _execute_swap_attempt calls: MDP.get_jupiter_swap_quote or JupClient methods
        # Let's make sign_and_send_transaction cause the retry

        self.mock_market_data_provider.get_jupiter_swap_quote.return_value = {
            'success': True, 'data': {"quote_key": "value"}
        }
        self.mock_jup_api_client_instance.get_swap_transaction_data.return_value = {
            "serialized_transaction_b64": "dummy_tx_b64", "last_valid_block_height": 123
        }
        
        expired_error = TransactionExpiredError("Expired!", signature="exp_sig")
        self.mock_jup_api_client_instance.sign_and_send_transaction.side_effect = [
            expired_error, # First call fails
            expired_error, # Second call fails
            SAMPLE_TX_SIGNATURE # Third call succeeds
        ]
        
        # Ensure JUPITER_MAX_RETRIES is at least 3 in config mock for this test
        self.mock_config_instance.JUPITER_MAX_RETRIES = 3
        # Re-initialize trading engine with this specific config for retry if needed, or ensure setUp uses it.
        # The setUp already applies the mocked config to the TradingEngine instance.

        result = await self.trading_engine.execute_swap(
            input_token_mint=INPUT_MINT_SOL,
            output_token_mint=OUTPUT_MINT_USDC,
            amount_in_tokens_float=1.0
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['signature'], SAMPLE_TX_SIGNATURE)
        self.assertEqual(self.mock_jup_api_client_instance.sign_and_send_transaction.call_count, 3)

    async def test_execute_swap_retry_on_transaction_expired_exhausted(self):
        self.mock_market_data_provider.get_jupiter_swap_quote.return_value = {
            'success': True, 'data': {"quote_key": "value"}
        }
        self.mock_jup_api_client_instance.get_swap_transaction_data.return_value = {
            "serialized_transaction_b64": "dummy_tx_b64", "last_valid_block_height": 123
        }
        
        expired_error = TransactionExpiredError("Expired always!", signature="exp_sig_always")
        # Make it fail more times than max_retries (e.g., JUPITER_MAX_RETRIES = 2 for this test)
        self.mock_config_instance.JUPITER_MAX_RETRIES = 2
        self.mock_jup_api_client_instance.sign_and_send_transaction.side_effect = [
            expired_error, expired_error, expired_error # Fails 3 times
        ]

        result = await self.trading_engine.execute_swap(
            input_token_mint=INPUT_MINT_SOL,
            output_token_mint=OUTPUT_MINT_USDC,
            amount_in_tokens_float=1.0
        )

        self.assertFalse(result['success'])
        self.assertIn("Expired always!", result['error'])
        self.assertTrue(isinstance(result['details'], TransactionExpiredError))
        # It should be called JUPITER_MAX_RETRIES times (which is 2 for _execute_swap_attempt)
        # plus one initial attempt. The @retry decorator handles this.
        # The stop_after_attempt(N) means N total attempts. So if N=2, it tries once, then retries once.
        # If JUPITER_MAX_RETRIES is the value for stop_after_attempt, then call_count will be JUPITER_MAX_RETRIES.
        self.assertEqual(self.mock_jup_api_client_instance.sign_and_send_transaction.call_count, self.mock_config_instance.JUPITER_MAX_RETRIES)

if __name__ == '__main__':
    unittest.main() 