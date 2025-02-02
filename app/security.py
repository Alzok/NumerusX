import requests
import logging
from typing import Dict, Tuple
from cachetools import TTLCache
from config import Config

class EnhancedSecurity:
    def __init__(self, db):
        self.db = db
        self.strict_list_cache = TTLCache(maxsize=1, ttl=3600)  # Cache 1h
        self.metrics_cache = TTLCache(maxsize=1000, ttl=300)    # Cache 5min
        self.logger = logging.getLogger('Security')

    def verify_token(self, mint_address: str) -> Tuple[bool, str]:
        """Vérification en 3 étapes améliorée"""
        try:
            # Étape 1: Liste stricte avec cache
            if not self._check_strict_list(mint_address):
                return False, "non_listed"

            # Étape 2: Métriques on-chain avec revalidation
            metrics = self._get_cached_metrics(mint_address)
            if metrics['liquidity_change_24h'] <= -0.2:
                return False, "liquidity_drop"

            # Étape 3: Détection de rug-pull améliorée
            if self._detect_rug_pattern(mint_address):
                return False, "rug_pattern"

            return True, "verified"
        except Exception as e:
            self.logger.error(f"Échec vérification: {str(e)}", exc_info=True)
            return False, "error"

    def _check_strict_list(self, mint_address: str) -> bool:
        """Vérification avec cache et rafraîchissement automatique"""
        if 'strict_list' in self.strict_list_cache:
            return mint_address in self.strict_list_cache['strict_list']

        try:
            response = requests.get(Config.JUPITER_STRICT_LIST, timeout=10)
            response.raise_for_status()
            strict_list = [t['address'] for t in response.json()]
            self.strict_list_cache['strict_list'] = strict_list
            return mint_address in strict_list
        except requests.RequestException as e:
            self.logger.warning(f"Erreur liste stricte: {str(e)}")
            return False  # Fail-safe

    def _get_cached_metrics(self, mint_address: str) -> Dict:
        """Récupération optimisée des métriques avec cache"""
        if mint_address in self.metrics_cache:
            return self.metrics_cache[mint_address]

        metrics = self._fetch_onchain_metrics(mint_address)
        self.metrics_cache[mint_address] = metrics
        return metrics

    def _fetch_onchain_metrics(self, mint_address: str) -> Dict:
        """Récupération robuste des métriques on-chain"""
        try:
            # Essayer DexScreener d'abord
            dex_data = requests.get(f"https://api.dexscreener.com/solana/{mint_address}", timeout=10).json()
            pair = dex_data.get('pairs', [{}])[0]
            
            # Fallback Jupiter si nécessaire
            if not pair.get('liquidity'):
                jup_data = requests.get(f"{Config.JUPITER_PRICE_URL}/{mint_address}", timeout=10).json()
                pair.update(jup_data.get('data', {}))

            return {
                'liquidity_change_24h': pair.get('liquidity', {}).get('usd_24h_change', 0),
                'top_holder_control': self._calculate_holder_control(pair)
            }
        except Exception as e:
            self.logger.error(f"Erreur métriques: {str(e)}")
            return {'liquidity_change_24h': 0, 'top_holder_control': 0}

    def _calculate_holder_control(self, pair_data: Dict) -> float:
        """Calcul précis de la concentration des holders"""
        holders = pair_data.get('holders', [])
        if not holders:
            return 0.0
            
        total_supply = pair_data.get('totalSupply', 1)
        top_holder = holders[0].get('balance', 0)
        return min(top_holder / total_supply, 1.0)

    def _detect_rug_pattern(self, mint_address: str) -> bool:
        """Détection améliorée des rug-pulls avec analyse temporelle"""
        try:
            history = self.db.get_token_history(mint_address)
            if len(history) < 24:
                return False  # Pas assez de données

            # Analyse des dernières 6 heures
            recent = history[-6:]
            price_change = (recent[-1]['price'] - recent[0]['price']) / recent[0]['price']
            liquidity_change = (recent[-1]['liquidity'] - recent[0]['liquidity']) / recent[0]['liquidity']

            return price_change > 0.5 and liquidity_change < -0.8
        except Exception as e:
            self.logger.warning(f"Erreur détection rug-pull: {str(e)}")
            return False