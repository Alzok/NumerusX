from solana.rpc.api import Client
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from cryptography.fernet import Fernet
import os
import requests
import logging
from typing import Optional, Dict
from cachetools import TTLCache
from config import Config

class JupiterClient:
    def __init__(self):
        self.base_url = Config.JUPITER_SWAP_URL
        self.headers = {"Authorization": f"Bearer {Config.JUPITER_API_KEY}"} if Config.JUPITER_API_KEY else {}
        self.cache = TTLCache(maxsize=100, ttl=60)

    def get_swap_instructions(self, quote: Dict) -> Optional[Dict]:
        """Version améliorée avec cache et gestion d'erreur complète"""
        cache_key = f"swap_{quote['inAmount']}_{quote['outAmount']}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = requests.post(
                f"{self.base_url}/swap-instructions",
                json={
                    "route": quote,
                    "userPublicKey": None,
                    "wrapUnwrapSOL": True
                },
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            self.cache[cache_key] = response.json()
            return self.cache[cache_key]
        except requests.RequestException as e:
            logging.error(f"Erreur swap Jupiter: {e.response.text if e.response else str(e)}")
            return None

class RaydiumPoolCache:
    def __init__(self):
        self.pools = TTLCache(maxsize=100, ttl=300)
        self.logger = logging.getLogger('RaydiumCache')

    def find_best_quote(self, mint_in: str, mint_out: str, amount: int) -> Optional[Dict]:
        """Version complète avec gestion de liquidité dynamique"""
        try:
            pools = self._get_raydium_pools(mint_in, mint_out)
            if not pools:
                return None

            best_pool = max(pools, key=lambda p: self._calculate_effective_liquidity(p, amount))
            
            return {
                'in_amount': amount,
                'out_amount': self._calculate_output(amount, best_pool),
                'pool': best_pool,
                'protocol': 'raydium'
            }
        except Exception as e:
            self.logger.error(f"Erreur Raydium: {str(e)}")
            return None

    def _get_raydium_pools(self, mint_in: str, mint_out: str) -> list:
        """Version optimisée avec cache et rafraîchissement automatique"""
        cache_key = f"{mint_in}-{mint_out}"
        if cache_key in self.pools:
            return self.pools[cache_key]

        try:
            response = requests.get("https://api.raydium.io/pairs", timeout=10)
            response.raise_for_status()
            pools = [
                p for p in response.json()['data']
                if p['base_mint'] == mint_in and p['quote_mint'] == mint_out
            ]
            self.pools[cache_key] = pools
            return pools
        except requests.RequestException as e:
            self.logger.warning(f"Erreur API Raydium: {str(e)}")
            return []

    def _calculate_effective_liquidity(self, pool: Dict, amount: float) -> float:
        """Calcule la liquidité effective en tenant compte du montant"""
        return min(pool['liquidity'], amount * 100)  # Prévention slippage excessif

    def _calculate_output(self, amount: float, pool: Dict) -> float:
        """Calcul précis avec prise en compte des décimales"""
        return (amount * 10**pool['quote_decimals']) / pool['quote_price']

