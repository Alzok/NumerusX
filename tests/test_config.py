import unittest
from app.config import get_config

class TestConfigJupiterV6(unittest.TestCase):

    def setUp(self):
        self.config = get_config()

    def test_jupiter_api_hostnames_exist(self):
        self.assertIsNotNone(self.config.jupiter.lite_api_hostname, "JUPITER_LITE_API_HOSTNAME is None")
        self.assertIsNotNone(self.config.jupiter.pro_api_hostname, "JUPITER_PRO_API_HOSTNAME is None")
        self.assertIsInstance(self.config.jupiter.lite_api_hostname, str, "JUPITER_LITE_API_HOSTNAME is not a string")
        self.assertIsInstance(self.config.jupiter.pro_api_hostname, str, "JUPITER_PRO_API_HOSTNAME is not a string")

    def test_jupiter_api_paths_exist(self):
        # Test a few key paths
        self.assertIsNotNone(self.config.jupiter.swap_api_path, "JUPITER_SWAP_API_PATH is None")
        self.assertIsNotNone(self.config.jupiter.price_api_path, "JUPITER_PRICE_API_PATH is None")

    def test_jupiter_transaction_parameters_exist(self):
        self.assertIsNotNone(self.config.jupiter.default_slippage_bps, "JUPITER_DEFAULT_SLIPPAGE_BPS is None")
        self.assertIsInstance(self.config.jupiter.default_slippage_bps, int, "JUPITER_DEFAULT_SLIPPAGE_BPS is not an int")
        
        # This can be None if not set, so we only check type if not None
        if self.config.jupiter.compute_unit_price_micro_lamports is not None:
            self.assertIsInstance(self.config.jupiter.compute_unit_price_micro_lamports, str) # Should be string

        self.assertIsNotNone(self.config.jupiter.max_retries, "JUPITER_MAX_RETRIES is None")
        self.assertIsInstance(self.config.jupiter.max_retries, int, "JUPITER_MAX_RETRIES is not an int")

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