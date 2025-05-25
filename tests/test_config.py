import unittest
from app.config import Config

class TestConfigJupiterV6(unittest.TestCase):

    def setUp(self):
        self.config = Config()

    def test_jupiter_api_hostnames_exist(self):
        self.assertTrue(hasattr(self.config, 'JUPITER_LITE_API_HOSTNAME'), "JUPITER_LITE_API_HOSTNAME missing")
        self.assertTrue(hasattr(self.config, 'JUPITER_PRO_API_HOSTNAME'), "JUPITER_PRO_API_HOSTNAME missing")
        self.assertIsNotNone(self.config.JUPITER_LITE_API_HOSTNAME, "JUPITER_LITE_API_HOSTNAME is None")
        self.assertIsNotNone(self.config.JUPITER_PRO_API_HOSTNAME, "JUPITER_PRO_API_HOSTNAME is None")
        self.assertIsInstance(self.config.JUPITER_LITE_API_HOSTNAME, str, "JUPITER_LITE_API_HOSTNAME is not a string")
        self.assertIsInstance(self.config.JUPITER_PRO_API_HOSTNAME, str, "JUPITER_PRO_API_HOSTNAME is not a string")

    def test_jupiter_api_paths_exist(self):
        # Test a few key paths
        self.assertTrue(hasattr(self.config, 'JUPITER_SWAP_API_PATH'), "JUPITER_SWAP_API_PATH missing")
        self.assertIsNotNone(self.config.JUPITER_SWAP_API_PATH, "JUPITER_SWAP_API_PATH is None")
        self.assertTrue(hasattr(self.config, 'JUPITER_PRICE_API_PATH'), "JUPITER_PRICE_API_PATH missing")
        self.assertIsNotNone(self.config.JUPITER_PRICE_API_PATH, "JUPITER_PRICE_API_PATH is None")

    def test_jupiter_transaction_parameters_exist(self):
        self.assertTrue(hasattr(self.config, 'JUPITER_DEFAULT_SLIPPAGE_BPS'), "JUPITER_DEFAULT_SLIPPAGE_BPS missing")
        self.assertIsNotNone(self.config.JUPITER_DEFAULT_SLIPPAGE_BPS, "JUPITER_DEFAULT_SLIPPAGE_BPS is None")
        self.assertIsInstance(self.config.JUPITER_DEFAULT_SLIPPAGE_BPS, int, "JUPITER_DEFAULT_SLIPPAGE_BPS is not an int")
        
        self.assertTrue(hasattr(self.config, 'JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS'), "JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS missing")
        # This can be None if not set, so we only check existence or type if not None
        if hasattr(self.config, 'JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS') and self.config.JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS is not None:
            self.assertIsInstance(self.config.JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS, (int, str)) # Can be int or "auto"

        self.assertTrue(hasattr(self.config, 'JUPITER_MAX_RETRIES'), "JUPITER_MAX_RETRIES missing")
        self.assertIsNotNone(self.config.JUPITER_MAX_RETRIES, "JUPITER_MAX_RETRIES is None")
        self.assertIsInstance(self.config.JUPITER_MAX_RETRIES, int, "JUPITER_MAX_RETRIES is not an int")

    def test_jupiter_deprecated_constants_still_accessible_or_none(self):
        # Example: Check if a deprecated constant is either gone, None, or has a specific value if retained
        # This depends on how deprecation is handled (removal, set to None, or kept with old value)
        # For now, let's assume they might still exist but could be None
        if hasattr(self.config, 'JUPITER_API_BASE_URL_LEGACY'): # DEPRECATED_JUPITER_API_V4_URL
             # No assertion on value, just that it can be accessed if it exists
            pass
        
        # Check one of the old V6 style base URLs that were marked for deprecation
        if hasattr(self.config, 'JUPITER_API_V6_URL'): # This was the old general one
            pass


    def test_jupiter_url_getters(self):
        # These methods might be obsolete if JupiterApiClient handles URL construction.
        # If they are kept, ensure they function or are marked as deprecated.
        # Example: Assuming get_jupiter_quote_url might still exist
        if hasattr(self.config, 'get_jupiter_quote_url'):
            # Further tests could check the output if the method is expected to be functional
            # For now, just checking existence.
            quote_url_method = getattr(self.config, 'get_jupiter_quote_url')
            self.assertTrue(callable(quote_url_method))
            # try:
            #     url = quote_url_method() # Call it to see if it raises errors
            #     self.assertIsInstance(url, str)
            # except Exception as e:
            #     # This is fine if it's expected to be obsolete and potentially raise NotImplementedError
            #     pass 

if __name__ == '__main__':
    unittest.main() 