import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import json

from app.market.market_data import MarketDataProvider
from app.utils.jupiter_api_client import JupiterApiClient # For type hinting
from app.utils.exceptions import JupiterAPIError, DexScreenerAPIError, NumerusXBaseError
from app.config import get_config # For potential config mocking or access

# Sample mint addresses
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

class TestMarketDataProvider(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.config = Config() # Use default config for now
        
        # Patch JupiterApiClient instantiation within MarketDataProvider
        self.mock_jup_client_patcher = patch('app.market.market_data.JupiterApiClient')
        self.MockJupiterApiClientClass = self.mock_jup_client_patcher.start()
        
        self.mock_jupiter_client_instance = AsyncMock(spec=JupiterApiClient)
        self.MockJupiterApiClientClass.return_value = self.mock_jupiter_client_instance

        # Patch aiohttp.ClientSession for DexScreener calls
        self.mock_aiohttp_session_patcher = patch('aiohttp.ClientSession')
        self.MockAiohttpSessionClass = self.mock_aiohttp_session_patcher.start()
        self.mock_aiohttp_session_instance = AsyncMock()
        # Mock common session methods like get, post, etc.
        self.mock_response = AsyncMock()
        self.mock_response.status = 200
        self.mock_response.text = AsyncMock(return_value='{}') # Default empty JSON
        self.mock_response.json = AsyncMock(return_value={})    # Default empty JSON
        
        async def mock_get_context_manager(*args, **kwargs): # Simulates `async with session.get(...) as response:`
            return self.mock_response
        
        self.mock_aiohttp_session_instance.get = MagicMock(return_value=MagicMock(__aenter__=mock_get_context_manager, __aexit__=AsyncMock()))
        self.MockAiohttpSessionClass.return_value = self.mock_aiohttp_session_instance

        self.market_provider = MarketDataProvider()
        # Crucially, re-assign jupiter_client to our controlled mock *after* MarketDataProvider init,
        # if its __init__ creates its own JupiterApiClient instance.
        # The patch above should ensure that when MarketDataProvider calls JupiterApiClient(...), it gets our mock.
        # So, self.market_provider.jupiter_client should already be self.mock_jupiter_client_instance.
        # We can assert this:
        self.assertIs(self.market_provider.jupiter_client, self.mock_jupiter_client_instance, 
                      "MarketDataProvider.jupiter_client was not patched correctly.")

        # Ensure MarketDataProvider uses a mock session for its direct aiohttp calls
        # MarketDataProvider creates its session in __aenter__
        # We will enter its context to allow session creation, then patch its session.
        await self.market_provider.__aenter__()
        # self.market_provider.session should now exist if its __aenter__ was called
        # We will ensure it's our mocked session for subsequent calls within tests
        self.market_provider.session = self.mock_aiohttp_session_instance


    async def asyncTearDown(self):
        self.mock_jup_client_patcher.stop()
        self.mock_aiohttp_session_patcher.stop()
        if self.market_provider.session: # Close session if __aenter__ was called
            await self.market_provider.__aexit__(None, None, None)

    # --- Tests for _get_jupiter_price ---
    async def test_get_jupiter_price_success(self):
        token_address = SOL_MINT
        reference_token = "USDC" # Symbol
        expected_price_data = {
            "id": SOL_MINT, "mintSymbol": "SOL", "vsToken": USDC_MINT, 
            "vsTokenSymbol": "USDC", "price": 150.0
        }
        # The JupiterApiClient.get_prices returns a dict where keys are token IDs
        mock_jup_api_response = {
            SOL_MINT: expected_price_data
        }
        self.mock_jupiter_client_instance.get_prices.return_value = mock_jup_api_response

        result = await self.market_provider._get_jupiter_price(token_address, reference_token)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], expected_price_data)
        self.mock_jupiter_client_instance.get_prices.assert_awaited_once_with(
            token_ids_list=[token_address], 
            vs_token_str=reference_token
        )

    async def test_get_jupiter_price_success_non_usdc_reference(self):
        token_address = SOL_MINT
        reference_token_symbol = "USDT"
        reference_token_mint = "Es9vMFrzaCERmJfrF4H2uZVwjqA2D2h6kJH5812iR3FT" # USDT Mint for example
        expected_price_data = {
            "id": SOL_MINT, "mintSymbol": "SOL", "vsToken": reference_token_mint, 
            "vsTokenSymbol": reference_token_symbol, "price": 150.5
        }
        mock_jup_api_response = {
            SOL_MINT: expected_price_data
        }
        self.mock_jupiter_client_instance.get_prices.return_value = mock_jup_api_response

        result = await self.market_provider._get_jupiter_price(token_address, reference_token_symbol)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], expected_price_data)
        self.mock_jupiter_client_instance.get_prices.assert_awaited_once_with(
            token_ids_list=[token_address], 
            vs_token_str=reference_token_symbol
        )

    async def test_get_jupiter_price_api_error(self):
        token_address = SOL_MINT
        reference_token = "USDC"
        error_message = "Jupiter API is down"
        self.mock_jupiter_client_instance.get_prices.side_effect = JupiterAPIError(error_message)

        result = await self.market_provider._get_jupiter_price(token_address, reference_token)

        self.assertFalse(result['success'])
        self.assertIn(error_message, result['error'])
        self.assertIsNone(result['data'])
        self.mock_jupiter_client_instance.get_prices.assert_awaited_once_with(
            token_ids_list=[token_address], 
            vs_token_str=reference_token
        )

    async def test_get_jupiter_price_token_not_found_in_response(self):
        token_address = SOL_MINT
        reference_token = "USDC"
        # JupiterApiClient.get_prices returns a dict, if token_address is not a key, it's a "not found"
        mock_jup_api_response = {
            "SOME_OTHER_MINT": {"id": "OTHER", "price": 10.0} # SOL_MINT is missing
        }
        self.mock_jupiter_client_instance.get_prices.return_value = mock_jup_api_response

        result = await self.market_provider._get_jupiter_price(token_address, reference_token)
        
        self.assertFalse(result['success'])
        self.assertIn(f"Price data for token {token_address} not found in Jupiter response", result['error'])
        self.assertIsNone(result['data'])

    async def test_get_jupiter_price_malformed_data_from_jupiter(self):
        token_address = SOL_MINT
        reference_token = "USDC"
        # Malformed: 'price' key is missing
        malformed_price_data = {"id": SOL_MINT, "mintSymbol": "SOL"} 
        mock_jup_api_response = { SOL_MINT: malformed_price_data }
        self.mock_jupiter_client_instance.get_prices.return_value = mock_jup_api_response

        result = await self.market_provider._get_jupiter_price(token_address, reference_token)

        self.assertFalse(result['success'])
        self.assertIn("Malformed price data from Jupiter", result['error'].lower()) # Check for part of the error message
        self.assertIsNone(result['data'])

    # --- Tests for _get_jupiter_token_info ---
    async def test_get_jupiter_token_info_success(self):
        token_address = SOL_MINT
        expected_token_info = {
            "address": SOL_MINT, "symbol": "SOL", "name": "Solana", "decimals": 9, 
            "logoURI": "some_sol_logo.png", "tags": ["native"]
        }
        # JupiterApiClient.get_token_info_list returns a list of token details
        self.mock_jupiter_client_instance.get_token_info_list.return_value = [expected_token_info]

        result = await self.market_provider._get_jupiter_token_info(token_address)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], expected_token_info)
        self.mock_jupiter_client_instance.get_token_info_list.assert_awaited_once_with(mint_address_list=[token_address])

    async def test_get_jupiter_token_info_api_error(self):
        token_address = SOL_MINT
        error_message = "Jupiter token info API is down"
        self.mock_jupiter_client_instance.get_token_info_list.side_effect = JupiterAPIError(error_message)

        result = await self.market_provider._get_jupiter_token_info(token_address)

        self.assertFalse(result['success'])
        self.assertIn(error_message, result['error'])
        self.assertIsNone(result['data'])
        self.mock_jupiter_client_instance.get_token_info_list.assert_awaited_once_with(mint_address_list=[token_address])

    async def test_get_jupiter_token_info_not_found_in_response(self):
        token_address = SOL_MINT
        # Simulate Jupiter client returning an empty list or list without the requested token
        self.mock_jupiter_client_instance.get_token_info_list.return_value = [
            {"address": USDC_MINT, "symbol": "USDC", "name": "USD Coin", "decimals": 6}
        ]

        result = await self.market_provider._get_jupiter_token_info(token_address)

        self.assertFalse(result['success'])
        self.assertIn(f"Token info for {token_address} not found in Jupiter response", result['error'])
        self.assertIsNone(result['data'])
    
    async def test_get_jupiter_token_info_empty_list_from_jupiter(self):
        token_address = SOL_MINT
        self.mock_jupiter_client_instance.get_token_info_list.return_value = [] # Empty list

        result = await self.market_provider._get_jupiter_token_info(token_address)

        self.assertFalse(result['success'])
        self.assertIn(f"Token info for {token_address} not found in Jupiter response", result['error'])
        self.assertIsNone(result['data'])

    async def test_get_jupiter_token_info_malformed_data(self):
        token_address = SOL_MINT
        # Malformed: missing 'decimals' or 'address'
        malformed_info = {"symbol": "SOL", "name": "Solana"} 
        self.mock_jupiter_client_instance.get_token_info_list.return_value = [malformed_info]

        result = await self.market_provider._get_jupiter_token_info(token_address)

        self.assertFalse(result['success'])
        # The error could be about missing 'address' during search or missing 'decimals' during validation
        self.assertTrue(
            f"Token info for {token_address} not found" in result['error'] or 
            "malformed token data from jupiter" in result['error'].lower()
        )
        self.assertIsNone(result['data'])

    # --- Tests for get_jupiter_swap_quote ---
    async def test_get_jupiter_swap_quote_success(self):
        input_mint = SOL_MINT
        output_mint = USDC_MINT
        amount_tokens = 0.5 # 0.5 SOL
        slippage = 100 # 1%

        # Mock for self.market_provider.get_token_info for input_mint
        mock_input_token_info = {
            'success': True, 
            'data': {"address": input_mint, "decimals": 9, "symbol": "SOL"}
        }
        # Mock for jupiter_client.get_quote
        mock_jup_quote_response = {"some_quote_key": "some_quote_value", "inAmount": "500000000"} # 0.5 SOL in lamports
        
        # Patch get_token_info directly on the instance for this test
        self.market_provider.get_token_info = AsyncMock(return_value=mock_input_token_info)
        self.mock_jupiter_client_instance.get_quote.return_value = mock_jup_quote_response

        result = await self.market_provider.get_jupiter_swap_quote(
            input_mint_str=input_mint, 
            output_mint_str=output_mint, 
            amount_in_tokens=amount_tokens, 
            slippage_bps=slippage
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], mock_jup_quote_response)
        self.market_provider.get_token_info.assert_awaited_once_with(input_mint)
        
        expected_amount_lamports = int(amount_tokens * (10**9)) # 0.5 SOL * 10^9 lamports/SOL
        self.mock_jupiter_client_instance.get_quote.assert_awaited_once_with(
            input_mint_str=input_mint,
            output_mint_str=output_mint,
            amount_lamports=expected_amount_lamports,
            slippage_bps=slippage,
            swap_mode=self.config.JUPITER_SWAP_MODE # Check if default swap_mode is passed
        )

    async def test_get_jupiter_swap_quote_token_info_fails(self):
        input_mint = SOL_MINT
        output_mint = USDC_MINT
        amount_tokens = 0.5

        mock_input_token_info_error = {'success': False, 'error': 'Failed to get token info'}
        self.market_provider.get_token_info = AsyncMock(return_value=mock_input_token_info_error)

        result = await self.market_provider.get_jupiter_swap_quote(
            input_mint_str=input_mint, 
            output_mint_str=output_mint, 
            amount_in_tokens=amount_tokens
        )

        self.assertFalse(result['success'])
        self.assertIn(mock_input_token_info_error['error'], result['error'])
        self.market_provider.get_token_info.assert_awaited_once_with(input_mint)
        self.mock_jupiter_client_instance.get_quote.assert_not_awaited() # Should not be called

    async def test_get_jupiter_swap_quote_token_info_missing_decimals(self):
        input_mint = SOL_MINT
        output_mint = USDC_MINT
        amount_tokens = 0.5

        mock_input_token_info_no_decimals = {
            'success': True, 
            'data': {"address": input_mint, "symbol": "SOL"} # Decimals missing
        }
        self.market_provider.get_token_info = AsyncMock(return_value=mock_input_token_info_no_decimals)

        result = await self.market_provider.get_jupiter_swap_quote(
            input_mint_str=input_mint, 
            output_mint_str=output_mint, 
            amount_in_tokens=amount_tokens
        )

        self.assertFalse(result['success'])
        self.assertIn("decimals not found for input token", result['error'].lower())
        self.mock_jupiter_client_instance.get_quote.assert_not_awaited()

    async def test_get_jupiter_swap_quote_jupiter_api_error(self):
        input_mint = SOL_MINT
        output_mint = USDC_MINT
        amount_tokens = 0.5

        mock_input_token_info = {
            'success': True, 
            'data': {"address": input_mint, "decimals": 9, "symbol": "SOL"}
        }
        jup_api_error_msg = "Jupiter quote API error"
        self.market_provider.get_token_info = AsyncMock(return_value=mock_input_token_info)
        self.mock_jupiter_client_instance.get_quote.side_effect = JupiterAPIError(jup_api_error_msg)

        result = await self.market_provider.get_jupiter_swap_quote(
            input_mint_str=input_mint, 
            output_mint_str=output_mint, 
            amount_in_tokens=amount_tokens
        )

        self.assertFalse(result['success'])
        self.assertIn(jup_api_error_msg, result['error'])
        self.market_provider.get_token_info.assert_awaited_once_with(input_mint)
        self.mock_jupiter_client_instance.get_quote.assert_awaited_once() # Check it was called

    # --- Tests for get_token_price (public method with fallback) ---
    async def test_get_token_price_jupiter_success(self):
        token_address = SOL_MINT
        reference_token = "USDC"
        expected_price_data = {"id": SOL_MINT, "price": 150.0}
        
        # Mock _get_jupiter_price to succeed
        self.market_provider._get_jupiter_price = AsyncMock(
            return_value={'success': True, 'data': expected_price_data, 'source': 'jupiter'}
        )
        # Ensure _get_dexscreener_price is not called
        self.market_provider._get_dexscreener_price = AsyncMock()

        result = await self.market_provider.get_token_price(token_address, reference_token)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], expected_price_data)
        self.market_provider._get_jupiter_price.assert_awaited_once_with(token_address, reference_token)
        self.market_provider._get_dexscreener_price.assert_not_awaited()
        # Check cache (optional, depends on how deep we test cache interaction here)
        self.assertEqual(self.market_provider.price_cache.get(f"{token_address}_{reference_token}_price"), expected_price_data)

    async def test_get_token_price_jupiter_fails_dexscreener_success(self):
        token_address = SOL_MINT
        reference_token = "USDC"
        dexscreener_price_data = {"priceUsd": "149.50", "symbol": "SOL"} # Dexscreener raw data part
        # _get_dexscreener_price returns a dict {'success': True, 'data': formatted_data}
        formatted_dex_data = {"id": SOL_MINT, "price": 149.50, "symbol": "SOL"} # Example formatted output

        self.market_provider._get_jupiter_price = AsyncMock(
            return_value={'success': False, 'error': 'Jupiter error'}
        )
        self.market_provider._get_dexscreener_price = AsyncMock(
            return_value={'success': True, 'data': formatted_dex_data, 'source': 'dexscreener'}
        )

        result = await self.market_provider.get_token_price(token_address, reference_token)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], formatted_dex_data)
        self.market_provider._get_jupiter_price.assert_awaited_once_with(token_address, reference_token)
        self.market_provider._get_dexscreener_price.assert_awaited_once_with(token_address)
        self.assertEqual(self.market_provider.price_cache.get(f"{token_address}_{reference_token}_price"), formatted_dex_data)

    async def test_get_token_price_jupiter_api_error_dexscreener_success(self):
        token_address = SOL_MINT
        reference_token = "USDC"
        formatted_dex_data = {"id": SOL_MINT, "price": 148.0, "symbol": "SOL"}

        # _get_jupiter_price in MarketDataProvider catches JupiterAPIError and returns a dict
        # So, we mock jupiter_client.get_prices to raise error, then check _get_jupiter_price behavior
        self.mock_jupiter_client_instance.get_prices.side_effect = JupiterAPIError("Jupiter is burning")
        
        self.market_provider._get_dexscreener_price = AsyncMock(
            return_value={'success': True, 'data': formatted_dex_data, 'source': 'dexscreener'}
        )

        # Clear cache for this specific test if testing a full flow including _get_jupiter_price call
        self.market_provider.price_cache.clear()

        result = await self.market_provider.get_token_price(token_address, reference_token)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], formatted_dex_data)
        self.mock_jupiter_client_instance.get_prices.assert_awaited_once() # Called by _get_jupiter_price
        self.market_provider._get_dexscreener_price.assert_awaited_once_with(token_address)

    async def test_get_token_price_all_fail(self):
        token_address = SOL_MINT
        reference_token = "USDC"

        self.market_provider._get_jupiter_price = AsyncMock(
            return_value={'success': False, 'error': 'Jupiter error'}
        )
        # Simulate _get_dexscreener_price raising an error directly
        self.market_provider._get_dexscreener_price = AsyncMock(side_effect=DexScreenerAPIError("Dexscreener down"))

        result = await self.market_provider.get_token_price(token_address, reference_token)

        self.assertFalse(result['success'])
        self.assertIn("Jupiter error", result['error'])
        self.assertIn("DexScreener Error: Dexscreener down", result['error'])
        self.market_provider._get_jupiter_price.assert_awaited_once_with(token_address, reference_token)
        self.market_provider._get_dexscreener_price.assert_awaited_once_with(token_address)

    # --- Tests for get_token_info (public method with fallback) ---
    async def test_get_token_info_jupiter_success(self):
        token_address = SOL_MINT
        expected_info = {"address": SOL_MINT, "symbol": "SOL", "decimals": 9}

        # Mock _get_jupiter_token_info to succeed
        self.market_provider._get_jupiter_token_info = AsyncMock(
            return_value={'success': True, 'data': expected_info, 'source': 'jupiter'}
        )
        # Ensure direct DexScreener call is not made by mocking its response setup if get_token_info tries it
        # For this test, primarily ensure _get_jupiter_token_info is used and is sufficient.

        result = await self.market_provider.get_token_info(token_address)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], expected_info)
        self.market_provider._get_jupiter_token_info.assert_awaited_once_with(token_address)
        # Assert that the aiohttp session wasn't used for a dexscreener token lookup IF _get_jupiter_token_info succeeded.
        # This depends on the internal structure of get_token_info. For now, assume no direct DexScreener call if Jupiter is fine.
        # self.mock_aiohttp_session_instance.get.assert_not_called() # Or specifically for dexscreener token URL
        self.assertEqual(self.market_provider.token_info_cache.get(f"{token_address}_info"), expected_info)

    async def test_get_token_info_jupiter_fails_dexscreener_direct_success(self):
        token_address = SOL_MINT
        # Mock _get_jupiter_token_info to fail
        self.market_provider._get_jupiter_token_info = AsyncMock(
            return_value={'success': False, 'error': 'Jupiter info error'}
        )

        # Setup mock response for the direct DexScreener call inside get_token_info
        dexscreener_api_raw_response = {
            "schemaVersion": "1.0.0",
            "pairs": [{
                "chainId": "solana", "dexId": "raydium", "url": "https://dexscreener.com/solana/pair",
                "pairAddress": "somepair", "baseToken": {"address": SOL_MINT, "name": "Solana", "symbol": "SOL"},
                "quoteToken": {"address": USDC_MINT, "name": "USD Coin", "symbol": "USDC"},
                "priceNative": "150.0", "priceUsd": "150.0",
                "liquidity": {"usd": 1000000, "base": 5000, "quote": 750000}
            }]
        }
        # The MarketDataProvider._convert_dexscreener_format is used internally
        # Let's assume it correctly extracts token info (address, symbol, name, decimals from baseToken)
        expected_dex_info = {
            "address": SOL_MINT, "symbol": "SOL", "name": "Solana", "decimals": None, # Decimals not directly in this example
            "priceUsd": 150.0, "liquidityUsd": 1000000
        }
        # We need to ensure _convert_dexscreener_format produces something valid that get_token_info would use.
        # For simplicity, let's mock the output of _convert_dexscreener_format as it is complex
        formatted_dex_info_for_cache = {"address": SOL_MINT, "name": "Solana", "symbol": "SOL", "decimals": 9} # Ideal

        self.mock_response.status = 200
        self.mock_response.json = AsyncMock(return_value=dexscreener_api_raw_response)
        self.mock_response.text = AsyncMock(return_value=json.dumps(dexscreener_api_raw_response))
        
        # Mock _convert_dexscreener_format to control its output for this test
        # This is tricky as it's an internal helper. We will rely on the actual implementation of get_token_info and its direct call.
        # The `get_token_info` method does the conversion. We need to ensure the mocked json response has enough data.
        # The direct dexscreener call in get_token_info will extract decimals if available in baseToken or quoteToken.
        # Let's refine the dexscreener_api_raw_response to include decimals:
        dexscreener_api_raw_response["pairs"][0]["baseToken"]["decimals"] = 9
        formatted_dex_info_for_cache["decimals"] = 9

        result = await self.market_provider.get_token_info(token_address)

        self.assertTrue(result['success'])
        # The data returned by get_token_info from its internal DexScreener call uses _convert_dexscreener_format.
        # The structure of data might be slightly different from `expected_dex_info` if it prioritizes certain fields.
        # We mainly check that success is True and some data is present. And that it was cached.
        self.assertEqual(result['data']['address'], SOL_MINT)
        self.assertEqual(result['data']['symbol'], "SOL")
        self.assertEqual(result['data']['decimals'], 9)
        self.market_provider._get_jupiter_token_info.assert_awaited_once_with(token_address)
        self.mock_aiohttp_session_instance.get.assert_called_once() # Check that aiohttp was used
        self.assertEqual(self.market_provider.token_info_cache.get(f"{token_address}_info"), result['data'])

    async def test_get_token_info_jupiter_api_error_dexscreener_direct_success(self):
        token_address = SOL_MINT
        self.mock_jupiter_client_instance.get_token_info_list.side_effect = JupiterAPIError("Jupiter burning")
        
        dexscreener_api_raw_response = {
            "pairs": [{
                "baseToken": {"address": SOL_MINT, "name": "Solana", "symbol": "SOL", "decimals": 9},
                "quoteToken": {"address": USDC_MINT, "name": "USD Coin", "symbol": "USDC"},
                "liquidity": {"usd": 1000000}
            }]
        }
        self.mock_response.status = 200
        self.mock_response.json = AsyncMock(return_value=dexscreener_api_raw_response)
        self.mock_response.text = AsyncMock(return_value=json.dumps(dexscreener_api_raw_response))
        self.market_provider.token_info_cache.clear()

        result = await self.market_provider.get_token_info(token_address)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['address'], SOL_MINT)
        self.mock_jupiter_client_instance.get_token_info_list.assert_awaited_once()
        self.mock_aiohttp_session_instance.get.assert_called_once() 

    async def test_get_token_info_all_sources_fail(self):
        token_address = SOL_MINT
        self.market_provider._get_jupiter_token_info = AsyncMock(
            return_value={'success': False, 'error': 'Jupiter info error'}
        )
        # Simulate direct DexScreener call failure (e.g., non-200 status)
        self.mock_response.status = 500
        self.mock_response.text = AsyncMock(return_value="Dexscreener server error")

        result = await self.market_provider.get_token_info(token_address)

        self.assertFalse(result['success'])
        self.assertIn("Jupiter info error", result['error'])
        self.assertIn("DexScreener API returned status 500", result['error']) # From the direct call error handling
        self.market_provider._get_jupiter_token_info.assert_awaited_once_with(token_address)
        self.mock_aiohttp_session_instance.get.assert_called_once()

if __name__ == '__main__':
    unittest.main() 