import base58
import logging
from typing import Optional, Dict
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from app.config import Config

class SolanaWallet:
    def __init__(self, private_key: Optional[str] = None):
        """
        Initialise un portefeuille Solana.
        
        Args:
            private_key: Clé privée au format base58 (optionnel)
        """
        self.logger = logging.getLogger("wallet")
        self.client = Client(Config.SOLANA_RPC_URL)
        
        if private_key:
            self.keypair = Keypair.from_secret_key(base58.b58decode(private_key))
        else:
            self.keypair = Keypair()
            
        self.public_key = self.keypair.public_key
        self.logger.info(f"Portefeuille initialisé: {self.public_key}")
        
    def get_balance(self) -> float:
        """
        Récupère le solde SOL du portefeuille.
        
        Returns:
            Solde en SOL (float)
        """
        try:
            response = self.client.get_balance(self.public_key)
            balance_lamports = response['result']['value']
            balance_sol = balance_lamports / 10**9  # Conversion lamports -> SOL
            return balance_sol
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du solde: {str(e)}")
            return 0.0
            
    def get_token_balances(self) -> Dict[str, float]:
        """
        Récupère les soldes de tous les tokens SPL dans le portefeuille.
        
        Returns:
            Dictionnaire {adresse_token: solde}
        """
        token_balances = {}
        try:
            response = self.client.get_token_accounts_by_owner(
                self.public_key,
                TokenAccountOpts(program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"))
            )
            
            for account in response['result']['value']:
                data = account['account']['data']
                parsed_data = data[0]
                mint = parsed_data['parsed']['info']['mint']
                amount = float(parsed_data['parsed']['info']['tokenAmount']['uiAmount'])
                token_balances[mint] = amount
                
            return token_balances
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des tokens: {str(e)}")
            return {}
    
    def export_private_key(self) -> str:
        """
        Exporte la clé privée en format base58.
        
        Returns:
            Clé privée encodée en base58
        """
        return base58.b58encode(bytes(self.keypair.secret_key)).decode('ascii')
