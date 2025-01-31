import requests
import logging
from typing import Dict, Tuple
from cachetools import TTLCache
from config import Config
import json

class EnhancedSecurity:
    def __init__(self, db):
        self.db = db
        self.strict_list = self._load_strict_list()
        self.dex_screener_cache = TTLCache(maxsize=1000, ttl=300)
        self.logger = logging.getLogger('Security')

    def _load_strict_list(self):
        try:
            response = requests.get(Config.JUPITER_STRICT_LIST, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to load strict list: {str(e)}")
            return []

    def verify_token(self, mint_address: str) -> Tuple[bool, str]:
        """Vérification de sécurité en 3 étapes avec diagnostic"""
        try:
            # Étape 1: Liste stricte Jupiter
            if not any(t.get('address') == mint_address for t in self.strict_list):
                return False, "non_listed"
            
            # Étape 2: Analyse on-chain
            onchain_data = self._get_onchain_metrics(mint_address)
            if onchain_data.get('liquidity_change_24h', 0) <= -0.2:
                return False, "liquidity_drop"
                
            # Étape 3: Pattern historique
            if self._detect_rug_pattern(mint_address):
                return False, "rug_pattern"
            
            return True, "verified"

        except Exception as e:
            self.logger.error(f"Échec vérification sécurité: {str(e)}")
            return False, "error"

    def _get_onchain_metrics(self, mint_address: str) -> Dict:
        try:
            if mint_address in self.dex_screener_cache:
                return self.dex_screener_cache[mint_address]
            
            response = requests.get(
                f"https://api.dexscreener.com/solana/{mint_address}",
                timeout=10
            )
            data = response.json()
            
            # Gestion des erreurs de structure de réponse
            pairs = data.get('pairs', [{}])
            first_pair = pairs[0] if pairs else {}
            holders = first_pair.get('holders', [{}])
            
            metrics = {
                'liquidity_change_24h': first_pair.get('liquidity', {}).get('usd_24h_change', 0),
                'top_holder_control': holders[0].get('balance', 0) / first_pair.get('totalSupply', 1) if first_pair.get('totalSupply', 0) > 0 else 1
            }
            
            self.dex_screener_cache[mint_address] = metrics
            return metrics
            
        except (KeyError, IndexError, requests.RequestException) as e:
            self.logger.warning(f"Error fetching onchain metrics: {str(e)}")
            return {'liquidity_change_24h': 0, 'top_holder_control': 1}

    def _detect_rug_pattern(self, mint_address: str) -> bool:
        try:
            historical_data = self.db.get_token_history(mint_address)
            return (
                historical_data.get('price_change_1h', 0) > 0.5 
                and historical_data.get('liquidity_change_1h', 0) < -0.8
            )
        except AttributeError:
            return False