from solana.rpc.api import Client
from solders.keypair import Keypair
from cryptography.fernet import Fernet
import os
import requests
import logging
from config import Config

class JupiterClient:
    def __init__(self, api_key=None):
        self.base_url = Config.JUPITER_QUOTE_URL
        self.api_key = api_key

class RaydiumPoolCache:
    def find_best_quote(self, mint_in, mint_out, amount):
        # Implémentation simplifiée
        return None

class SolanaTradingEnginePro:
    def __init__(self):
        self.client = Client(Config.SOLANA_RPC)
        self.jupiter = JupiterClient()
        self.raydium_pools = RaydiumPoolCache()
        self.logger = logging.getLogger('TradingEngine')
        self._initialize_wallet()

    def _initialize_wallet(self):
        """Charge le portefeuille de manière sécurisée"""
        try:
            enc_key = os.getenv("ENCRYPTION_KEY")
            encrypted_pk = os.getenv("ENCRYPTED_SOLANA_PK")
            
            if not enc_key or not encrypted_pk:
                raise ValueError("Configuration de sécurité manquante")
                
            cipher = Fernet(enc_key.encode())
            decrypted_pk = cipher.decrypt(encrypted_pk.encode()).decode()
            self.wallet = Keypair.from_base58_string(decrypted_pk)
            
        except Exception as e:
            self.logger.critical(f"Échec d'initialisation du portefeuille: {str(e)}")
            raise

    def execute_swap(self, mint_in: str, mint_out: str, amount: int):
        """Exécute un swap optimisé"""
        try:
            jup_quote = self._get_jupiter_quote(mint_in, mint_out, amount)
            ray_quote = self.raydium_pools.find_best_quote(mint_in, mint_out, amount)
            
            best_quote = self._select_best_quote(jup_quote, ray_quote)
            if not best_quote:
                raise ValueError("Aucun quote valide disponible")
                
            self._validate_swap(best_quote)
            return self._send_transaction(best_quote)
            
        except Exception as e:
            self.logger.error(f"Échec du swap: {str(e)}")
            return None

    def _get_jupiter_quote(self, mint_in, mint_out, amount):
        try:
            response = requests.get(
                f"{self.jupiter.base_url}?"
                f"inputMint={mint_in}&"
                f"outputMint={mint_out}&"
                f"amount={amount}&"
                f"slippageBps={int(Config.SLIPPAGE * 100)}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.warning(f"Erreur Jupiter API: {str(e)}")
            return None

    def _select_best_quote(self, *quotes):
        valid_quotes = [q for q in quotes if q and 'out_amount' in q and 'in_amount' in q]
        if not valid_quotes:
            return None
        return max(valid_quotes, key=lambda x: x['out_amount'] / x['in_amount'])

    def _validate_swap(self, quote):
        required_balance = quote['in_amount'] * (1 + Config.SLIPPAGE)
        balance = self._get_wallet_balance(Config.BASE_ASSET)
        
        if balance < required_balance:
            raise ValueError(f"Solde insuffisant: {balance} < {required_balance}")

    def _get_wallet_balance(self, mint):
        # Implémentation simplifiée
        return 1000000000  # À remplacer par une vraie implémentation

    def _send_transaction(self, quote):
        # Implémentation simplifiée
        return {"status": "success", "tx_hash": "simulated_tx"}