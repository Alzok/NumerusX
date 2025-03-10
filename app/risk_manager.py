import logging
import time
import numpy as np
import pandas as pd
import json
import os
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
import asyncio

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("risk_manager")

@dataclass
class Position:
    """Classe représentant une position de trading."""
    token_address: str
    token_symbol: str
    entry_price: float
    size: float
    entry_time: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    trailing_distance: Optional[float] = None
    id: Optional[str] = None

@dataclass
class RiskMetrics:
    """Métriques de risque du portefeuille."""
    var_95: float  # Value at Risk à 95%
    cvar_95: float  # Conditional Value at Risk à 95%
    max_drawdown: float
    sharpe_ratio: float
    current_exposure: float
    max_position_size: float
    correlation_matrix: Dict[str, Dict[str, float]]
    portfolio_volatility: float

class RiskManager:
    """
    Système sophistiqué de gestion des risques avec limites d'exposition dynamiques,
    critère de Kelly et contrôles de drawdown.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le gestionnaire de risque.
        
        Args:
            config_path: Chemin optionnel vers un fichier de configuration
        """
        self.positions = {}  # Positions actuelles par token_address
        self.portfolio_value = 0.0  # Valeur totale du portefeuille
        self.price_history = {}  # Historique des prix par token
        self.volatility_window = 30  # Jours pour le calcul de la volatilité
        self.correlation_window = 60  # Jours pour le calcul des corrélations
        
        # Limites de risque
        self.max_portfolio_risk = 0.02  # Risque maximum du portefeuille (2%)
        self.max_position_size_pct = 0.20  # Taille maximale d'une position (20%)
        self.target_risk_per_trade = 0.005  # Risque cible par transaction (0.5%)
        self.max_correlated_exposure = 0.30  # Exposition maximale à des actifs corrélés (30%)
        self.circuit_breaker_drawdown = 0.15  # Seuil de drawdown pour le circuit breaker (15%)
        
        self.historical_portfolio_values = []  # Pour le calcul du drawdown
        self.last_portfolio_update = time.time()
        
        # Chargement de la configuration personnalisée si disponible
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> None:
        """
        Charge la configuration des paramètres de risque.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Mise à jour des paramètres de risque
            if 'max_portfolio_risk' in config:
                self.max_portfolio_risk = float(config['max_portfolio_risk'])
            if 'max_position_size_pct' in config:
                self.max_position_size_pct = float(config['max_position_size_pct'])
            if 'target_risk_per_trade' in config:
                self.target_risk_per_trade = float(config['target_risk_per_trade'])
            if 'max_correlated_exposure' in config:
                self.max_correlated_exposure = float(config['max_correlated_exposure'])
            if 'circuit_breaker_drawdown' in config:
                self.circuit_breaker_drawdown = float(config['circuit_breaker_drawdown'])
            if 'volatility_window' in config:
                self.volatility_window = int(config['volatility_window'])
            if 'correlation_window' in config:
                self.correlation_window = int(config['correlation_window'])
                
            logger.info(f"Configuration du risque chargée depuis {config_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
    
    def update_portfolio_value(self, new_value: float) -> None:
        """
        Met à jour la valeur du portefeuille et calcule le drawdown.
        
        Args:
            new_value: Nouvelle valeur du portefeuille
        """
        self.portfolio_value = new_value
        self.historical_portfolio_values.append((time.time(), new_value))
        self.last_portfolio_update = time.time()
        
        # Limiter la taille de l'historique (garder les 1000 dernières entrées)
        if len(self.historical_portfolio_values) > 1000:
            self.historical_portfolio_values = self.historical_portfolio_values[-1000:]
            
        # Vérifier le circuit breaker si suffisamment de données
        if len(self.historical_portfolio_values) > 10:
            self._check_circuit_breaker()
    
    def _check_circuit_breaker(self) -> None:
        """
        Vérifie si le drawdown dépasse le seuil de circuit breaker.
        Déclenche des alertes ou des actions d'arrêt d'urgence si nécessaire.
        """
        max_value = max(value for _, value in self.historical_portfolio_values)
        current_value = self.historical_portfolio_values[-1][1]
        
        # Calcul du drawdown
        drawdown = (max_value - current_value) / max_value if max_value > 0 else 0
        
        if drawdown >= self.circuit_breaker_drawdown:
            logger.warning(f"CIRCUIT BREAKER ACTIF! Drawdown: {drawdown*100:.2f}% dépasse le seuil de {self.circuit_breaker_drawdown*100:.2f}%")
            self._trigger_emergency_stop(drawdown)
    
    def _trigger_emergency_stop(self, drawdown: float) -> None:
        """
        Déclenche une procédure d'arrêt d'urgence en cas de drawdown excessif.
        
        Args:
            drawdown: Niveau actuel de drawdown
        """
        logger.critical(f"ARRÊT D'URGENCE: Drawdown {drawdown*100:.2f}% - Fermeture de positions risquées")
        # Cette fonction pourrait fermer automatiquement les positions les plus risquées
        # ou suspendre complètement le trading jusqu'à une intervention manuelle
    
    def calculate_position_size(self, token_address: str, token_symbol: str, 
                                entry_price: float, stop_loss: Optional[float] = None) -> float:
        """
        Calcule la taille optimale d'une position en utilisant le critère de Kelly.
        
        Args:
            token_address: Adresse du token
            token_symbol: Symbole du token
            entry_price: Prix d'entrée
            stop_loss: Prix de stop-loss (optionnel)
            
        Returns:
            Taille de position recommandée en unités monétaires
        """
        # Obtenir l'historique des performances de ce token
        win_rate, avg_win_pct, avg_loss_pct = self._get_token_performance_metrics(token_address)
        
        # Si nous n'avons pas d'historique, utiliser une approche basée sur la volatilité
        if win_rate is None:
            volatility = self._get_token_volatility(token_address) or 0.03  # Valeur par défaut
            return self._calculate_volatility_based_position_size(volatility)
            
        # Calculer la taille de position selon Kelly
        # Formule: f* = (win_rate * avg_win_pct - (1 - win_rate) * avg_loss_pct) / avg_win_pct
        numerator = (win_rate * avg_win_pct - (1 - win_rate) * avg_loss_pct)
        
        # Si la formule donne un résultat négatif, cela signifie que l'espérance est négative
        if numerator <= 0:
            logger.warning(f"Critère de Kelly négatif pour {token_symbol} - espérance mathématique négative")
            return 0
            
        kelly_fraction = numerator / avg_win_pct
        
        # Appliquer une fraction du Kelly pour être plus conservateur (half-Kelly)
        conservative_fraction = kelly_fraction * 0.5  # Utiliser la moitié du Kelly
        
        # Calculer la taille monétaire
        position_size = self.portfolio_value * min(conservative_fraction, self.max_position_size_pct)
        
        # Si un stop-loss est fourni, ajuster la taille pour respecter le risque par trade
        if stop_loss and entry_price > 0:
            risk_per_unit = abs(entry_price - stop_loss) / entry_price
            if risk_per_unit > 0:
                max_risk_amount = self.portfolio_value * self.target_risk_per_trade
                alternative_size = max_risk_amount / risk_per_unit
                position_size = min(position_size, alternative_size)
                
        logger.info(f"Taille de position calculée pour {token_symbol}: ${position_size:.2f} (Kelly: {kelly_fraction:.4f})")
        
        # Vérifier les contraintes additionnelles comme la diversification
        position_size = self._apply_portfolio_constraints(token_address, position_size)
        
        return position_size
    
    def _calculate_volatility_based_position_size(self, volatility: float) -> float:
        """
        Calcule la taille de position basée sur la volatilité.
        
        Args:
            volatility: Volatilité du token (écart-type des rendements)
            
        Returns:
            Taille de position recommandée
        """
        # Plus la volatilité est élevée, plus la position sera petite
        volatility_factor = 0.15 / max(volatility, 0.01)  # Normaliser par rapport à 15% de volatilité
        
        # Limiter la taille à une fraction du portefeuille
        max_size = self.portfolio_value * self.max_position_size_pct
        
        return min(self.portfolio_value * 0.1 * volatility_factor, max_size)
    
    def _get_token_performance_metrics(self, token_address: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Récupère les métriques de performance historique pour un token.
        
        Args:
            token_address: Adresse du token
            
        Returns:
            Tuple (taux de succès, gain moyen en %, perte moyenne en %)
        """
        # Cette fonction devrait idéalement analyser les trades passés dans la base de données
        # Ici, nous utilisons des valeurs simulées pour l'exemple
        # Une vraie implémentation consulterait l'historique des transactions et calculerait ces métriques
        
        # Pour l'exemple, on renvoie des valeurs par défaut
        return 0.55, 0.12, 0.08  # 55% win rate, 12% gain moyen, 8% perte moyenne
    
    def _get_token_volatility(self, token_address: str) -> Optional[float]:
        """
        Calcule la volatilité d'un token à partir de son historique de prix.
        
        Args:
            token_address: Adresse du token
            
        Returns:
            Volatilité (écart-type des rendements) ou None si pas assez de données
        """
        if token_address not in self.price_history or len(self.price_history[token_address]) < 2:
            return None
            
        # Calculer les rendements journaliers
        prices = self.price_history[token_address]
        returns = [(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
        
        # Calculer l'écart-type des rendements (volatilité)
        return float(np.std(returns))
    
    def _apply_portfolio_constraints(self, token_address: str, proposed_size: float) -> float:
        """
        Applique les contraintes de portefeuille pour ajuster la taille de la position.
        
        Args:
            token_address: Adresse du token
            proposed_size: Taille de position proposée
            
        Returns:
            Taille de position ajustée
        """
        # 1. Vérifier la contrainte de taille maximale absolue
        max_allowed_size = self.portfolio_value * self.max_position_size_pct
        size = min(proposed_size, max_allowed_size)
        
        # 2. Vérifier les expositions corrélées
        correlated_tokens = self._find_correlated_tokens(token_address)
        if correlated_tokens:
            current_exposure = sum(pos.size for addr, pos in self.positions.items() 
                                 if addr in correlated_tokens)
            max_correlated = self.portfolio_value * self.max_correlated_exposure
            
            if current_exposure + size > max_correlated:
                size = max(0, max_correlated - current_exposure)
                logger.warning(f"Taille de position réduite en raison d'exposition corrélée: ${size:.2f}")
                
        # 3. Vérifier la diversification globale (pas plus de X% du portefeuille sur un seul token)
        # Cela est déjà pris en compte par max_position_size_pct
        
        return size
    
    def _find_correlated_tokens(self, token_address: str, threshold: float = 0.7) -> List[str]:
        """
        Trouve les tokens fortement corrélés avec le token donné.
        
        Args:
            token_address: Adresse du token
            threshold: Seuil de corrélation (0.7 = 70% de corrélation)
            
        Returns:
            Liste des adresses de tokens corrélés
        """
        # Idéalement, cela utiliserait une matrice de corrélation calculée à partir des données historiques
        # Pour l'exemple, nous renvoyons une liste vide
        return []
    
    def add_position(self, position: Position) -> str:
        """
        Ajoute une nouvelle position au gestionnaire de risque.
        
        Args:
            position: Objet Position à ajouter
            
        Returns:
            ID unique de la position
        """
        if not position.id:
            position.id = f"pos_{len(self.positions)}_{int(time.time())}"
            
        self.positions[position.token_address] = position
        logger.info(f"Position ajoutée: {position.token_symbol} - {position.size:.2f} unités à {position.entry_price:.6f}")
        
        return position.id
    
    def update_position(self, token_address: str, current_price: float) -> None:
        """
        Met à jour une position avec le prix courant et vérifie les stop-loss et take-profit.
        
        Args:
            token_address: Adresse du token
            current_price: Prix actuel
        """
        if token_address not in self.positions:
            return
            
        position = self.positions[token_address]
        
        # Mettre à jour le trailing stop si nécessaire
        self._update_trailing_stop(position, current_price)
        
        # Vérifier si un stop-loss ou take-profit a été atteint
        if self._check_stop_conditions(position, current_price):
            # La position a été fermée par un stop
            logger.info(f"Position {position.token_symbol} fermée par stop/target à {current_price:.6f}")
    
    def _update_trailing_stop(self, position: Position, current_price: float) -> None:
        """
        Met à jour le trailing stop d'une position si nécessaire.
        
        Args:
            position: Position à mettre à jour
            current_price: Prix actuel
        """
        if position.trailing_stop is None or position.trailing_distance is None:
            return
            
        # Pour une position longue, le trailing stop monte avec le prix
        if current_price > position.entry_price:  # Position longue
            new_stop = current_price * (1 - position.trailing_distance)
            if new_stop > position.trailing_stop:
                position.trailing_stop = new_stop
                logger.info(f"Trailing stop mis à jour: {position.token_symbol} -> {new_stop:.6f}")
        
        # Pour une position courte, le trailing stop descend avec le prix
        # Cela nécessiterait une logique supplémentaire pour les positions courtes
    
    def _check_stop_conditions(self, position: Position, current_price: float) -> bool:
        """
        Vérifie si une position a atteint ses conditions de stop ou target.
        
        Args:
            position: Position à vérifier
            current_price: Prix actuel
            
        Returns:
            True si une condition de stop a été atteinte
        """
        # Vérifier le stop-loss
        if position.stop_loss is not None:
            if current_price <= position.stop_loss:  # Condition de stop-loss
                logger.warning(f"Stop-loss déclenché pour {position.token_symbol} à {current_price:.6f}")
                del self.positions[position.token_address]
                return True
        
        # Vérifier le trailing stop
        if position.trailing_stop is not None:
            if current_price <= position.trailing_stop:  # Condition de trailing stop
                logger.warning(f"Trailing stop déclenché pour {position.token_symbol} à {current_price:.6f}")
                del self.positions[position.token_address]
                return True
                
        # Vérifier le take-profit
        if position.take_profit is not None:
            if current_price >= position.take_profit:  # Condition de take-profit
                logger.info(f"Take-profit atteint pour {position.token_symbol} à {current_price:.6f}")
                del self.positions[position.token_address]
                return True
                
        return False
    
    async def calculate_risk_metrics(self) -> RiskMetrics:
        """
        Calcule les métriques de risque complètes pour le portefeuille.
        
        Returns:
            Objet RiskMetrics contenant les mesures de risque calculées
        """
        # Calculer la valeur actuelle du portefeuille
        current_exposure = sum(pos.size * self._get_current_price(pos.token_address)
                               for pos in self.positions.values())
        
        # Calculer la volatilité du portefeuille
        port_volatility = await self._calculate_portfolio_volatility()
        
        # Calculer VaR et CVaR à 95%
        var_95, cvar_95 = await self._calculate_var_cvar(confidence=0.95)
        
        # Calculer le drawdown maximum
        max_dd = self._calculate_max_drawdown()
        
        # Calculer le ratio de Sharpe
        sharpe = await self._calculate_sharpe_ratio()
        
        # Trouver la position la plus grande
        max_position = max((pos.size for pos in self.positions.values()), default=0)
        
        # Générer la matrice de corrélation (simplifiée pour l'exemple)
        correlation_matrix = await self._calculate_correlation_matrix()
        
        return RiskMetrics(
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            current_exposure=current_exposure,
            max_position_size=max_position,
            correlation_matrix=correlation_matrix,
            portfolio_volatility=port_volatility
        )
    
    async def _calculate_var_cvar(self, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calcule la Valeur à Risque (VaR) et la VaR conditionnelle (CVaR) du portefeuille.
        
        Args:
            confidence: Niveau de confiance (généralement 0.95 ou 0.99)
            
        Returns:
            Tuple (VaR, CVaR) en unités monétaires
        """
        # Pour une implémentation réelle, utilisez des simulations historiques ou Monte Carlo
        # Ici nous utilisons une approche simplifiée basée sur la volatilité
        
        # Récupérer la volatilité du portefeuille
        portfolio_volatility = await self._calculate_portfolio_volatility()
        
        # Calculer VaR paramétrique (basé sur la distribution normale)
        # Pour un niveau de confiance de 95%, le z-score est environ 1.645
        z_score = 1.645 if confidence == 0.95 else 2.326  # 2.326 pour 99%
        
        portfolio_value = sum(pos.size for pos in self.positions.values())
        
        # VaR quotidienne (avec l'hypothèse d'une distribution normale)
        var = portfolio_value * portfolio_volatility * z_score
        
        # CVaR est généralement 1.3 à 1.5 fois la VaR pour des conditions de marché normales
        cvar = var * 1.4
        
        return var, cvar
    
    def _calculate_max_drawdown(self) -> float:
        """
        Calcule le drawdown maximum observé.
        
        Returns:
            Drawdown maximum en pourcentage
        """
        if not self.historical_portfolio_values or len(self.historical_portfolio_values) < 2:
            return 0.0
            
        # Extraction des valeurs
        values = [value for _, value in self.historical_portfolio_values]
        
        # Calcul du drawdown maximum
        max_dd = 0
        peak = values[0]
        
        for value in values:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak if peak > 0 else 0
                max_dd = max(max_dd, drawdown)
                
        return max_dd
    
    async def _calculate_portfolio_volatility(self) -> float:
        """
        Calcule la volatilité du portefeuille en tenant compte des corrélations.
        
        Returns:
            Volatilité du portefeuille (écart-type des rendements)
        """
        # Si nous n'avons pas de positions ou pas d'historique, renvoyer une valeur par défaut
        if not self.positions or not any(addr in self.price_history for addr in self.positions):
            return 0.03  # 3% par défaut
            
        # Pour une implémentation réelle, nous calculerions:
        # 1. Les volatilités individuelles de chaque actif
        # 2. Les corrélations entre les actifs
        # 3. La volatilité du portefeuille en utilisant la formule de variance du portefeuille
        
        # Pour l'exemple, nous utilisons une approche simplifiée
        weighted_volatility = 0.0
        total_weight = 0.0
        
        for addr, position in self.positions.items():
            volatility = self._get_token_volatility(addr) or 0.03  # Valeur par défaut
            price = self._get_current_price(addr)
            position_value = position.size * price
            weighted_volatility += position_value * volatility
            total_weight += position_value
            
        if total_weight > 0:
            return weighted_volatility / total_weight
        else:
            return 0.03  # Valeur par défaut
    
    async def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calcule le ratio de Sharpe du portefeuille.
        
        Args:
            risk_free_rate: Taux sans risque annualisé
            
        Returns:
            Ratio de Sharpe
        """
        # Pour calculer correctement le ratio de Sharpe, nous avons besoin:
        # 1. Du rendement moyen annualisé du portefeuille
        # 2. De la volatilité annualisée du portefeuille
        # 3. Du taux sans risque annualisé
        
        # Pour l'exemple, nous simulons un rendement annualisé
        annualized_return = 0.12  # 12% de rendement annuel (exemple)
        
        # Récupérer la volatilité quotidienne et l'annualiser
        daily_volatility = await self._calculate_portfolio_volatility()
        annualized_volatility = daily_volatility * np.sqrt(252)  # 252 jours de trading par an
        
        if annualized_volatility == 0:
            return 0
            
        # Calcul du ratio de Sharpe
        sharpe = (annualized_return - risk_free_rate) / annualized_volatility
        
        return sharpe
    
    async def _calculate_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Calcule la matrice de corrélation entre les différents tokens du portefeuille.
        
        Returns:
            Matrice de corrélation sous forme de dictionnaire imbriqué
        """
        # Pour une implémentation réelle, nous calculerions les corrélations à partir
        # des séries temporelles de rendements
        
        # Pour l'exemple, nous renvoyons une structure vide
        correlation_matrix = {}
        
        for addr1, pos1 in self.positions.items():
            correlation_matrix[addr1] = {}
            for addr2, pos2 in self.positions.items():
                correlation_matrix[addr1][addr2] = 1.0 if addr1 == addr2 else 0.3  # Corrélation simulée
                
        return correlation_matrix
    
    def _get_current_price(self, token_address: str) -> float:
        """
        Obtient le prix actuel d'un token.
        
        Args:
            token_address: Adresse du token
            
        Returns:
            Prix actuel, ou 0 si non disponible
        """
        # Cette méthode devrait idéalement utiliser un service de prix en temps réel
        # Pour l'exemple, nous simulons un prix
        
        if token_address in self.price_history and self.price_history[token_address]:
            return self.price_history[token_address][-1]
        else:
            return 0.0

    def update_price_history(self, token_address: str, price: float) -> None:
        """
        Met à jour l'historique des prix d'un token.
        
        Args:
            token_address: Adresse du token
            price: Prix actuel
        """
        if token_address not in self.price_history:
            self.price_history[token_address] = []
            
        self.price_history[token_address].append(price)
        
        # Limiter la taille de l'historique
        max_history = self.volatility_window * 100  # 100 points par jour
        if len(self.price_history[token_address]) > max_history:
            self.price_history[token_address] = self.price_history[token_address][-max_history:]

    def generate_risk_report(self) -> Dict[str, Any]:
        """
        Génère un rapport complet des risques pour le portefeuille.
        
        Returns:
            Rapport de risque sous forme de dictionnaire
        """
        report = {
            'timestamp': time.time(),
            'portfolio_value': self.portfolio_value,
            'positions_count': len(self.positions),
            'positions': {}
        }
        
        # Détails des positions
        for addr, pos in self.positions.items():
            current_price = self._get_current_price(addr)
            pnl = (current_price - pos.entry_price) * pos.size
            pnl_pct = (current_price / pos.entry_price - 1) * 100 if pos.entry_price > 0 else 0
            
            report['positions'][addr] = {
                'symbol': pos.token_symbol,
                'size': pos.size,
                'entry_price': pos.entry_price,
                'current_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'stop_loss': pos.stop_loss,
                'take_profit': pos.take_profit,
                'trailing_stop': pos.trailing_stop
            }
        
        # Ajouter des métriques de risque calculées de façon asynchrone
        # Note: cela nécessiterait normalement d'être exécuté dans un bloc async
        # Pour l'exemple, nous simulons des valeurs
        
        report['risk'] = {
            'var_95': self.portfolio_value * 0.05,  # 5% VaR (simulé)
            'max_drawdown': 0.12,  # 12% (simulé)
            'sharpe_ratio': 1.5,  # (simulé)
            'volatility': 0.02  # 2% (simulé)
        }
        
        return report
