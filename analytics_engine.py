from banana_gun_sdk import BananaGunSDK

class PatternEngine:
    def detect_pump(self, data):
        return (
            data['price_change_1h'] > 0.45
            and data['volume_change_24h'] > 2.8
            and data['liquidity_usd'] > 25000
        )
    
    def detect_rug(self, data):
        return (
            data['liquidity_change_24h'] < -0.85
            and data['tx_count_1h'] < 5
        )

class VerificationHub(BananaGunSDK):
    def full_verification(self, token_address):
        return (
            self.get_rugcheck_score(token_address) >= 90
            and self.get_bananagun_safety(token_address) >= 85
            and not self.is_bundled(token_address)
        )