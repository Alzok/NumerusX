import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pytest # Using pytest for async/await tests and fixtures if needed
import base64 # For send_transaction tests

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction # For send_transaction tests
from solders.message import Message # For send_transaction tests
from solders.signature import Signature # For mocking send_transaction return
from solana.rpc.types import TxOpts # For send_transaction tests
from solana.rpc.commitment import Confirmed, Finalized # For send_transaction tests
from solana.rpc.core import RPCException # For mocking Solana RPC errors
from jupiter_python_sdk.jupiter import Jupiter # For type hinting if needed
from jupiter_python_sdk.models import QuoteResponse, SwapResponse, TxResponse # For mocking returns
from jupiter_python_sdk.exceptions import JupiterPythonSdkError, TransactionExpiredBlockheightExceededError # Import base SDK error for mocking

from app.config import Config
from app.utils.jupiter_api_client import JupiterApiClient
from app.utils.exceptions import (
    JupiterAPIError, SolanaTransactionError, TransactionExpiredError,
    TransactionBroadcastError, TransactionConfirmationError, TransactionSimulationError
)

# Sample data for mocking
SAMPLE_WALLET_BS58 = "588FU4PktJWfGfytLko9XkBabYvuSn5ZrefxM2D2G8wP"
SAMPLE_RPC_URL = "https://api.mainnet-beta.solana.com"

# Using a more complete QuoteResponse for testing
SAMPLE_QUOTE_RESPONSE_DICT = {
    "inputMint": "So11111111111111111111111111111111111111112",
    "inAmount": "100000000",
    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "outAmount": "6410300",
    "routePlan": [
        {
            "swapInfo": {
                "ammKey": "someAmmKey",
                "label": "Saber",
                "inputMint": "So11111111111111111111111111111111111111112",
                "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "inAmount": "100000000",
                "outAmount": "6410300",
                "feeAmount": "5000",
                "feeMint": "So11111111111111111111111111111111111111112"
            },
            "percent": 100
        }
    ],
    "slippageBps": 50,
    "otherAmountThreshold": "6378248", # Example
    "swapMode": "ExactIn",
    "priceImpactPct": "0.00123", # Example
    "contextSlot": 123456789,
    "timeTaken": 0.123,
    # platformFee can be None or a dict
    "platformFee": {"amount": "10000", "feeMint": "So11111111111111111111111111111111111111112"} 
}
SAMPLE_QUOTE_RESPONSE = QuoteResponse.from_dict(SAMPLE_QUOTE_RESPONSE_DICT)

# Based on JupiterApiClient's expected return for get_swap_transaction_data
SAMPLE_SWAP_TX_DATA_RETURN_DICT = {
    "serialized_transaction_b64": "AgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACDAQEAAgAGDBImS+JEXHTg5nxXDRW2u4z5A6tESNHx2P72zHzN3xZBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAgABDAoDAgADAgEAAgABBwEAAgABAQEECAEAAQEDAQYHAQACAQEBAAAAAAADAQIAAQECBAgBAAEBAwECBwEAAgECAQAAAAAAAwECAAEBBQgBAAICAgQECAEAAgECBwEAAgECAAAAAAADBQIAAQEECAEAAQEKAwIAAQEBBwEAAgECBAgBAAICAgABAQIAAQEECAEAAgIKAwIAAQMHAQABAgQIATECBAQEAQECBAgBAAEBCgME",
    "last_valid_block_height": 123456800 
}
# This TxResponse is what the SDK's get_swap_transaction method might return
SAMPLE_SDK_TX_RESPONSE = TxResponse(
    # Populate with fields that TxResponse expects, matching what client uses
    # The client extracts compute_unit_price_micro_lamports, prioritize_fee, swap_instructions, address_lookup_table_addresses
    # last_valid_block_height, blockhash, and serialized_transaction. 
    # The most important for the client's get_swap_transaction_data are serialized_transaction and last_valid_block_height.
    tx_id="dummy_tx_id", # Not directly used by client's method but part of TxResponse
    compute_unit_price_micro_lamports=10000,
    prioritize_fee="Medium",
    swap_instructions=["instr1", "instr2"], # Placeholder
    address_lookup_table_addresses=["addr1", "addr2"], # Placeholder
    last_valid_block_height=SAMPLE_SWAP_TX_DATA_RETURN_DICT["last_valid_block_height"],
    blockhash="dummy_blockhash",
    serialized_transaction=SAMPLE_SWAP_TX_DATA_RETURN_DICT["serialized_transaction_b64"],
    open_orders_instructions=[] # Add if TxResponse requires it
)
SAMPLE_TX_SIGNATURE_STR = "5Zdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1vSo11111111111111111111111111111111111111112"

