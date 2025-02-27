import os
import time
import json
import base64
import requests
from typing import Dict, List, Any, Optional, Tuple
from solana.rpc.api import Client
from solana.transaction import Transaction
from solders.pubkey import Pubkey
from solana.rpc.types import TxOpts

from utils.logger import DexLogger
from security.security import SecurityManager
from market.market_data_fetcher import MarketDataFetcher

logger = DexLogger("TradeExecutor")

class TradeExecutor:
    """
    Classe responsable de l'exécution des ordres de trading.
    Séparée du RiskManager pour une séparation claire des responsabilités.
    """
    def __init__(self, solana_rpc_url: str = None):
        self.solana_rpc_url = solana_rpc_url or os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self.solana_client = Client(self.solana_rpc_url)
        self.jupiter_api_url = "https://quote-api.jup.ag/v6"
        self.security_manager = SecurityManager()
        self.market_data = MarketDataFetcher()
        self._load_wallet()
        
    def _load_wallet(self):
        """
        Charge le portefeuille Solana de manière sécurisée.
        """
        try:
            encrypted_pk = os.getenv("ENCRYPTED_SOLANA_PK")
            if not encrypted_pk:
                logger.error("Clé privée Solana non trouvée dans les variables d'environnement")
                raise ValueError("Clé privée Solana manquante")
                
            self.private_key = self.security_manager.decrypt_data(encrypted_pk)
            # Validation supplémentaire de la clé
            if len(base64.b64decode(self.private_key)) != 64:
                raise ValueError("Format de clé privée Solana invalide")
                
            logger.info("Portefeuille Solana chargé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du portefeuille: {str(e)}")
            raise
        
    def check_network_fees(self) -> Dict:
        """
        Vérifie les frais actuels du réseau Solana pour s'assurer qu'ils sont raisonnables.
        """
        try:
            response = self.solana_client.get_recent_blockhash()
            if not response.value:
                return {"success": False, "error": "Impossible d'obtenir les informations de blockhash récent"}
                
            fee_calculator = response.value.fee_calculator
            lamports_per_signature = fee_calculator.lamports_per_signature
            
            return {
                "success": True, 
                "lamports_per_signature": lamports_per_signature,
                "sol_per_signature": lamports_per_signature / 1_000_000_000
            }
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des frais réseau: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_fee_for_message(self, transaction_data: Dict) -> Dict:
        """
        Estime les frais pour une transaction spécifique.
        """
        try:
            encoded_message = transaction_data.get("encodedMessage")
            if not encoded_message:
                return {"success": False, "error": "Message de transaction manquant"}
                
            response = self.solana_client.get_fee_for_message(encoded_message)
            if not response.value:
                return {"success": False, "error": "Impossible d'estimer les frais"}
                
            estimated_fee = response.value
            return {
                "success": True,
                "estimated_fee_lamports": estimated_fee,
                "estimated_fee_sol": estimated_fee / 1_000_000_000
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'estimation des frais: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def find_best_quote(self, input_mint: str, output_mint: str, amount: int,
                        slippage_bps: int = 50, min_liquidity_usd: float = 10000) -> Dict:
        """
        Trouve la meilleure cotation pour un swap avec vérification de liquidité minimale.
        """
        try:
            # Vérification de la liquidité du token de sortie
            liquidity_info = self.market_data.check_token_liquidity(output_mint)
            if liquidity_info and liquidity_info.get("total_liquidity_usd", 0) < min_liquidity_usd:
                logger.warning(f"Liquidité insuffisante pour {output_mint}: ${liquidity_info.get('total_liquidity_usd', 0)}")
                return {"success": False, "error": "Liquidité insuffisante"}
                
            quote = self.market_data.get_jupiter_quote(input_mint, output_mint, amount, slippage_bps)
            if not quote:
                return {"success": False, "error": "Impossible d'obtenir une cotation"}
                
            return {
                "success": True,
                "quote": quote
            }
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de la meilleure cotation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def execute_swap(self, input_mint: str, output_mint: str, amount: int, 
                    slippage_bps: int = 50) -> Dict:
        """
        Exécute un swap avec vérification préalable des frais réseau et de transaction.
        """
        try:
            # 1. Vérifier les frais réseau
            network_fees = self.check_network_fees()
            if not network_fees.get("success"):
                return {"success": False, "error": f"Erreur de frais réseau: {network_fees.get('error')}"}
                
            # Frais trop élevés?
            if network_fees.get("sol_per_signature", 0) > 0.001:  # Exemple: 0.001 SOL
                return {"success": False, "error": "Frais réseau trop élevés"}
                
            # 2. Obtenir la cotation
            quote_result = self.find_best_quote(input_mint, output_mint, amount, slippage_bps)
            if not quote_result.get("success"):
                return quote_result
                
            quote = quote_result["quote"]
            
            # 3. Créer la transaction via Jupiter API
            swap_params = {
                "quoteResponse": quote["raw_data"],
                "userPublicKey": self.public_key.to_base58(),
                "wrapUnwrapSOL": True
            }
            
            headers = {"Content-Type": "application/json"}
            swap_response = requests.post(
                f"{self.jupiter_api_url}/swap",
                headers=headers,
                json=swap_params
            )
            
            if swap_response.status_code != 200:
                return {"success": False, "error": f"Erreur de l'API Jupiter: {swap_response.status_code}, {swap_response.text}"}
                
            swap_transaction = swap_response.json()
            
            # 4. Vérifier les frais de transaction
            fee_result = self.get_fee_for_message(swap_transaction)
            if not fee_result.get("success"):
                return {"success": False, "error": f"Erreur d'estimation des frais: {fee_result.get('error')}"}
                
            # 5. Signer et envoyer la transaction
            transaction = Transaction.deserialize(base64.b64decode(swap_transaction["transaction"]))
            signed_tx = self.sign_transaction(transaction)
            
            tx_response = self.solana_client.send_raw_transaction(signed_tx.serialize())
            if not tx_response.value:
                return {"success": False, "error": f"Erreur d'envoi de transaction: {tx_response.error}"}
                
            logger.info(f"Swap exécuté: {input_mint} -> {output_mint}, Montant: {amount}, TxID: {tx_response.value}")
            
            return {
                "success": True,
                "tx_id": tx_response.value,
                "input_mint": input_mint,
                "output_mint": output_mint,
                "input_amount": amount,
                "expected_output_amount": quote["output_amount"],
                "price": quote["price"],
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du swap: {str(e)}")
            return {"success": False, "error": str(e)}
