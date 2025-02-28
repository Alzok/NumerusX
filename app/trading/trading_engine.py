import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.signature import Signature
from solana.rpc.commitment import Confirmed
from solders.fee_calculator import FeeCalculator
import base58
import os
import json

from market.market_data import MarketDataProvider

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
logger = logging.getLogger("trading_engine")

class TradingEngine:
    """Moteur de trading optimisé pour exécuter des opérations sur les DEX Solana."""
    
    def __init__(self, wallet_path: str, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        """
        Initialise le moteur de trading.
        
        Args:
            wallet_path: Chemin vers le fichier de clé du portefeuille
            rpc_url: URL du point de terminaison RPC Solana
        """
        self.rpc_url = rpc_url
        self.client = AsyncClient(rpc_url)
        self.wallet = self._initialize_wallet(wallet_path)
        self.market_data_provider = None
        self.last_transaction_signature = None
        self.transaction_history = []
        
    def _initialize_wallet(self, wallet_path: str) -> Keypair:
        """
        Initialise le portefeuille de manière sécurisée avec validation.
        
        Args:
            wallet_path: Chemin vers le fichier de clé du portefeuille
            
        Returns:
            Instance Keypair pour le portefeuille
        """
        try:
            if not os.path.exists(wallet_path):
                raise FileNotFoundError(f"Fichier de portefeuille non trouvé: {wallet_path}")
                
            with open(wallet_path, 'r') as f:
                try:
                    # Essayer de charger comme JSON (format Solana CLI)
                    key_data = json.load(f)
                    if isinstance(key_data, list):
                        private_key = bytes(key_data)
                    else:
                        raise ValueError("Format de clé non reconnu")
                except json.JSONDecodeError:
                    # Essayer de charger comme Base58 (format .key)
                    content = f.read().strip()
                    try:
                        private_key = base58.b58decode(content)
                    except Exception:
                        raise ValueError("Format de clé non reconnu")
            
            # Vérifier que la longueur de la clé est correcte
            if len(private_key) != 64:
                raise ValueError(f"Clé privée invalide: longueur {len(private_key)}, attendue 64")
                
            keypair = Keypair.from_bytes(private_key)
            logger.info(f"Portefeuille initialisé avec succès. Adresse: {keypair.pubkey()}")
            return keypair
            
        except Exception as e:
            logger.error(f"Échec de l'initialisation du portefeuille: {e}")
            # Implémenter une stratégie de repli - par exemple, utiliser une clé de secours
            try:
                # Essayer d'utiliser un fichier de clé de secours ou une variable d'environnement
                backup_wallet_path = os.environ.get("BACKUP_WALLET_PATH")
                if backup_wallet_path and os.path.exists(backup_wallet_path):
                    logger.warning(f"Utilisation du portefeuille de secours: {backup_wallet_path}")
                    return self._initialize_wallet(backup_wallet_path)
            except Exception as backup_e:
                logger.critical(f"Échec également avec le portefeuille de secours: {backup_e}")
            
            raise ValueError(f"Impossible d'initialiser le portefeuille: {e}")
            
    async def __aenter__(self):
        """Initialise les ressources asynchrones."""
        self.market_data_provider = MarketDataProvider()
        await self.market_data_provider.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Libère les ressources asynchrones."""
        if self.market_data_provider:
            await self.market_data_provider.__aexit__(exc_type, exc_val, exc_tb)
        await self.client.close()
            
    async def get_fee_for_message(self, transaction: Transaction) -> int:
        """
        Estime les frais pour une transaction avant exécution.
        
        Args:
            transaction: Transaction à analyser
            
        Returns:
            Frais estimés en lamports
        """
        try:
            # Convertir la transaction en message
            recent_blockhash = await self.client.get_latest_blockhash()
            transaction.recent_blockhash = recent_blockhash.value.blockhash
            
            # Obtenir l'estimation des frais
            fee_response = await self.client.get_fee_for_message(
                transaction.serialize_message()
            )
            
            if fee_response.value is None:
                # Utiliser une estimation de repli
                fee_calculator = FeeCalculator(5000)  # 5000 lamports par signature
                signatures_count = len(transaction.signatures)
                estimated_fee = fee_calculator.calculate_fee(transaction.serialize_message()) 
                logger.warning(f"Utilisation de l'estimation de repli des frais: {estimated_fee} lamports")
                return estimated_fee
                
            return fee_response.value
            
        except Exception as e:
            logger.error(f"Erreur lors de l'estimation des frais: {e}")
            # Valeur par défaut sécuritaire
            return 5000 * len(transaction.signatures)  # 5000 lamports par signature
            
    async def execute_swap(self, input_token: str, output_token: str, 
                          amount_in: float, slippage: float = 0.5) -> Dict[str, Any]:
        """
        Exécute un swap entre deux tokens avec estimation des frais.
        
        Args:
            input_token: Adresse du token d'entrée
            output_token: Adresse du token de sortie
            amount_in: Montant à échanger
            slippage: Tolérance de slippage en pourcentage
            
        Returns:
            Résultat de la transaction
        """
        try:
            # Obtenir les meilleures routes pour le swap
            routes = await self._get_swap_routes(input_token, output_token, amount_in)
            
            # Sélectionner la meilleure route en tenant compte du prix et des frais
            best_route = await self._select_best_quote(routes, amount_in)
            
            # Estimer les frais avant d'exécuter
            transaction_data = await self._build_swap_transaction(best_route)
            transaction = Transaction.deserialize(transaction_data["transaction"])
            
            estimated_fee = await self.get_fee_for_message(transaction)
            logger.info(f"Frais estimés pour cette transaction: {estimated_fee / 1_000_000_000:.6f} SOL")
            
            # Exécuter la transaction
            result = await self._execute_transaction(transaction)
            
            # Enregistrer l'historique
            self._record_transaction(result, {
                "input_token": input_token,
                "output_token": output_token,
                "amount_in": amount_in,
                "route": best_route["market"],
                "expected_amount_out": best_route["outAmount"],
                "fee": estimated_fee
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Échec de l'exécution du swap: {e}")
            # Essayer un chemin d'exécution alternatif
            try:
                logger.warning("Tentative d'exécution sur une route alternative...")
                return await self._execute_fallback_swap(input_token, output_token, amount_in, slippage)
            except Exception as fallback_e:
                logger.error(f"Échec également de la route alternative: {fallback_e}")
                raise Exception(f"Impossible d'exécuter le swap: {e}")
                
    async def _select_best_quote(self, routes: List[Dict[str, Any]], amount_in: float) -> Dict[str, Any]:
        """
        Sélectionne la meilleure offre en tenant compte du prix et des frais.
        
        Args:
            routes: Liste des routes disponibles
            amount_in: Montant d'entrée
            
        Returns:
            Meilleure route pour l'échange
        """
        if not routes:
            raise ValueError("Aucune route disponible pour cet échange")
            
        best_route = None
        best_effective_price = 0
        
        for route in routes:
            # Calculer le prix effectif (montant sortant moins frais estimés)
            out_amount = float(route["outAmount"])
            
            # Estimer les frais pour cette route
            try:
                tx_data = await self._build_swap_transaction(route)
                tx = Transaction.deserialize(tx_data["transaction"])
                estimated_fee = await self.get_fee_for_message(tx)
                
                # Convertir les frais dans la même unité que le montant sortant
                # (ceci est une simplification, nécessiterait normalement une conversion de devise)
                fee_adjustment = estimated_fee / 1_000_000  # Ajustement approximatif
                
                effective_price = out_amount - fee_adjustment
                
                if best_route is None or effective_price > best_effective_price:
                    best_route = route
                    best_effective_price = effective_price
                    
            except Exception as e:
                logger.warning(f"Erreur lors de l'évaluation de la route {route.get('market', 'inconnue')}: {e}")
                # Continuer avec la route suivante
                continue
                
        if best_route is None:
            raise ValueError("Impossible de trouver une route viable pour cet échange")
            
        return best_route
        
    async def _get_swap_routes(self, input_token: str, output_token: str, amount_in: float) -> List[Dict[str, Any]]:
        """Obtient les routes possibles pour un swap."""
        # Implémentation pour obtenir les routes de swap
        pass
        
    async def _build_swap_transaction(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """Construit une transaction de swap basée sur la route sélectionnée."""
        # Implémentation pour construire une transaction
        pass
        
    async def _execute_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """Exécute une transaction Solana."""
        # Implémentation pour exécuter une transaction
        pass
        
    async def _execute_fallback_swap(self, input_token: str, output_token: str, 
                                   amount_in: float, slippage: float) -> Dict[str, Any]:
        """Exécute un swap via un chemin alternatif si la méthode principale échoue."""
        # Implémentation du chemin alternatif
        pass
        
    def _record_transaction(self, result: Dict[str, Any], details: Dict[str, Any]) -> None:
        """Enregistre les détails d'une transaction dans l'historique."""
        transaction_record = {
            "signature": result.get("signature"),
            "timestamp": time.time(),
            "success": result.get("success", False),
            "details": details
        }
        
        self.transaction_history.append(transaction_record)
        self.last_transaction_signature = result.get("signature")

import logging
import time
import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union, Set, Callable
import json
import os
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

from app.strategy_framework import Strategy, Signal, SignalType
from market.market_data import MarketDataProvider
from app.risk_manager import RiskManager, Position

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("trading_engine")

class OrderType(Enum):
    """Types d'ordres disponibles."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"

class OrderSide(Enum):
    """Côtés des ordres."""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """États des ordres."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class Order:
    """Représentation d'un ordre."""
    id: str
    token_address: str
    token_symbol: str
    side: OrderSide
    type: OrderType
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0
    average_fill_price: Optional[float] = None
    created_at: float = None
    updated_at: float = None
    strategy_name: Optional[str] = None
    exchange: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()
        if self.metadata is None:
            self.metadata = {}
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class ExecutionResult:
    """Résultat de l'exécution d'un ordre."""
    success: bool
    order: Order
    message: str
    transaction_id: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class ExchangeAdapter:
    """
    Classe de base pour l'adaptation aux différentes API d'échange.
    Cette classe doit être étendue pour chaque plateforme d'échange spécifique.
    """
    def __init__(self, api_key: str, api_secret: str, exchange_name: str):
        """
        Initialise l'adaptateur d'échange.
        
        Args:
            api_key: Clé API
            api_secret: Secret API
            exchange_name: Nom de l'échange
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange_name = exchange_name
        self.last_api_call = 0
        self.rate_limit_wait = 0.2  # Temps d'attente entre les appels API en secondes
    
    async def create_order(self, order: Order) -> ExecutionResult:
        """
        Crée un ordre sur l'échange.
        
        Args:
            order: Ordre à créer
            
        Returns:
            Résultat de l'exécution
        """
        # Implémentation spécifique à l'échange à fournir dans les sous-classes
        raise NotImplementedError("Cette méthode doit être implémentée dans une sous-classe")
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Annule un ordre existant.
        
        Args:
            order_id: ID de l'ordre à annuler
            
        Returns:
            True si l'annulation a réussi
        """
        # Implémentation spécifique à l'échange à fournir dans les sous-classes
        raise NotImplementedError("Cette méthode doit être implémentée dans une sous-classe")
    
    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """
        Récupère le statut d'un ordre.
        
        Args:
            order_id: ID de l'ordre
            
        Returns:
            Statut de l'ordre ou None si non trouvé
        """
        # Implémentation spécifique à l'échange à fournir dans les sous-classes
        raise NotImplementedError("Cette méthode doit être implémentée dans une sous-classe")
    
    async def get_account_balances(self) -> Dict[str, float]:
        """
        Récupère les soldes du compte.
        
        Returns:
            Dictionnaire des soldes par devise
        """
        # Implémentation spécifique à l'échange à fournir dans les sous-classes
        raise NotImplementedError("Cette méthode doit être implémentée dans une sous-classe")
    
    async def get_token_price(self, token_address: str, reference: str = "USDC") -> float:
        """
        Récupère le prix actuel d'un token.
        
        Args:
            token_address: Adresse du token
            reference: Token de référence pour le prix
            
        Returns:
            Prix actuel
        """
        # Implémentation spécifique à l'échange à fournir dans les sous-classes
        raise NotImplementedError("Cette méthode doit être implémentée dans une sous-classe")
    
    async def _api_call(self, endpoint: str, method: str = "GET", params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Effectue un appel API avec gestion de la limite de taux.
        
        Args:
            endpoint: Point de terminaison API
            method: Méthode HTTP
            params: Paramètres de la requête
            
        Returns:
            Réponse de l'API
        """
        # Respecter les limites de taux
        time_since_last_call = time.time() - self.last_api_call
        if time_since_last_call < self.rate_limit_wait:
            await asyncio.sleep(self.rate_limit_wait - time_since_last_call)
        
        # Effectuer l'appel API
        self.last_api_call = time.time()
        
        # Cette méthode doit être implémentée dans les sous-classes spécifiques à chaque échange
        raise NotImplementedError("Cette méthode doit être implémentée dans une sous-classe")

class MockExchangeAdapter(ExchangeAdapter):
    """Adaptateur d'échange simulé pour les tests et la démonstration."""
    
    def __init__(self, initial_balances: Dict[str, float] = None):
        """
        Initialise l'adaptateur d'échange simulé.
        
        Args:
            initial_balances: Soldes initiaux du compte
        """
        super().__init__("mock_key", "mock_secret", "MockExchange")
        self.balances = initial_balances or {"USDC": 10000.0, "SOL": 100.0, "BTC": 0.5}
        self.orders: Dict[str, Order] = {}
        self.last_prices: Dict[str, float] = {
            "SOL": 100.0,
            "BTC": 29000.0,
            "ETH": 1800.0
        }
        self.price_volatility = 0.01  # 1% de volatilité pour la simulation
    
    async def create_order(self, order: Order) -> ExecutionResult:
        """
        Simule la création d'un ordre.
        
        Args:
            order: Ordre à créer
            
        Returns:
            Résultat de l'exécution
        """
        # Simuler un délai réseau
        await asyncio.sleep(0.1)
        
        # Vérifier les soldes
        if order.side == OrderSide.BUY:
            quote_currency = "USDC"  # Pour simplifier, on suppose toujours USDC comme devise de référence
            order_cost = order.price * order.amount if order.price else await self._get_market_price(order.token_symbol) * order.amount
            
            if self.balances.get(quote_currency, 0) < order_cost:
                return ExecutionResult(
                    success=False,
                    order=order,
                    message=f"Solde insuffisant en {quote_currency}"
                )
        else:  # SELL
            if self.balances.get(order.token_symbol, 0) < order.amount:
                return ExecutionResult(
                    success=False,
                    order=order,
                    message=f"Solde insuffisant en {order.token_symbol}"
                )
        
        # Simuler différents types d'ordres
        if order.type == OrderType.MARKET:
            # Les ordres au marché sont exécutés immédiatement
            price = await self._get_market_price(order.token_symbol)
            order.price = price
            order.status = OrderStatus.FILLED
            order.filled_amount = order.amount
            order.average_fill_price = price
            
            # Mettre à jour les soldes
            self._update_balances(order)
            
        elif order.type == OrderType.LIMIT:
            # Les ordres limites sont placés dans le carnet d'ordres
            order.status = OrderStatus.OPEN
            
        self.orders[order.id] = order
        order.updated_at = time.time()
        
        return ExecutionResult(
            success=True,
            order=order,
            message="Ordre créé avec succès",
            transaction_id=f"mock_tx_{int(time.time())}"
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Simule l'annulation d'un ordre.
        
        Args:
            order_id: ID de l'ordre à annuler
            
        Returns:
            True si l'annulation a réussi
        """
        await asyncio.sleep(0.1)  # Simuler un délai réseau
        
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                order.status = OrderStatus.CANCELLED
                order.updated_at = time.time()
                return True
        
        return False
    
    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """
        Récupère le statut d'un ordre simulé.
        
        Args:
            order_id: ID de l'ordre
            
        Returns:
            Statut de l'ordre ou None si non trouvé
        """
        await asyncio.sleep(0.05)  # Simuler un délai réseau
        
        if order_id in self.orders:
            return self.orders[order_id].status
        
        return None
    
    async def get_account_balances(self) -> Dict[str, float]:
        """
        Récupère les soldes simulés du compte.
        
        Returns:
            Dictionnaire des soldes
        """
        await asyncio.sleep(0.1)  # Simuler un délai réseau
        return self.balances.copy()
    
    async def get_token_price(self, token_address: str, reference: str = "USDC") -> float:
        """
        Récupère un prix simulé pour un token.
        
        Args:
            token_address: Adresse du token
            reference: Token de référence pour le prix
            
        Returns:
            Prix simulé
        """
        # Pour la simplicité, on utilise le symbole directement
        symbol = token_address.split("_")[-1] if "_" in token_address else token_address
        return await self._get_market_price(symbol)
    
    async def _get_market_price(self, symbol: str) -> float:
        """
        Génère un prix de marché simulé avec volatilité.
        
        Args:
            symbol: Symbole du token
            
        Returns:
            Prix simulé
        """
        if symbol not in self.last_prices:
            self.last_prices[symbol] = 10.0  # Prix par défaut pour les nouveaux tokens
            
        # Simuler un mouvement de prix
        price_change = np.random.normal(0, self.price_volatility)
        new_price = self.last_prices[symbol] * (1 + price_change)
        self.last_prices[symbol] = new_price
        
        return new_price
    
    def _update_balances(self, order: Order) -> None:
        """
        Met à jour les soldes après l'exécution d'un ordre.
        
        Args:
            order: Ordre exécuté
        """
        if order.status != OrderStatus.FILLED:
            return
        
        if order.side == OrderSide.BUY:
            quote_currency = "USDC"  # Pour simplifier
            cost = order.average_fill_price * order.filled_amount
            
            # Déduire le coût de la devise de référence
            self.balances[quote_currency] = self.balances.get(quote_currency, 0) - cost
            
            # Ajouter les tokens achetés
            self.balances[order.token_symbol] = self.balances.get(order.token_symbol, 0) + order.filled_amount
            
        else:  # SELL
            proceeds = order.average_fill_price * order.filled_amount
            quote_currency = "USDC"  # Pour simplifier
            
            # Déduire les tokens vendus
            self.balances[order.token_symbol] = self.balances.get(order.token_symbol, 0) - order.filled_amount
            
            # Ajouter le produit de la vente
            self.balances[quote_currency] = self.balances.get(quote_currency, 0) + proceeds
    
    async def process_open_orders(self) -> None:
        """
        Simule le traitement des ordres ouverts.
        Certains ordres peuvent être exécutés en fonction des mouvements de prix simulés.
        """
        for order_id, order in list(self.orders.items()):
            if order.status != OrderStatus.OPEN:
                continue
                
            current_price = await self._get_market_price(order.token_symbol)
            
            # Simuler l'exécution des ordres limites lorsque le prix est favorable
            if order.type == OrderType.LIMIT:
                if (order.side == OrderSide.BUY and current_price <= order.price) or \
                   (order.side == OrderSide.SELL and current_price >= order.price):
                    
                    order.status = OrderStatus.FILLED
                    order.filled_amount = order.amount
                    order.average_fill_price = order.price
                    order.updated_at = time.time()
                    
                    # Mettre à jour les soldes
                    self._update_balances(order)
                    logger.info(f"Ordre simulé exécuté: {order_id}, prix: {order.price}, montant: {order.amount}")

class TradingEngine:
    """
    Moteur d'exécution de trading qui reçoit les signaux des stratégies,
    gère les positions et exécute les ordres sur les plateformes d'échange.
    """
    
    def __init__(self, 
                 exchange_adapter: ExchangeAdapter, 
                 risk_manager: Optional[RiskManager] = None,
                 data_provider: Optional[MarketDataProvider] = None,
                 config_path: Optional[str] = None):
        """
        Initialise le moteur de trading.
        
        Args:
            exchange_adapter: Adaptateur pour l'échange
            risk_manager: Gestionnaire de risque (optionnel)
            data_provider: Fournisseur de données de marché (optionnel)
            config_path: Chemin vers un fichier de configuration (optionnel)
        """
        self.exchange = exchange_adapter
        self.risk_manager = risk_manager or RiskManager()
        self.data_provider = data_provider
        
        self.strategies: Dict[str, Strategy] = {}
        self.active_positions: Dict[str, Position] = {}  # Par token_address
        self.pending_orders: Dict[str, Order] = {}  # Par order_id
        self.executed_trades: List[Dict[str, Any]] = []
        
        # Configuration par défaut
        self.config = {
            "signal_confidence_threshold": 0.6,
            "max_open_positions": 10,
            "signal_expiry_seconds": 300,  # 5 minutes
            "price_check_interval": 30,  # 30 secondes
            "order_update_interval": 15,  # 15 secondes
            "execute_market_orders": True,
            "auto_close_positions": True
        }
        
        # Charger la configuration si disponible
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
            
        self.running = False
        self.tasks = []
        
        logger.info(f"Moteur de trading initialisé avec l'échange {exchange_adapter.exchange_name}")
    
    def _load_config(self, config_path: str) -> None:
        """
        Charge la configuration depuis un fichier JSON.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
            logger.info(f"Configuration chargée depuis {config_path}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
    
    def register_strategy(self, strategy: Strategy) -> None:
        """
        Enregistre une stratégie auprès du moteur de trading.
        
        Args:
            strategy: Stratégie à enregistrer
        """
        self.strategies[strategy.name] = strategy
        logger.info(f"Stratégie enregistrée: {strategy.name}")
    
    async def start(self) -> None:
        """Démarre le moteur de trading."""
        if self.running:
            logger.warning("Le moteur de trading est déjà en cours d'exécution")
            return
            
        self.running = True
        logger.info("Démarrage du moteur de trading...")
        
        # Récupérer les soldes initiaux
        balances = await self.exchange.get_account_balances()
        logger.info(f"Soldes du compte: {balances}")
        
        # Mettre à jour la valeur du portefeuille dans le gestionnaire de risque
        total_value = 0
        for token, amount in balances.items():
            if token != "USDC":  # Pour les tokens non-USDC, obtenir la valeur en USDC
                try:
                    price = await self.exchange.get_token_price(token)
                    total_value += amount * price
                except Exception as e:
                    logger.error(f"Erreur lors de l'obtention du prix pour {token}: {e}")
            else:
                total_value += amount
                
        self.risk_manager.update_portfolio_value(total_value)
        logger.info(f"Valeur initiale du portefeuille: ${total_value:.2f}")
        
        # Démarrer les tâches périodiques
        self.tasks = [
            asyncio.create_task(self._process_orders_loop()),
            asyncio.create_task(self._update_positions_loop())
        ]
        
        logger.info("Moteur de trading démarré")
        
    async def stop(self) -> None:
        """Arrête le moteur de trading."""
        if not self.running:
            return
            
        self.running = False
        logger.info("Arrêt du moteur de trading...")
        
        # Annuler toutes les tâches
        for task in self.tasks:
            task.cancel()
            
        try:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass
            
        logger.info("Moteur de trading arrêté")
    
    async def process_signal(self, signal: Signal) -> Optional[str]:
        """
        Traite un signal généré par une stratégie.
        
        Args:
            signal: Signal à traiter
            
        Returns:
            ID de l'ordre créé ou None
        """
        if not self.running:
            logger.warning("Le moteur de trading n'est pas en cours d'exécution")
            return None
            
        # Vérifier si le signal est assez récent
        signal_age = time.time() - signal.timestamp
        if signal_age > self.config["signal_expiry_seconds"]:
            logger.warning(f"Signal expiré ignoré: {signal.type.value} pour {signal.token_address} (âge: {signal_age:.1f}s)")
            return None
            
        # Vérifier si le signal est suffisamment confiant
        if signal.confidence < self.config["signal_confidence_threshold"]:
            logger.info(f"Signal ignoré en raison d'une confiance insuffisante: {signal.confidence:.2f}")
            return None
            
        # Vérifier si nous avons déjà une position pour ce token
        has_position = signal.token_address in self.active_positions
        
        # Pour les signaux d'achat, vérifier si nous avons atteint le nombre maximum de positions
        if (signal.type in (SignalType.BUY, SignalType.STRONG_BUY) and 
            len(self.active_positions) >= self.config["max_open_positions"] and 
            not has_position):
            logger.warning(f"Signal d'achat ignoré, nombre maximum de positions atteint: {len(self.active_positions)}")
            return None
            
        # Obtenir le prix actuel
        try:
            current_price = await self.exchange.get_token_price(signal.token_address)
        except Exception as e:
            logger.error(f"Impossible d'obtenir le prix actuel pour {signal.token_address}: {e}")
            return None
            
        # Traiter le signal selon son type
        if signal.type in (SignalType.BUY, SignalType.STRONG_BUY) and not has_position:
            return await self._process_buy_signal(signal, current_price)
        elif signal.type in (SignalType.SELL, SignalType.STRONG_SELL) and has_position:
            return await self._process_sell_signal(signal, current_price)
        elif signal.type == SignalType.EXIT and has_position:
            return await self._close_position(signal.token_address, "exit_signal")
        else:
            logger.info(f"Signal ignoré: {signal.type.value} pour {signal.token_address} (a_position={has_position})")
            return None
            
    async def _process_buy_signal(self, signal: Signal, current_price: float) -> Optional[str]:
        """
        Traite un signal d'achat.
        
        Args:
            signal: Signal d'achat
            current_price: Prix actuel
            
        Returns:
            ID de l'ordre créé ou None
        """
        token_address = signal.token_address
        token_symbol = signal.metadata.get("token_symbol", token_address.split("_")[-1] if "_" in token_address else "UNKNOWN")
        
        # Calculer la taille de position optimale
        position_size = self.risk_manager.calculate_position_size(
            token_address=token_address,
            token_symbol=token_symbol,
            entry_price=current_price,
            stop_loss=signal.stop_loss
        )
        
        if position_size <= 0:
            logger.info(f"Position ignorée pour {token_symbol}: taille calculée trop petite ({position_size:.2f})")
            return None
            
        # Calculer la quantité à acheter
        quantity = position_size / current_price
        
        # Si la taille est trop petite, ignorer
        min_order_value = 10  # Valeur minimale en USD
        if position_size < min_order_value:
            logger.info(f"Position ignorée pour {token_symbol}: trop petite ({position_size:.2f} < {min_order_value})")
            return None
            
        # Créer l'ordre
        order_type = OrderType.MARKET if self.config["execute_market_orders"] else OrderType.LIMIT
        
        order = Order(
            id="",  # Sera défini lors de la création
            token_address=token_address,
            token_symbol=token_symbol,
            side=OrderSide.BUY,
            type=order_type,
            amount=quantity,
            price=current_price if order_type == OrderType.LIMIT else None,
            stop_price=None,
            strategy_name=signal.strategy_name,
            metadata={
                "signal_confidence": signal.confidence,
                "signal_timeframe": signal.timeframe,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit
            }
        )
        
        # Exécuter l'ordre
        try:
            execution_result = await self.exchange.create_order(order)
            
            if execution_result.success:
                # Créer une position
                position = Position(
                    token_address=token_address,
                    token_symbol=token_symbol,
                    entry_price=current_price,
                    size=position_size,
                    entry_time=time.time(),
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit
                )
                
                # Ajouter la position
                pos_id = self.risk_manager.add_position(position)
                self.active_positions[token_address] = position
                
                # Ajouter l'ordre en attente
                self.pending_orders[execution_result.order.id] = execution_result.order
                
                logger.info(f"Position d'achat ouverte pour {token_symbol} à {current_price:.6f}: {quantity:.4f} unités (${position_size:.2f})")
                
                return execution_result.order.id
            else:
                logger.error(f"Échec de l'ordre d'achat pour {token_symbol}: {execution_result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'ordre d'achat pour {token_symbol}: {e}")
            return None
            
    async def _process_sell_signal(self, signal: Signal, current_price: float) -> Optional[str]:
        """
        Traite un signal de vente.
        
        Args:
            signal: Signal de vente
            current_price: Prix actuel
            
        Returns:
            ID de l'ordre créé ou None
        """
        token_address = signal.token_address
        position = self.active_positions.get(token_address)
        
        if not position:
            logger.warning(f"Signal de vente ignoré: aucune position active pour {token_address}")
            return None
            
        # Créer l'ordre
        order_type = OrderType.MARKET if self.config["execute_market_orders"] else OrderType.LIMIT
        
        order = Order(
            id="",  # Sera défini lors de la création
            token_address=token_address,
            token_symbol=position.token_symbol,
            side=OrderSide.SELL,
            type=order_type,
            amount=position.size / current_price,  # Convertir la valeur en unités
            price=current_price if order_type == OrderType.LIMIT else None,
            stop_price=None,
            strategy_name=signal.strategy_name,
            metadata={
                "signal_confidence": signal.confidence,
                "signal_timeframe": signal.timeframe,
                "entry_price": position.entry_price,
                "position_duration": time.time() - position.entry_time
            }
        )
        
        # Exécuter l'ordre
        try:
            execution_result = await self.exchange.create_order(order)
            
            if execution_result.success:
                # Calculer le P&L
                pnl = (current_price / position.entry_price - 1) * position.size
                pnl_pct = (current_price / position.entry_price - 1) * 100
                
                # Enregistrer le trade
                self._record_trade(position, current_price, "sell_signal", pnl, pnl_pct)
                
                # Supprimer la position
                del self.active_positions[token_address]
                
                # Ajouter l'ordre en attente
                self.pending_orders[execution_result.order.id] = execution_result.order
                
                logger.info(f"Position fermée pour {position.token_symbol}: P&L ${pnl:.2f} ({pnl_pct:.2f}%)")
                
                return execution_result.order.id
            else:
                logger.error(f"Échec de l'ordre de vente pour {position.token_symbol}: {execution_result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'ordre de vente pour {position.token_symbol}: {e}")
            return None
            
    async def _close_position(self, token_address: str, reason: str) -> Optional[str]:
        """
        Ferme une position existante.
        
        Args:
            token_address: Adresse du token
            reason: Raison de la fermeture
            
        Returns:
            ID de l'ordre créé ou None
        """
        position = self.active_positions.get(token_address)
        
        if not position:
            logger.warning(f"Fermeture de position ignorée: aucune position active pour {token_address}")
            return None
            
        # Obtenir le prix actuel
        try:
            current_price = await self.exchange.get_token_price(token_address)
        except Exception as e:
            logger.error(f"Impossible d'obtenir le prix actuel pour {token_address}: {e}")
            return None
            
        # Créer un ordre de marché pour fermer la position
        order = Order(
            id="",  # Sera défini lors de la création
            token_address=token_address,
            token_symbol=position.token_symbol,
            side=OrderSide.SELL,
            type=OrderType.MARKET,  # Toujours utiliser un ordre au marché pour les fermetures
            amount=position.size / current_price,  # Convertir la valeur en unités
            price=None,
            stop_price=None,
            metadata={
                "close_reason": reason,
                "entry_price": position.entry_price,
                "position_duration": time.time() - position.entry_time
            }
        )
        
        # Exécuter l'ordre
        try:
            execution_result = await self.exchange.create_order(order)
            
            if execution_result.success:
                # Calculer le P&L
                pnl = (current_price / position.entry_price - 1) * position.size
                pnl_pct = (current_price / position.entry_price - 1) * 100
                
                # Enregistrer le trade
                self._record_trade(position, current_price, reason, pnl, pnl_pct)
                
                # Supprimer la position
                del self.active_positions[token_address]
                
                # Ajouter l'ordre en attente
                self.pending_orders[execution_result.order.id] = execution_result.order
                
                logger.info(f"Position fermée pour {position.token_symbol} ({reason}): P&L ${pnl:.2f} ({pnl_pct:.2f}%)")
                
                return execution_result.order.id
            else:
                logger.error(f"Échec de la fermeture de position pour {position.token_symbol}: {execution_result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de position pour {position.token_symbol}: {e}")
            return None
            
    def _record_trade(self, position: Position, exit_price: float, exit_reason: str, 
                    profit_loss: float, profit_pct: float) -> None:
        """
        Enregistre un trade complété dans l'historique.
        
        Args:
            position: Position fermée
            exit_price: Prix de sortie
            exit_reason: Raison de la sortie
            profit_loss: P&L en valeur absolue
            profit_pct: P&L en pourcentage
        """
        trade = {
            "token_address": position.token_address,
            "token_symbol": position.token_symbol,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "size": position.size,
            "entry_time": position.entry_time,
            "exit_time": time.time(),
            "profit_loss": profit_loss,
            "profit_pct": profit_pct,
            "exit_reason": exit_reason
        }
        
        self.executed_trades.append(trade)
        
        # Si le gestionnaire de risque est disponible, mettre à jour les volatilités
        if hasattr(self.risk_manager, 'update_price_history'):
            self.risk_manager.update_price_history(position.token_address, exit_price)
            
    async def _process_orders_loop(self) -> None:
        """Boucle de traitement des ordres en attente."""
        while self.running:
            try:
                # Attendre l'intervalle configuré
                await asyncio.sleep(self.config["order_update_interval"])
                
                # Copie des clés pour éviter la modification pendant l'itération
                order_ids = list(self.pending_orders.keys())
                
                for order_id in order_ids:
                    if order_id not in self.pending_orders:
                        continue
                        
                    order = self.pending_orders[order_id]
                    
                    # Vérifier le statut de l'ordre
                    status = await self.exchange.get_order_status(order_id)
                    
                    if status == OrderStatus.FILLED:
                        logger.info(f"Ordre {order_id} exécuté: {order.token_symbol} {order.side.value.upper()} à {order.price}")
                        
                        # Si c'était un ordre d'achat, il a déjà été enregistré comme position
                        
                        # Supprimer de la liste des ordres en attente
                        del self.pending_orders[order_id]
                        
                    elif status in (OrderStatus.REJECTED, OrderStatus.CANCELLED, OrderStatus.EXPIRED):
                        logger.warning(f"Ordre {order_id} {status.value}: {order.token_symbol} {order.side.value.upper()}")
                        
                        # Si c'était un ordre d'achat et qu'il est rejeté/annulé, supprimer la position
                        if order.side == OrderSide.BUY and order.token_address in self.active_positions:
                            del self.active_positions[order.token_address]
                            logger.info(f"Position {order.token_symbol} supprimée suite à l'échec de l'ordre")
                            
                        # Supprimer de la liste des ordres en attente
                        del self.pending_orders[order_id]
                        
            except asyncio.CancelledError:
                logger.info("Boucle de traitement des ordres arrêtée")
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle de traitement des ordres: {e}")
                
    async def _update_positions_loop(self) -> None:
        """Boucle de mise à jour des positions actives."""
        while self.running:
            try:
                # Attendre l'intervalle configuré
                await asyncio.sleep(self.config["price_check_interval"])
                
                # Copie des clés pour éviter la modification pendant l'itération
                token_addresses = list(self.active_positions.keys())
                
                for token_address in token_addresses:
                    if token_address not in self.active_positions:
                        continue
                        
                    position = self.active_positions[token_address]
                    
                    # Obtenir le prix actuel
                    try:
                        current_price = await self.exchange.get_token_price(token_address)
                    except Exception as e:
                        logger.error(f"Impossible d'obtenir le prix actuel pour {position.token_symbol}: {e}")
                        continue
                        
                    # Mettre à jour la position avec le nouveau prix
                    self.risk_manager.update_position(token_address, current_price)
                    
                    # Si la fermeture automatique est activée, vérifier les conditions de stop-loss et take-profit
                    if self.config["auto_close_positions"]:
                        # Vérifier le stop-loss
                        if position.stop_loss is not None and current_price <= position.stop_loss:
                            logger.warning(f"Stop-loss déclenché pour {position.token_symbol} à {current_price:.6f}")
                            await self._close_position(token_address, "stop_loss")
                            continue
                            
                        # Vérifier le take-profit
                        if position.take_profit is not None and current_price >= position.take_profit:
                            logger.info(f"Take-profit atteint pour {position.token_symbol} à {current_price:.6f}")
                            await self._close_position(token_address, "take_profit")
                            continue
                    
                # Mettre à jour la valeur totale du portefeuille
                await self._update_portfolio_value()
                
            except asyncio.CancelledError:
                logger.info("Boucle de mise à jour des positions arrêtée")
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle de mise à jour des positions: {e}")
                
    async def _update_portfolio_value(self) -> None:
        """Met à jour la valeur totale du portefeuille."""
        try:
            # Obtenir les soldes
            balances = await self.exchange.get_account_balances()
            
            # Calculer la valeur en USD
            total_value = 0
            
            for token, amount in balances.items():
                if token == "USDC" or token == "USDT" or token == "USD":
                    total_value += amount
                else:
                    try:
                        price = await self.exchange.get_token_price(token)
                        total_value += amount * price
                    except Exception as e:
                        logger.error(f"Erreur lors de l'obtention du prix pour {token}: {e}")
                        
            # Mettre à jour la valeur du portefeuille dans le gestionnaire de risque
            self.risk_manager.update_portfolio_value(total_value)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la valeur du portefeuille: {e}")
            
    async def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Obtient le statut du portefeuille actuel.
        
        Returns:
            Statut du portefeuille
        """
        try:
            # Obtenir les métriques de risque
            risk_metrics = await self.risk_manager.calculate_risk_metrics()
            
            # Obtenir les soldes
            balances = await self.exchange.get_account_balances()
            
            # Construire le statut
            status = {
                "timestamp": time.time(),
                "portfolio_value": self.risk_manager.portfolio_value,
                "risk_metrics": {
                    "var_95": risk_metrics.var_95,
                    "max_drawdown": risk_metrics.max_drawdown,
                    "sharpe_ratio": risk_metrics.sharpe_ratio,
                    "current_exposure": risk_metrics.current_exposure
                },
                "balances": balances,
                "active_positions": len(self.active_positions),
                "positions": [],
                "executed_trades_count": len(self.executed_trades),
                "recent_trades": self.executed_trades[-10:] if self.executed_trades else []
            }
            
            # Ajouter les détails des positions
            for token_address, position in self.active_positions.items():
                try:
                    current_price = await self.exchange.get_token_price(token_address)
                    
                    # Calculer le P&L non réalisé
                    unrealized_pnl = (current_price / position.entry_price - 1) * position.size
                    unrealized_pnl_pct = (current_price / position.entry_price - 1) * 100
                    
                    status["positions"].append({
                        "token_address": token_address,
                        "token_symbol": position.token_symbol,
                        "entry_price": position.entry_price,
                        "current_price": current_price,
                        "size": position.size,
                        "unrealized_pnl": unrealized_pnl,
                        "unrealized_pnl_pct": unrealized_pnl_pct,
                        "entry_time": position.entry_time,
                        "duration_hours": (time.time() - position.entry_time) / 3600,
                        "stop_loss": position.stop_loss,
                        "take_profit": position.take_profit
                    })
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'obtention des détails de la position {token_address}: {e}")
            
            return status
            
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention du statut du portefeuille: {e}")
            return {
                "timestamp": time.time(),
                "error": str(e)
            }