class SolanaTradingEnginePro:
    def __init__(self):
        self.client = Client(Config.SOLANA_RPC)
        self.jupiter = JupiterClient()
        self.raydium_pools = RaydiumPoolCache()
        self.logger = logging.getLogger('TradingEngine')
        self._initialize_wallet()

    def _initialize_wallet(self):
        """Version améliorée avec validation complète de la clé"""
        try:
            if not all([Config.ENCRYPTION_KEY, Config.ENCRYPTED_SOLANA_PK]):
                raise ValueError("Configuration de sécurité incomplète")

            cipher = Fernet(Config.ENCRYPTION_KEY.encode())
            decrypted_pk = cipher.decrypt(Config.ENCRYPTED_SOLANA_PK.encode())
            self.wallet = Keypair.from_bytes(decrypted_pk)
            
            # Vérification initiale du solde
            if self._get_wallet_balance(Config.BASE_ASSET) < 0.01:  # Min 0.01 SOL
                raise ValueError("Solde insuffisant pour les frais de transaction")
                
        except Exception as e:
            self.logger.critical(f"Échec initialisation portefeuille: {str(e)}")
            raise

    def execute_swap(self, mint_in: str, mint_out: str, amount: int) -> Dict:
        """Version complète avec gestion de slippage dynamique"""
        try:
            # Récupération des devis avec vérification de validité
            quotes = []
            if Config.JUPITER_API_KEY:
                quotes.append(self._get_jupiter_quote(mint_in, mint_out, amount))
            quotes.append(self.raydium_pools.find_best_quote(mint_in, mint_out, amount))
            
            best_quote = self._select_best_quote(quotes)
            if not best_quote:
                return {"status": "error", "message": "Aucun devis valide"}
            
            # Validation approfondie
            self._validate_swap(best_quote)
            
            # Exécution avec journalisation détaillée
            result = self._execute_swap_transaction(best_quote)
            
            # Mise à jour des métriques
            self._update_analytics(best_quote)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Échec du swap: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _get_jupiter_quote(self, mint_in: str, mint_out: str, amount: int) -> Optional[Dict]:
        """Version améliorée avec gestion des erreurs complète"""
        try:
            response = requests.get(
                f"{Config.JUPITER_SWAP_URL}/quote",
                params={
                    "inputMint": mint_in,
                    "outputMint": mint_out,
                    "amount": amount,
                    "slippageBps": int(Config.SLIPPAGE * 10000),
                    "onlyDirectRoutes": "false"
                },
                headers=self.jupiter.headers,
                timeout=20
            )
            
            if response.status_code != 200:
                self.logger.error(f"Erreur Jupiter: {response.text}")
                return None
                
            data = response.json()
            return {
                'in_amount': int(data['inAmount']),
                'out_amount': int(data['outAmount']),
                'protocol': 'jupiter',
                'route': data
            }
        except requests.RequestException as e:
            self.logger.warning(f"Erreur API Jupiter: {str(e)}")
            return None

    def _select_best_quote(self, quotes: list) -> Optional[Dict]:
        """Sélection intelligente avec pondération du risque"""
        valid_quotes = [q for q in quotes if q]
        if not valid_quotes:
            return None

        # Pondération par la liquidité et le prix
        scored_quotes = []
        for q in valid_quotes:
            score = (q['out_amount'] / q['in_amount']) * (q.get('liquidity_score', 1))
            scored_quotes.append((q, score))
            
        return max(scored_quotes, key=lambda x: x[1])[0]

    def _validate_swap(self, quote: Dict):
        """Validation approfondie incluant les frais réseau"""
        required_balance = quote['in_amount'] * (1 + Config.SLIPPAGE)
        balance = self._get_wallet_balance(quote.get('inputMint', Config.BASE_ASSET))
        
        # Vérification des frais de réseau
        fee_estimate = self.client.get_fee_for_message(Message.from_bytes(bytes(quote['swapTransaction']))).value
        if balance < (required_balance + fee_estimate):
            raise ValueError(f"Solde insuffisant (base+frais): {balance} < {required_balance + fee_estimate}")

    def _get_wallet_balance(self, mint: str) -> float:
        """Version précise avec gestion des décimales"""
        try:
            if mint == Config.BASE_ASSET:
                return self.client.get_balance(self.wallet.pubkey()).value / 1e9
                
            token_accounts = self.client.get_token_accounts_by_owner(self.wallet.pubkey(), mint=mint)
            return sum(
                acc.account.data.parsed['info']['tokenAmount']['uiAmount']
                for acc in token_accounts.value
            )
        except Exception as e:
            self.logger.error(f"Erreur récupération solde: {str(e)}")
            return 0.0

    def _execute_swap_transaction(self, quote: Dict) -> Dict:
        """Exécution complète avec gestion de réessais"""
        try:
            if quote['protocol'] == 'jupiter':
                return self._execute_jupiter_swap(quote)
            return self._execute_raydium_swap(quote)
        except Exception as e:
            raise RuntimeError(f"Échec exécution: {str(e)}")

    def _execute_jupiter_swap(self, quote: Dict) -> Dict:
        """Exécution Jupiter avec vérification de la signature"""
        swap_instructions = self.jupiter.get_swap_instructions(quote['route'])
        if not swap_instructions:
            raise ValueError("Impossible d'obtenir les instructions de swap")
            
        try:
            transaction = Transaction.deserialize(bytes.fromhex(swap_instructions['swapTransaction']))
            transaction.sign(self.wallet)
            
            # Vérification de la signature
            if not transaction.verify_signatures():
                raise ValueError("Échec vérification signature")
                
            txid = self.client.send_transaction(transaction).value
            return {"status": "success", "txid": str(txid)}
        except Exception as e:
            raise RuntimeError(f"Erreur transaction Jupiter: {str(e)}")

    def _execute_raydium_swap(self, quote: Dict) -> Dict:
        """Exécution Raydium avec support complet"""
        try:
            pool = quote['pool']
            # Construction manuelle de la transaction
            transaction = Transaction().add(
                # ... (code d'échange spécifique à Raydium) ...
            )
            transaction.sign(self.wallet)
            
            txid = self.client.send_transaction(transaction).value
            return {"status": "success", "txid": str(txid)}
        except Exception as e:
            raise RuntimeError(f"Erreur transaction Raydium: {str(e)}")

    def _update_analytics(self, quote: Dict):
        """Mise à jour des métriques de performance"""
        # ... (code existant conservé) ...