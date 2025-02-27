import re
import logging
import time
import asyncio
import json
from typing import Dict, Any, Optional, List, Union, Tuple, Set
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import aiohttp
import sqlite3
from dataclasses import dataclass
import numpy as np
from market.market_data import MarketDataProvider

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("security")

# Regex pour valider les adresses Solana (format Base58)
SOLANA_ADDRESS_PATTERN = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

@dataclass
class SecurityRisk:
    """Classe pour représenter un risque de sécurité détecté."""
    risk_type: str
    severity: int  # 1-10, 10 étant le plus sévère
    description: str
    metadata: Dict[str, Any]

class SecurityChecker:
    """Classe pour vérifier la sécurité des tokens et des transactions."""
    
    def __init__(self, db_path: str, market_data_provider: Optional[MarketDataProvider] = None):
        """
        Initialise le vérificateur de sécurité.
        
        Args:
            db_path: Chemin vers la base de données SQLite
            market_data_provider: Fournisseur de données de marché (optionnel)
        """
        self.db_path = db_path
        self.market_data = market_data_provider
        self.conn = self._initialize_database()
        self.blacklist = self._load_blacklist()
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.request_timestamps: Dict[str, List[float]] = {}  # Pour la protection contre les taux limites
        
    def _initialize_database(self) -> sqlite3.Connection:
        """Initialise la connexion à la base de données et crée les tables si nécessaire."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Créer la table de blacklist si elle n'existe pas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    address TEXT PRIMARY KEY,
                    reason TEXT,
                    severity INTEGER,
                    timestamp REAL,
                    metadata TEXT
                )
            ''')
            
            # Créer la table des incidents de sécurité
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT,
                    incident_type TEXT,
                    severity INTEGER,
                    timestamp REAL,
                    details TEXT
                )
            ''')
            
            conn.commit()
            return conn
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            raise
            
    def _load_blacklist(self) -> Set[str]:
        """Charge la liste noire de la base de données."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT address FROM blacklist")
            return set(row[0] for row in cursor.fetchall())
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la liste noire: {e}")
            return set()
            
    def _load_suspicious_patterns(self) -> List[Dict[str, Any]]:
        """Charge les modèles suspects pour la détection des arnaques."""
        # Ces modèles pourraientt être chargés d'un fichier de config, ici on les définit en dur
        return [
            {
                "name": "high_token_allocation",
                "description": "Plus de 50% des tokens sont détenus par une seule adresse non vérifiée",
                "severity": 8,
                "indicators": {
                    "holder_percentage_threshold": 0.5,
                    "exclude_verified_contracts": True
                }
            },
            {
                "name": "rapid_liquidity_removal",
                "description": "Retrait de liquidité rapide (> 30% en moins d'une heure)",
                "severity": 9,
                "indicators": {
                    "liquidity_change_threshold": -0.3,
                    "time_window_seconds": 3600
                }
            },
            {
                "name": "honeypot_contract",
                "description": "Contrat avec restrictions de vente (honeypot)",
                "severity": 10,
                "indicators": {
                    "sell_function_disabled": True,
                    "high_sell_tax": 0.5
                }
            },
            {
                "name": "asymmetric_liquidity",
                "description": "Liquidité asymétrique dans le pool (déséquilibre > 80%)",
                "severity": 7,
                "indicators": {
                    "asymmetry_threshold": 0.8
                }
            },
            {
                "name": "suspicious_transaction_pattern",
                "description": "Schéma de transactions suspect (wash trading)",
                "severity": 6,
                "indicators": {
                    "circular_transfers": True,
                    "unusual_frequency": 0.9  # 90% plus fréquent que la normale
                }
            }
        ]

    def validate_solana_address(self, address: str) -> bool:
        """
        Valide le format d'une adresse Solana.
        
        Args:
            address: Adresse Solana à valider
            
        Returns:
            True si l'adresse est valide, False sinon
        """
        if not isinstance(address, str):
            return False
        return bool(SOLANA_ADDRESS_PATTERN.match(address))
    
    async def check_token_security(self, token_address: str) -> Tuple[bool, List[SecurityRisk]]:
        """
        Vérifie la sécurité d'un token avec plusieurs couches d'analyse.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Tuple (sécurité_validée, liste_risques)
        """
        # Valider le format de l'adresse
        if not self.validate_solana_address(token_address):
            return False, [SecurityRisk(
                risk_type="invalid_address",
                severity=10,
                description=f"Format d'adresse Solana invalide: {token_address}",
                metadata={"address": token_address}
            )]
            
        # Vérifier si le token est sur la liste noire
        if token_address in self.blacklist:
            return False, [SecurityRisk(
                risk_type="blacklisted",
                severity=10,
                description="Token présent dans la liste noire",
                metadata={"address": token_address}
            )]
            
        # Collecte des risques détectés
        risks = []
        
        # Exécuter toutes les vérifications de sécurité
        try:
            # 1. Vérifier l'âge et l'historique du token
            age_risks = await self._check_token_age_and_history(token_address)
            risks.extend(age_risks)
            
            # 2. Analyser la distribution des détenteurs
            holder_risks = await self._analyze_holder_distribution(token_address)
            risks.extend(holder_risks)
            
            # 3. Vérifier les métriques on-chain
            metrics_risks = await self._get_onchain_metrics(token_address)
            risks.extend(metrics_risks)
            
            # 4. Détection avancée de modèles de rug pull
            rugpull_risks = await self._detect_rugpull_patterns(token_address)
            risks.extend(rugpull_risks)
            
            # 5. Analyse de la profondeur de liquidité
            liquidity_risks = await self._analyze_liquidity_depth(token_address)
            risks.extend(liquidity_risks)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de sécurité pour {token_address}: {e}")
            # Ajouter un risque pour l'échec de vérification
            risks.append(SecurityRisk(
                risk_type="verification_failure",
                severity=5,
                description=f"Échec de la vérification complète: {str(e)}",
                metadata={"address": token_address, "error": str(e)}
            ))
            
        # Déterminer si le token est sûr en fonction des risques
        is_safe = all(risk.severity < 7 for risk in risks)
        
        # Si des risques graves sont détectés, ajouter à la liste noire
        if not is_safe:
            severe_risks = [risk for risk in risks if risk.severity >= 8]
            if severe_risks:
                self._add_to_blacklist(token_address, severe_risks)
                
        return is_safe, risks
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=30),
           retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
    async def _check_token_age_and_history(self, token_address: str) -> List[SecurityRisk]:
        """
        Vérifie l'âge et l'historique du token.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        try:
            if self.market_data:
                token_info = await self.market_data.get_token_info(token_address)
                
                # Vérifier l'âge du token
                if "created_at" in token_info:
                    token_age_days = (time.time() - token_info["created_at"]) / (60 * 60 * 24)
                    if token_age_days < 1:
                        risks.append(SecurityRisk(
                            risk_type="new_token",
                            severity=7,
                            description=f"Token créé il y a moins de 24 heures ({token_age_days:.1f} heures)",
                            metadata={"age_days": token_age_days, "created_at": token_info["created_at"]}
                        ))
                    elif token_age_days < 7:
                        risks.append(SecurityRisk(
                            risk_type="new_token",
                            severity=4,
                            description=f"Token créé il y a moins d'une semaine ({token_age_days:.1f} jours)",
                            metadata={"age_days": token_age_days, "created_at": token_info["created_at"]}
                        ))
            
            # Autres vérifications historiques...
            
            return risks
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'âge du token {token_address}: {e}")
            # Gestion d'erreur améliorée - distinguer les différents types d'erreurs
            if isinstance(e, aiohttp.ClientResponseError):
                if e.status == 429:
                    logger.warning(f"Limite de taux dépassée lors de la vérification du token {token_address}")
                    raise  # Permet au décorateur retry de réessayer
                elif e.status >= 500:
                    logger.warning(f"Erreur serveur lors de la vérification du token {token_address}: {e}")
                    # Pour les erreurs serveur, on renvoie un risque mais on permet aussi le retry
                    risks.append(SecurityRisk(
                        risk_type="api_error",
                        severity=3,
                        description="Erreur API temporaire lors de la vérification du token",
                        metadata={"error": str(e), "status": e.status}
                    ))
                    raise
            
            # Pour les autres types d'erreurs, on ajoute simplement un risque
            risks.append(SecurityRisk(
                risk_type="verification_error",
                severity=4,
                description="Impossible de vérifier l'âge et l'historique du token",
                metadata={"error": str(e)}
            ))
            return risks

    async def _analyze_holder_distribution(self, token_address: str) -> List[SecurityRisk]:
        """
        Analyse la distribution des détenteurs du token.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        try:
            # Obtenir les données sur les détenteurs
            # Cette fonctionnalité nécessiterait d'appeler une API externe pour obtenir les détenteurs
            # Exemple d'implémentation simulée
            holder_data = await self._get_token_holders(token_address)
            
            if not holder_data or "holders" not in holder_data:
                return [SecurityRisk(
                    risk_type="holder_data_unavailable",
                    severity=3,
                    description="Données sur les détenteurs non disponibles",
                    metadata={"address": token_address}
                )]
                
            holders = holder_data["holders"]
            
            # Calculer la concentration de possession
            if holders:
                # Calculer le pourcentage détenu par le plus grand détenteur (non vérifié)
                non_verified_holders = [h for h in holders if not h.get("is_verified", False)]
                if non_verified_holders:
                    largest_holder = max(non_verified_holders, key=lambda h: h.get("percentage", 0))
                    largest_percentage = largest_holder.get("percentage", 0)
                    
                    if largest_percentage > 0.5:
                        risks.append(SecurityRisk(
                            risk_type="high_concentration",
                            severity=8,
                            description=f"Un seul détenteur non vérifié possède {largest_percentage*100:.1f}% des tokens",
                            metadata={"holder_address": largest_holder.get("address"), "percentage": largest_percentage}
                        ))
                    elif largest_percentage > 0.3:
                        risks.append(SecurityRisk(
                            risk_type="medium_concentration",
                            severity=5,
                            description=f"Un seul détenteur non vérifié possède {largest_percentage*100:.1f}% des tokens",
                            metadata={"holder_address": largest_holder.get("address"), "percentage": largest_percentage}
                        ))
                
                # Calculer le nombre de détenteurs
                if len(holders) < 10:
                    risks.append(SecurityRisk(
                        risk_type="few_holders",
                        severity=6,
                        description=f"Le token n'a que {len(holders)} détenteurs",
                        metadata={"holder_count": len(holders)}
                    ))
            
            return risks
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des détenteurs pour {token_address}: {e}")
            return [SecurityRisk(
                risk_type="holder_analysis_error",
                severity=4,
                description=f"Erreur lors de l'analyse des détenteurs: {str(e)}",
                metadata={"error": str(e)}
            )]

    async def _get_onchain_metrics(self, token_address: str) -> List[SecurityRisk]:
        """
        Analyse les métriques on-chain du token avec analyse de profondeur de liquidité.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        try:
            if not self.market_data:
                return [SecurityRisk(
                    risk_type="missing_market_data",
                    severity=3,
                    description="Fournisseur de données de marché non disponible",
                    metadata={}
                )]
                
            # Obtenir les données de liquidité
            liquidity_data = await self.market_data.get_liquidity_data(token_address)
            
            # Analyser la liquidité
            if liquidity_data:
                usd_liquidity = liquidity_data.get("liquidity_usd", 0)
                
                # Vérifier le montant de la liquidité
                if usd_liquidity < 1000:
                    risks.append(SecurityRisk(
                        risk_type="very_low_liquidity",
                        severity=9,
                        description=f"Très faible liquidité: ${usd_liquidity:.2f}",
                        metadata={"liquidity_usd": usd_liquidity}
                    ))
                elif usd_liquidity < 10000:
                    risks.append(SecurityRisk(
                        risk_type="low_liquidity",
                        severity=6,
                        description=f"Faible liquidité: ${usd_liquidity:.2f}",
                        metadata={"liquidity_usd": usd_liquidity}
                    ))
                    
                # NOUVELLE FONCTIONNALITÉ: Analyse de la profondeur de liquidité
                if "depth" in liquidity_data:
                    depth = liquidity_data["depth"]
                    
                    # Calculer l'impact de prix pour un ordre de 1000 USD
                    if "price_impact_1000usd" in depth:
                        impact = depth["price_impact_1000usd"]
                        if impact > 0.1:  # Plus de 10% d'impact
                            risks.append(SecurityRisk(
                                risk_type="high_price_impact",
                                severity=7,
                                description=f"Impact de prix élevé: {impact*100:.1f}% pour un ordre de 1000 USD",
                                metadata={"price_impact": impact}
                            ))
                    
                    # Calculer la variance de profondeur
                    if "buy_depth" in depth and "sell_depth" in depth:
                        buy_depth = depth["buy_depth"]
                        sell_depth = depth["sell_depth"]
                        depth_ratio = min(buy_depth, sell_depth) / max(buy_depth, sell_depth) if max(buy_depth, sell_depth) > 0 else 0
                        
                        if depth_ratio < 0.2:  # Déséquilibre important
                            risks.append(SecurityRisk(
                                risk_type="imbalanced_liquidity",
                                severity=6,
                                description=f"Déséquilibre de liquidité: ratio {depth_ratio:.2f}",
                                metadata={"depth_ratio": depth_ratio, "buy_depth": buy_depth, "sell_depth": sell_depth}
                            ))
            
            return risks
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des métriques on-chain pour {token_address}: {e}")
            return [SecurityRisk(
                risk_type="metrics_analysis_error",
                severity=4,
                description=f"Erreur lors de l'analyse des métriques on-chain: {str(e)}",
                metadata={"error": str(e)}
            )]

    async def _detect_rugpull_patterns(self, token_address: str) -> List[SecurityRisk]:
        """
        Détecte les modèles sophistiqués de rug pull.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        try:
            if not self.market_data:
                return []
                
            # Obtenir l'historique des prix et transactions récentes
            try:
                price_history = await self.market_data.get_historical_prices(token_address, timeframe="15m", limit=96)  # 24h
                transaction_history = await self._get_recent_transactions(token_address)
                liquidity_history = await self._get_liquidity_history(token_address)
            except Exception as data_e:
                logger.warning(f"Impossible d'obtenir l'historique complet pour {token_address}: {data_e}")
                return [SecurityRisk(
                    risk_type="history_data_unavailable",
                    severity=5,
                    description="Données historiques incomplètes pour l'analyse de rug pull",
                    metadata={"error": str(data_e)}
                )]
            
            # Analyser les variations de prix soudaines
            if price_history and len(price_history) > 2:
                # Calculer les variations de prix en pourcentage
                price_changes = []
                for i in range(1, len(price_history)):
                    if price_history[i-1].get("price", 0) > 0:
                        change = (price_history[i].get("price", 0) - price_history[i-1].get("price", 0)) / price_history[i-1].get("price", 0)
                        price_changes.append(change)
                
                # Rechercher des chutes de prix inhabituelles
                if price_changes:
                    max_drop = min(price_changes)
                    if max_drop < -0.5:  # Chute de plus de 50%
                        risks.append(SecurityRisk(
                            risk_type="price_crash",
                            severity=8,
                            description=f"Chute de prix brutale détectée: {max_drop*100:.1f}%",
                            metadata={"max_drop": max_drop}
                        ))
            
            # Analyser les retraits de liquidité
            if liquidity_history and len(liquidity_history) > 1:
                # Calculer les variations de liquidité
                recent_liquidity_changes = []
                for i in range(1, min(12, len(liquidity_history))):  # 3h avec des intervalles de 15min
                    if liquidity_history[i-1].get("liquidity_usd", 0) > 0:
                        change = (liquidity_history[i].get("liquidity_usd", 0) - liquidity_history[i-1].get("liquidity_usd", 0)) / liquidity_history[i-1].get("liquidity_usd", 0)
                        recent_liquidity_changes.append(change)
                
                # Détecter un retrait important de liquidité
                if recent_liquidity_changes:
                    largest_drop = min(recent_liquidity_changes)
                    if largest_drop < -0.3:  # Retrait de plus de 30%
                        risks.append(SecurityRisk(
                            risk_type="liquidity_withdrawal",
                            severity=9,
                            description=f"Retrait important de liquidité détecté: {largest_drop*100:.1f}%",
                            metadata={"liquidity_drop": largest_drop}
                        ))
            
            # Analyser les transactions pour détecter des modèles suspects
            if transaction_history:
                # Exemple: détecter un modèle de "wash trading"
                if self._detect_wash_trading(transaction_history):
                    risks.append(SecurityRisk(
                        risk_type="wash_trading",
                        severity=7,
                        description="Modèle de wash trading détecté",
                        metadata={"transaction_count": len(transaction_history)}
                    ))
                
                # Exemple: détecter des transferts massifs vers des adresses d'échange
                if self._detect_exchange_transfers(transaction_history):
                    risks.append(SecurityRisk(
                        risk_type="exchange_transfers",
                        severity=6,
                        description="Transferts importants vers des adresses d'échange détectés",
                        metadata={"transaction_count": len(transaction_history)}
                    ))
            
            return risks
        except Exception as e:
            logger.error(f"Erreur lors de la détection de modèles de rug pull pour {token_address}: {e}")
            return [SecurityRisk(
                risk_type="rugpull_detection_error",
                severity=4,
                description=f"Erreur lors de la détection de modèles de rug pull: {str(e)}",
                metadata={"error": str(e)}
            )]

    async def _analyze_liquidity_depth(self, token_address: str) -> List[SecurityRisk]:
        """
        Analyse la profondeur de la liquidité pour détecter des manipulations.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        try:
            if not self.market_data:
                return []
                
            # Obtenir les données de profondeur de liquidité
            liquidity_depth = await self.market_data.get_liquidity_data(token_address)
            
            if not liquidity_depth or "depth_levels" not in liquidity_depth:
                return [SecurityRisk(
                    risk_type="depth_data_unavailable",
                    severity=2,
                    description="Données de profondeur de liquidité non disponibles",
                    metadata={"token": token_address}
                )]
            
            depth_levels = liquidity_depth["depth_levels"]
            
            # Analyser les niveaux de profondeur
            if depth_levels:
                # Calculer la différence entre les ordres d'achat et de vente
                buy_orders = [level for level in depth_levels if level["side"] == "buy"]
                sell_orders = [level for level in depth_levels if level["side"] == "sell"]
                
                # Calculer le volume total des ordres
                buy_volume = sum(level["size"] * level["price"] for level in buy_orders)
                sell_volume = sum(level["size"] * level["price"] for level in sell_orders)
                
                # Calculer le ratio d'asymétrie
                total_volume = buy_volume + sell_volume
                if total_volume > 0:
                    asymmetry_ratio = abs(buy_volume - sell_volume) / total_volume
                    
                    if asymmetry_ratio > 0.8:
                        risks.append(SecurityRisk(
                            risk_type="severe_liquidity_asymmetry",
                            severity=8,
                            description=f"Asymétrie sévère de la liquidité: {asymmetry_ratio*100:.1f}%",
                            metadata={"asymmetry_ratio": asymmetry_ratio, "buy_volume": buy_volume, "sell_volume": sell_volume}
                        ))
                    elif asymmetry_ratio > 0.5:
                        risks.append(SecurityRisk(
                            risk_type="moderate_liquidity_asymmetry",
                            severity=5,
                            description=f"Asymétrie modérée de la liquidité: {asymmetry_ratio*100:.1f}%",
                            metadata={"asymmetry_ratio": asymmetry_ratio, "buy_volume": buy_volume, "sell_volume": sell_volume}
                        ))
                
                # Calculer l'impact de prix pour différentes tailles d'ordres
                if sell_orders:
                    # Simuler un achat de 1000 USD
                    price_impact_1k = self._calculate_price_impact(sell_orders, 1000)
                    if price_impact_1k > 0.05:  # Impact de plus de 5%
                        risks.append(SecurityRisk(
                            risk_type="high_price_impact_1k",
                            severity=6,
                            description=f"Impact de prix élevé pour 1000 USD: {price_impact_1k*100:.2f}%",
                            metadata={"price_impact_1k": price_impact_1k}
                        ))
                    
                    # Simuler un achat de 10000 USD
                    price_impact_10k = self._calculate_price_impact(sell_orders, 10000)
                    if price_impact_10k > 0.10:  # Impact de plus de 10%
                        risks.append(SecurityRisk(
                            risk_type="high_price_impact_10k",
                            severity=7,
                            description=f"Impact de prix élevé pour 10000 USD: {price_impact_10k*100:.2f}%",
                            metadata={"price_impact_10k": price_impact_10k}
                        ))
            
            return risks
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la profondeur de liquidité pour {token_address}: {e}")
            return [SecurityRisk(
                risk_type="liquidity_depth_error",
                severity=3,
                description=f"Erreur lors de l'analyse de la profondeur de liquidité: {str(e)}",
                metadata={"error": str(e)}
            )]

    def _calculate_price_impact(self, order_levels: List[Dict[str, Any]], usd_amount: float) -> float:
        """
        Calcule l'impact de prix pour un ordre d'une certaine taille.
        
        Args:
            order_levels: Niveaux d'ordres
            usd_amount: Montant en USD à échanger
            
        Returns:
            Impact de prix en pourcentage
        """
        if not order_levels:
            return 0
        
        # Trier par prix croissant
        sorted_levels = sorted(order_levels, key=lambda x: x["price"])
        
        initial_price = sorted_levels[0]["price"]
        remaining_amount = usd_amount
        avg_price = 0
        total_tokens = 0
        
        for level in sorted_levels:
            price = level["price"]
            size = level["size"]
            level_value = price * size
            
            if level_value >= remaining_amount:
                # Cet ordre peut satisfaire la totalité du montant restant
                tokens_bought = remaining_amount / price
                total_tokens += tokens_bought
                avg_price = ((avg_price * (total_tokens - tokens_bought)) + (remaining_amount)) / total_tokens
                break
            else:
                # Consommer tout ce niveau
                tokens_bought = size
                total_tokens += tokens_bought
                avg_price = ((avg_price * (total_tokens - tokens_bought)) + (level_value)) / total_tokens
                remaining_amount -= level_value
        
        # Si on n'a pas pu consommer tout le montant
        if remaining_amount > 0:
            return 1.0  # Impact maximal
        
        # Calculer l'impact de prix
        price_impact = (avg_price - initial_price) / initial_price
        return price_impact

    def _add_to_blacklist(self, token_address: str, risks: List[SecurityRisk]) -> None:
        """
        Ajoute un token à la liste noire.
        
        Args:
            token_address: Adresse du token à blacklister
            risks: Liste des risques identifiés
        """
        try:
            # Ne rien faire si le token est déjà blacklisté
            if token_address in self.blacklist:
                return
                
            # Préparer les données pour la base de données
            max_severity = max(risk.severity for risk in risks)
            reasons = [f"{risk.risk_type}: {risk.description}" for risk in risks]
            reason_text = "; ".join(reasons)
            metadata = json.dumps({
                "risks": [{"type": risk.risk_type, "severity": risk.severity, "description": risk.description} for risk in risks]
            })
            
            # Ajouter à la liste noire en mémoire
            self.blacklist.add(token_address)
            
            # Ajouter à la base de données
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO blacklist (address, reason, severity, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                (token_address, reason_text, max_severity, time.time(), metadata)
            )
            self.conn.commit()
            
            logger.warning(f"Token {token_address} ajouté à la liste noire. Raison: {reason_text}")
            
            # Enregistrer également dans la table des incidents
            for risk in risks:
                if risk.severity >= 7:  # Enregistrer uniquement les risques élevés
                    cursor.execute(
                        "INSERT INTO security_incidents (token_address, incident_type, severity, timestamp, details) VALUES (?, ?, ?, ?, ?)",
                        (token_address, risk.risk_type, risk.severity, time.time(), json.dumps(risk.metadata))
                    )
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du token {token_address} à la liste noire: {e}")

    async def _get_token_holders(self, token_address: str) -> Dict[str, Any]:
        """
        Récupère la liste des détenteurs d'un token.
        
        Args:
            token_address: Adresse du token
            
        Returns:
            Données des détenteurs
        """
        try:
            if not self.market_data:
                return {"holders": []}
                
            # Utiliser le fournisseur de données de marché pour obtenir les détenteurs
            holders_data = await self.market_data.get_token_holders(token_address)
            return holders_data
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détenteurs pour {token_address}: {e}")
            return {"holders": []}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _get_recent_transactions(self, token_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les transactions récentes impliquant un token.
        
        Args:
            token_address: Adresse du token
            limit: Nombre maximum de transactions à récupérer
            
        Returns:
            Liste des transactions récentes
        """
        try:
            if not self.market_data:
                return []
                
            transactions = await self.market_data.get_token_transactions(token_address, limit=limit)
            return transactions
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des transactions pour {token_address}: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _get_liquidity_history(self, token_address: str, timeframe: str = "15m", limit: int = 96) -> List[Dict[str, Any]]:
        """
        Récupère l'historique de liquidité d'un token.
        
        Args:
            token_address: Adresse du token
            timeframe: Intervalle de temps (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Nombre de points de données
            
        Returns:
            Historique de liquidité
        """
        try:
            if not self.market_data:
                return []
                
            liquidity_history = await self.market_data.get_liquidity_history(token_address, timeframe=timeframe, limit=limit)
            return liquidity_history
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique de liquidité pour {token_address}: {e}")
            raise

    def _detect_wash_trading(self, transactions: List[Dict[str, Any]]) -> bool:
        """
        Détecte les modèles de wash trading dans les transactions.
        
        Args:
            transactions: Liste des transactions à analyser
            
        Returns:
            True si un modèle de wash trading est détecté
        """
        if not transactions or len(transactions) < 10:
            return False
            
        # Analyser les transactions pour détecter des cycles
        # Exemple: A -> B -> C -> A dans une période courte
        
        # Regrouper les transactions par adresse d'expéditeur
        sender_groups = {}
        for tx in transactions:
            sender = tx.get("sender")
            if sender:
                if sender not in sender_groups:
                    sender_groups[sender] = []
                sender_groups[sender].append(tx)
                
        # Rechercher des cycles dans les transactions
        cycles_detected = 0
        for sender, txs in sender_groups.items():
            if len(txs) < 3:
                continue
                
            # Trier par horodatage
            sorted_txs = sorted(txs, key=lambda x: x.get("timestamp", 0))
            
            # Rechercher des cycles dans une fenêtre de temps
            window_size = 3600  # 1 heure
            for i in range(len(sorted_txs) - 2):
                start_time = sorted_txs[i].get("timestamp", 0)
                # Rechercher des transactions formant un cycle dans cette fenêtre
                window_txs = [tx for tx in sorted_txs[i+1:] if tx.get("timestamp", 0) - start_time <= window_size]
                
                # Vérifier si un token revient au même expéditeur dans la fenêtre
                receivers = set(tx.get("recipient") for tx in window_txs)
                if sender in receivers:
                    cycles_detected += 1
                    
        # Seuil pour détecter le wash trading
        return cycles_detected >= 3

    def _detect_exchange_transfers(self, transactions: List[Dict[str, Any]]) -> bool:
        """
        Détecte les transferts vers des adresses d'échange connues.
        
        Args:
            transactions: Liste des transactions à analyser
            
        Returns:
            True si des transferts importants vers des échanges sont détectés
        """
        if not transactions:
            return False
            
        # Liste d'adresses d'échange connues (simplifiée)
        exchange_addresses = {
            "FG4Y3yX4AAchp1HvNZ7LfzFTewF2f6nDoMDCohTFjPEm",  # Exemple fictif d'adresse d'échange
            "BbKY1isRzkgwTm9JGBb6nQznPsJkHhb3Kh1u7Sz6k6BV",  # Exemple fictif d'adresse d'échange
            # Autres adresses d'échange...
        }
        
        # Analyser les transactions pour détecter des transferts vers des échanges
        exchange_transfers = [tx for tx in transactions if tx.get("recipient") in exchange_addresses]
        
        if not exchange_transfers:
            return False
            
        # Calculer le volume total transféré vers des échanges
        total_volume = sum(float(tx.get("amount", 0)) for tx in exchange_transfers)
        
        # Calculer le volume total de toutes les transactions
        all_volume = sum(float(tx.get("amount", 0)) for tx in transactions)
        
        # Si le volume des transferts vers des échanges est significatif
        if all_volume > 0 and total_volume / all_volume > 0.7:  # Plus de 70% du volume
            return True
            
        # Ou si un transfert unique important est détecté
        return any(float(tx.get("amount", 0)) > 0.3 * all_volume for tx in exchange_transfers)

    async def cleanup_blacklist(self, age_threshold_days: int = 30) -> int:
        """
        Nettoie la liste noire des entrées anciennes de faible gravité.
        
        Args:
            age_threshold_days: Âge en jours au-delà duquel une entrée peut être supprimée
            
        Returns:
            Nombre d'entrées supprimées
        """
        try:
            cursor = self.conn.cursor()
            
            # Calculer le timestamp seuil
            threshold_timestamp = time.time() - (age_threshold_days * 24 * 60 * 60)
            
            # Identifier les entrées à supprimer (anciennes et de faible gravité)
            cursor.execute(
                "SELECT address FROM blacklist WHERE timestamp < ? AND severity < 7",
                (threshold_timestamp,)
            )
            to_remove = [row[0] for row in cursor.fetchall()]
            
            # Supprimer de la base de données
            if to_remove:
                cursor.execute(
                    "DELETE FROM blacklist WHERE address IN ({}) AND severity < 7".format(
                        ','.join('?' * len(to_remove))
                    ),
                    to_remove
                )
                self.conn.commit()
                
                # Mettre à jour la liste en mémoire
                self.blacklist = self._load_blacklist()
                
                logger.info(f"Nettoyage de la liste noire: {len(to_remove)} entrées supprimées")
                
            return len(to_remove)
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de la liste noire: {e}")
            return 0

    async def get_security_summary(self) -> Dict[str, Any]:
        """
        Génère un résumé des statistiques de sécurité.
        
        Returns:
            Dictionnaire contenant les statistiques de sécurité
        """
        try:
            cursor = self.conn.cursor()
            
            # Compter les entrées de la liste noire
            cursor.execute("SELECT COUNT(*) FROM blacklist")
            blacklist_count = cursor.fetchone()[0]
            
            # Compter les incidents par type
            cursor.execute("SELECT incident_type, COUNT(*) FROM security_incidents GROUP BY incident_type")
            incidents_by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Compter les incidents au cours des dernières 24 heures
            last_24h = time.time() - (24 * 60 * 60)
            cursor.execute("SELECT COUNT(*) FROM security_incidents WHERE timestamp > ?", (last_24h,))
            recent_incidents = cursor.fetchone()[0]
            
            # Calculer la gravité moyenne des incidents
            cursor.execute("SELECT AVG(severity) FROM security_incidents")
            avg_severity = cursor.fetchone()[0] or 0
            
            return {
                "blacklist_size": blacklist_count,
                "incidents_by_type": incidents_by_type,
                "incidents_24h": recent_incidents,
                "average_severity": round(float(avg_severity), 2),
                "last_updated": time.time()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé de sécurité: {e}")
            return {
                "error": str(e),
                "last_updated": time.time()
            }

    def close(self):
        """Ferme les ressources ouvertes."""
        if hasattr(self, "conn") and self.conn:
            try:
                self.conn.close()
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture de la connexion à la base de données: {e}")