# Use IsolatedAsyncioTestCase for async test methods
class TestJupiterApiClient(unittest.IsolatedAsyncioTestCase): 

    def setUp(self):
        self.config = Config()
        self.config.SOLANA_PRIVATE_KEY_BS58 = SAMPLE_WALLET_BS58
        self.config.SOLANA_RPC_URL = SAMPLE_RPC_URL
        self.config.JUPITER_API_KEY = "test_api_key"
        self.config.JUPITER_DEFAULT_SLIPPAGE_BPS = 50
        self.config.JUPITER_MAX_RETRIES = 3 # For retry test
        self.config.JUPITER_WRAP_AND_UNWRAP_SOL = True # Example config value
        self.config.JUPITER_USE_SHARED_ACCOUNTS = True # Example config value
        self.config.TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS = 30 # For testing confirm timeout

    # Patch the client and SDK for each test method that needs them
    async def asyncSetUp(self):
        # This method will be called before each async test
        self.mock_keypair_patch = patch('app.utils.jupiter_api_client.Keypair')
        self.mock_jupiter_sdk_patch = patch('app.utils.jupiter_api_client.Jupiter')
        self.mock_async_client_patch = patch('app.utils.jupiter_api_client.AsyncClient')
        self.mock_versioned_tx_patch = patch('app.utils.jupiter_api_client.VersionedTransaction')

        self.MockKeypair = self.mock_keypair_patch.start()
        self.MockJupiterSDK = self.mock_jupiter_sdk_patch.start()
        self.MockAsyncClient = self.mock_async_client_patch.start()
        self.MockVersionedTransaction = self.mock_versioned_tx_patch.start()

        self.mock_keypair_instance = MagicMock(spec=Keypair)
        self.mock_keypair_instance.pubkey = Pubkey.from_string("11111111111111111111111111111111")
        self.mock_keypair_instance.sign_message = MagicMock(return_value=b"signed_message_bytes") # Mock sign_message
        self.MockKeypair.from_base58_string.return_value = self.mock_keypair_instance
        
        self.mock_async_client_instance = MagicMock(spec=AsyncClient)
        self.mock_async_client_instance.send_transaction = AsyncMock() # Mock async method
        self.mock_async_client_instance.confirm_transaction = AsyncMock() # Mock async method
        self.MockAsyncClient.return_value = self.mock_async_client_instance
        
        self.mock_jupiter_sdk_instance = MagicMock(spec=Jupiter)
        self.mock_jupiter_sdk_instance.get_quote = AsyncMock() # Mock async method
        self.mock_jupiter_sdk_instance.get_swap_transaction = AsyncMock() # Mocked for get_swap_transaction_data
        self.mock_jupiter_sdk_instance.sign_and_execute = AsyncMock() # If used by sign_and_send_transaction
        self.mock_jupiter_sdk_instance.get_latest_blockhash = AsyncMock(return_value="dummy_blockhash_from_sdk_via_async_client")

        self.MockJupiterSDK.return_value = self.mock_jupiter_sdk_instance

        # Mock for VersionedTransaction.from_bytes and .populate
        self.mock_v_tx_instance = MagicMock(spec=VersionedTransaction)
        self.mock_v_tx_instance.message = MagicMock(spec=Message)
        self.mock_v_tx_instance.message.payer = self.mock_keypair_instance.pubkey # Ensure payer matches
        self.mock_v_tx_instance.message_data.return_value = b"message_data_to_sign"
        self.MockVersionedTransaction.from_bytes.return_value = self.mock_v_tx_instance
        self.MockVersionedTransaction.populate.return_value = self.mock_v_tx_instance # Populate returns the signed tx

        self.client = JupiterApiClient(
            private_key_bs58=self.config.SOLANA_PRIVATE_KEY_BS58,
            rpc_url=self.config.SOLANA_RPC_URL,
            config=self.config
        )

    async def asyncTearDown(self):
        self.mock_keypair_patch.stop()
        self.mock_jupiter_sdk_patch.stop()
        self.mock_async_client_patch.stop()
        self.mock_versioned_tx_patch.stop()

    # Separate test for non-async __init__ still using unittest.TestCase structure
    # These init tests do not need asyncSetUp/asyncTearDown, so they can be in a standard TestCase or here
    # For simplicity, keeping them here but they won't use asyncSetUp.
    @patch('app.utils.jupiter_api_client.AsyncClient')
    @patch('app.utils.jupiter_api_client.Jupiter')
    @patch('app.utils.jupiter_api_client.Keypair')
    def test_init_success_with_private_key_and_rpc(self, MockKeypair, MockJupiterSDK, MockAsyncClient):
        # This test is synchronous and won't use asyncSetUp mocks.
        # It re-mocks locally.
        mock_keypair_instance = Keypair() 
        MockKeypair.from_base58_string.return_value = mock_keypair_instance
        mock_async_client_instance = MockAsyncClient.return_value
        mock_jupiter_sdk_instance = MockJupiterSDK.return_value

        client = JupiterApiClient(
            private_key_bs58=self.config.SOLANA_PRIVATE_KEY_BS58,
            rpc_url=self.config.SOLANA_RPC_URL,
            config=self.config
        )
        MockKeypair.from_base58_string.assert_called_once_with(self.config.SOLANA_PRIVATE_KEY_BS58)
        MockAsyncClient.assert_called_once_with(self.config.SOLANA_RPC_URL)
        expected_base_url = f"https://{self.config.JUPITER_PRO_API_HOSTNAME}"
        MockJupiterSDK.assert_called_once_with(
            async_client=mock_async_client_instance,
            keypair=mock_keypair_instance,
            base_url=expected_base_url,
            api_key=self.config.JUPITER_API_KEY
        )

    @patch('app.utils.jupiter_api_client.AsyncClient')
    @patch('app.utils.jupiter_api_client.Jupiter')
    @patch('app.utils.jupiter_api_client.Keypair')
    def test_init_success_no_api_key(self, MockKeypair, MockJupiterSDK, MockAsyncClient):
        self.config.JUPITER_API_KEY = None
        mock_keypair_instance = Keypair()
        MockKeypair.from_base58_string.return_value = mock_keypair_instance
        mock_async_client_instance = MockAsyncClient.return_value
        mock_jupiter_sdk_instance = MockJupiterSDK.return_value

        client = JupiterApiClient(
            private_key_bs58=self.config.SOLANA_PRIVATE_KEY_BS58,
            rpc_url=self.config.SOLANA_RPC_URL,
            config=self.config
        )
        expected_base_url = f"https://{self.config.JUPITER_LITE_API_HOSTNAME}"
        MockJupiterSDK.assert_called_once_with(
            async_client=mock_async_client_instance,
            keypair=mock_keypair_instance,
            base_url=expected_base_url,
            api_key=None
        )

    def test_init_missing_private_key(self):
        with self.assertRaisesRegex(ValueError, "private_key_bs58 must be provided"): 
            JupiterApiClient(private_key_bs58=None, rpc_url=self.config.SOLANA_RPC_URL, config=self.config)

    def test_init_missing_rpc_url(self):
        with self.assertRaisesRegex(ValueError, "rpc_url must be provided"): 
            JupiterApiClient(private_key_bs58=self.config.SOLANA_PRIVATE_KEY_BS58, rpc_url=None, config=self.config)

    async def test_get_quote_success(self):
        self.mock_jupiter_sdk_instance.get_quote.return_value = SAMPLE_QUOTE_RESPONSE

        quote_params = {
            "input_mint_str": "So11111111111111111111111111111111111111112",
            "output_mint_str": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "amount_lamports": 100000000,
            "slippage_bps": 50,
            "swap_mode": "ExactIn"
        }
        result = await self.client.get_quote(**quote_params)

        self.assertEqual(result, SAMPLE_QUOTE_RESPONSE)
        self.mock_jupiter_sdk_instance.get_quote.assert_awaited_once_with(
            input_mint=Pubkey.from_string(quote_params["input_mint_str"]),
            output_mint=Pubkey.from_string(quote_params["output_mint_str"]),
            amount=quote_params["amount_lamports"],
            slippage_bps=quote_params["slippage_bps"],
            swap_mode=quote_params["swap_mode"],
            only_direct_routes = self.config.JUPITER_ONLY_DIRECT_ROUTES,
            # Ensure other default params from config are passed if client applies them here
            # Example: platform_fee_bps=self.config.JUPITER_PLATFORM_FEE_BPS (if client adds it)
        )

    async def test_get_quote_sdk_error(self):
        sdk_error_message = "SDK quote failed"
        self.mock_jupiter_sdk_instance.get_quote.side_effect = JupiterPythonSdkError(sdk_error_message)

        quote_params = {
            "input_mint_str": "So11111111111111111111111111111111111111112",
            "output_mint_str": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "amount_lamports": 100000000
        }
        with self.assertRaises(JupiterAPIError) as context:
            await self.client.get_quote(**quote_params)
        
        self.assertIn(sdk_error_message, str(context.exception))
        self.assertIsInstance(context.exception.original_exception, JupiterPythonSdkError)

    async def test_get_quote_with_retry_on_sdk_error(self):
        # Simulate an SDK error that should trigger a retry (e.g., a generic JupiterPythonSdkError for non-TransactionExpired)
        # The tenacity retry in _call_sdk_method is for JupiterPythonSdkError generally.
        sdk_temp_error = JupiterPythonSdkError("Temporary SDK issue")
        self.mock_jupiter_sdk_instance.get_quote.side_effect = [
            sdk_temp_error, 
            sdk_temp_error, 
            SAMPLE_QUOTE_RESPONSE
        ]

        quote_params = {
            "input_mint_str": "So11111111111111111111111111111111111111112",
            "output_mint_str": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "amount_lamports": 100000000
        }
        
        # Override JUPITER_MAX_RETRIES for this specific test if client uses it directly in tenacity config
        # If _call_sdk_method uses a hardcoded retry count or config.JUPITER_MAX_RETRIES directly, that will be used.
        # For this test, assume JUPITER_MAX_RETRIES=3 set in setUp is effective.

        result = await self.client.get_quote(**quote_params)
        self.assertEqual(result, SAMPLE_QUOTE_RESPONSE)
        self.assertEqual(self.mock_jupiter_sdk_instance.get_quote.await_count, 3)

    async def test_get_swap_transaction_data_success(self):
        self.mock_jupiter_sdk_instance.get_swap_transaction.return_value = SAMPLE_SDK_TX_RESPONSE
        
        result = await self.client.get_swap_transaction_data(quote_response=SAMPLE_QUOTE_RESPONSE)

        self.assertEqual(result, SAMPLE_SWAP_TX_DATA_RETURN_DICT)
        self.mock_jupiter_sdk_instance.get_swap_transaction.assert_awaited_once_with(
            quote_response=SAMPLE_QUOTE_RESPONSE,
            user_public_key=self.mock_keypair_instance.pubkey,
            wrap_and_unwrap_sol=self.config.JUPITER_WRAP_AND_UNWRAP_SOL,
            use_shared_accounts=self.config.JUPITER_USE_SHARED_ACCOUNTS,
            # fee_account = Optional[Pubkey]
            # compute_unit_price_micro_lamports = Optional[int]
            # prioritize_fee = Optional[str]
            # as_legacy_transaction = Optional[bool]
        )

    async def test_get_swap_transaction_data_sdk_error(self):
        sdk_error_message = "SDK swap transaction failed"
        self.mock_jupiter_sdk_instance.get_swap_transaction.side_effect = JupiterPythonSdkError(sdk_error_message)

        with self.assertRaises(JupiterAPIError) as context:
            await self.client.get_swap_transaction_data(quote_response=SAMPLE_QUOTE_RESPONSE)
        
        self.assertIn(sdk_error_message, str(context.exception))
        self.assertIsInstance(context.exception.original_exception, JupiterPythonSdkError)

    async def test_get_swap_transaction_data_with_retry_on_sdk_error(self):
        sdk_temp_error = JupiterPythonSdkError("Temporary SDK issue for swap_tx")
        self.mock_jupiter_sdk_instance.get_swap_transaction.side_effect = [
            sdk_temp_error,
            sdk_temp_error,
            SAMPLE_SDK_TX_RESPONSE
        ]
        
        result = await self.client.get_swap_transaction_data(quote_response=SAMPLE_QUOTE_RESPONSE)
        self.assertEqual(result, SAMPLE_SWAP_TX_DATA_RETURN_DICT)
        self.assertEqual(self.mock_jupiter_sdk_instance.get_swap_transaction.await_count, 3)

    async def test_sign_and_send_transaction_success(self):
        # Mock send_transaction to return a mock response containing the signature
        mock_send_tx_response = MagicMock()
        mock_send_tx_response.value = Signature.from_string(SAMPLE_TX_SIGNATURE_STR)
        self.mock_async_client_instance.send_transaction.return_value = mock_send_tx_response
        
        # Mock confirm_transaction to simulate successful confirmation
        # The actual response structure for confirm_transaction is a list of statuses or None
        mock_confirm_response = MagicMock()
        mock_confirm_status = MagicMock()
        mock_confirm_status.confirmation_status = Confirmed # or Finalized
        mock_confirm_status.err = None
        mock_confirm_response.value = [mock_confirm_status] # List with one status
        self.mock_async_client_instance.confirm_transaction.return_value = mock_confirm_response

        serialized_tx = SAMPLE_SWAP_TX_DATA_RETURN_DICT["serialized_transaction_b64"]
        lvbh = SAMPLE_SWAP_TX_DATA_RETURN_DICT["last_valid_block_height"]

        result_signature = await self.client.sign_and_send_transaction(serialized_tx, lvbh)

        self.assertEqual(result_signature, SAMPLE_TX_SIGNATURE_STR)
        self.MockVersionedTransaction.from_bytes.assert_called_once_with(base64.b64decode(serialized_tx))
        self.mock_keypair_instance.sign_message.assert_called_once_with(self.mock_v_tx_instance.message_data())
        self.MockVersionedTransaction.populate.assert_called_once_with(self.mock_v_tx_instance.message, [b"signed_message_bytes"])
        self.mock_async_client_instance.send_transaction.assert_awaited_once_with(
            self.mock_v_tx_instance, 
            opts=TxOpts(skip_preflight=True, last_valid_block_height=lvbh, preflight_commitment=Confirmed)
        )
        self.mock_async_client_instance.confirm_transaction.assert_awaited()

    async def test_sign_and_send_transaction_expired_sdk_error_on_send(self):
        # Simulate TransactionExpiredBlockheightExceededError from SDK's send_transaction (hypothetical)
        # More realistically, this error comes from Solana client during send or confirm if LVBH is passed
        self.mock_async_client_instance.send_transaction.side_effect = TransactionExpiredBlockheightExceededError("Blockheight exceeded during send")
        
        serialized_tx = SAMPLE_SWAP_TX_DATA_RETURN_DICT["serialized_transaction_b64"]
        lvbh = SAMPLE_SWAP_TX_DATA_RETURN_DICT["last_valid_block_height"]

        with self.assertRaises(TransactionExpiredError) as context:
            await self.client.sign_and_send_transaction(serialized_tx, lvbh)
        self.assertIn("Blockheight exceeded during send", str(context.exception.original_exception))

    async def test_sign_and_send_transaction_expired_during_confirm(self):
        # Mock send_transaction to succeed
        mock_send_tx_response = MagicMock()
        mock_send_tx_response.value = Signature.from_string(SAMPLE_TX_SIGNATURE_STR)
        self.mock_async_client_instance.send_transaction.return_value = mock_send_tx_response

        # Mock confirm_transaction to raise an error that implies expiration, like a timeout or specific RPC error
        # For simplicity, we'll have it raise TransactionExpiredBlockheightExceededError directly as if SDK handled it
        # Or, more accurately, mock get_signature_statuses to show it's not confirmed and LVBH is passed.
        # The client code has a direct check for LVBH if confirm_transaction takes too long.
        # Let's simulate timeout by confirm_transaction taking too long (via multiple None returns)
        confirm_timeout_val = self.config.TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS
        num_polls = (confirm_timeout_val // 1) + 2 # Ensure it times out based on 1s poll interval in client
        self.mock_async_client_instance.confirm_transaction.side_effect = [MagicMock(value=[None])] * num_polls
        
        serialized_tx = SAMPLE_SWAP_TX_DATA_RETURN_DICT["serialized_transaction_b64"]
        lvbh = SAMPLE_SWAP_TX_DATA_RETURN_DICT["last_valid_block_height"]

        with self.assertRaises(TransactionConfirmationError) as context: # Should be ConfirmationError due to timeout
            await self.client.sign_and_send_transaction(serialized_tx, lvbh)
        self.assertIn("timed out", str(context.exception).lower())

    async def test_sign_and_send_transaction_rpc_error_on_send(self):
        rpc_error = RPCException("Failed to send transaction")
        self.mock_async_client_instance.send_transaction.side_effect = rpc_error
        serialized_tx = SAMPLE_SWAP_TX_DATA_RETURN_DICT["serialized_transaction_b64"]
        lvbh = SAMPLE_SWAP_TX_DATA_RETURN_DICT["last_valid_block_height"]

        with self.assertRaises(TransactionBroadcastError) as context:
            await self.client.sign_and_send_transaction(serialized_tx, lvbh)
        self.assertIs(context.exception.original_exception, rpc_error)

    async def test_sign_and_send_transaction_rpc_error_on_confirm(self):
        mock_send_tx_response = MagicMock()
        mock_send_tx_response.value = Signature.from_string(SAMPLE_TX_SIGNATURE_STR)
        self.mock_async_client_instance.send_transaction.return_value = mock_send_tx_response

        rpc_error = RPCException("Failed to confirm transaction")
        # Simulate error after a few null polls to ensure polling loop is entered
        confirm_responses = [MagicMock(value=[None]), MagicMock(value=[None]), rpc_error]
        self.mock_async_client_instance.confirm_transaction.side_effect = confirm_responses

        serialized_tx = SAMPLE_SWAP_TX_DATA_RETURN_DICT["serialized_transaction_b64"]
        lvbh = SAMPLE_SWAP_TX_DATA_RETURN_DICT["last_valid_block_height"]

        with self.assertRaises(TransactionConfirmationError) as context:
            await self.client.sign_and_send_transaction(serialized_tx, lvbh)
        self.assertIs(context.exception.original_exception, rpc_error)

    async def test_sign_and_send_transaction_invalid_base64(self):
        serialized_tx = "This is not valid base64"
        lvbh = SAMPLE_SWAP_TX_DATA_RETURN_DICT["last_valid_block_height"]
        with self.assertRaises(ValueError) as context: # Base64 errors raise ValueError or binascii.Error
            await self.client.sign_and_send_transaction(serialized_tx, lvbh)
        self.assertIn("Invalid base64", str(context.exception))
    
    async def test_close_async_client(self):
        await self.client.close_async_client()
        self.mock_async_client_instance.close.assert_awaited_once()

    async def test_close_dca_order_success(self):
        dca_order_id = "DCAOrderPublicKey11111111111111111111111"
        mock_sdk_response = {"status": "closed", "dca_order_id": dca_order_id}
        self.mock_jupiter_sdk_instance.dca_close.return_value = mock_sdk_response

        result = await self.client.close_dca_order(dca_order_id_str=dca_order_id)

        self.assertEqual(result, mock_sdk_response)
        self.mock_jupiter_sdk_instance.dca_close.assert_awaited_once_with(
            dca_order_id=Pubkey.from_string(dca_order_id)
        )

    async def test_close_dca_order_sdk_error(self):
        dca_order_id = "DCAOrderPublicKey11111111111111111111111"
        sdk_error_message = "SDK close DCA order failed"
        self.mock_jupiter_sdk_instance.dca_close.side_effect = JupiterPythonSdkError(sdk_error_message)

        with self.assertRaises(JupiterAPIError) as context:
            await self.client.close_dca_order(dca_order_id_str=dca_order_id)
        
        self.assertIn(sdk_error_message, str(context.exception))
        self.assertIsInstance(context.exception.original_exception, JupiterPythonSdkError)

# To run these tests (if you save this as test_jupiter_api_client.py in a tests/ directory):
# Ensure pytest and pytest-asyncio are installed: pip install pytest pytest-asyncio
# Then run from the root of your project: pytest

if __name__ == '__main__':
    unittest.main() 