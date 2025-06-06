"""
C8 - Optimized SecurityChecker with performance improvements.
Refactoring avec cache, parallélisation et intégration ResourceManager.
"""

import asyncio
import time
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
import sqlite3
import json
from concurrent.futures import ThreadPoolExecutor
import cachetools

from app.config import get_config
from app.services.market_data_cache import MarketDataCache
from app.services.resource_manager import ResourceManager, TaskPriority
from app.security.security import SecurityRisk  # Réutilise les types existants

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Niveaux de risque optimisés."""
    MINIMAL = "minimal"      # 1-2
    LOW = "low"             # 3-4
    MEDIUM = "medium"       # 5-6
    HIGH = "high"           # 7-8
    CRITICAL = "critical"   # 9-10

@dataclass
class SecurityAnalysisResult:
    """Résultat d'analyse de sécurité optimisé."""
    token_address: str
    is_safe: bool
    risk_level: RiskLevel
    risk_score: float
    risks: List[SecurityRisk]
    analysis_time_ms: float
    cached: bool
    sources_used: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversion en dictionnaire pour sérialisation."""
        return {
            'token_address': self.token_address,
            'is_safe': self.is_safe,
            'risk_level': self.risk_level.value,
            'risk_score': self.risk_score,
            'risks': [asdict(risk) for risk in self.risks],
            'analysis_time_ms': self.analysis_time_ms,
            'cached': self.cached,
            'sources_used': self.sources_used
        }

class OptimizedSecurityChecker:
    """
    SecurityChecker optimisé pour performances avec:
    - Cache multi-niveau (TTL + LRU)
    - Parallélisation des vérifications
    - Intégration ResourceManager pour limitation CPU
    - Base de données optimisée avec indexes
    - Réduction des appels API redondants
    """
    
    def __init__(
        self,
        db_path: str,
        market_data_cache: MarketDataCache,
        resource_manager: ResourceManager,
        cache_size: int = 1000,
        cache_ttl: int = 300  # 5 minutes
    ):
        """Initialiser le SecurityChecker optimisé."""
        self.db_path = db_path
        self.market_data = market_data_cache
        self.resource_manager = resource_manager
        
        # Cache mémoire multi-niveau
        self.analysis_cache = cachetools.TTLCache(maxsize=cache_size, ttl=cache_ttl)
        self.risk_cache = cachetools.TTLCache(maxsize=cache_size * 2, ttl=cache_ttl // 2)
        self.blacklist_cache = cachetools.TTLCache(maxsize=500, ttl=3600)  # 1h TTL
        
        # Pool de threads pour I/O
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Connexion DB optimisée
        self.conn = self._initialize_optimized_database()
        
        # Modèles de risque préchargés
        self.risk_patterns = self._load_risk_patterns()
        
        # Statistiques performance
        self.stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'avg_analysis_time': 0.0,
            'parallel_analyses': 0,
            'errors': 0
        }
        
        logger.info("OptimizedSecurityChecker initialisé avec succès")
    
    def _initialize_optimized_database(self) -> sqlite3.Connection:
        """Initialise la base de données avec optimisations SQLite."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
            
            # Optimisations SQLite pour performance
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            
            cursor = conn.cursor()
            
            # Table blacklist optimisée
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklist_optimized (
                    address TEXT PRIMARY KEY,
                    reason TEXT,
                    severity INTEGER,
                    timestamp REAL,
                    metadata TEXT,
                    risk_score REAL,
                    expires_at REAL
                ) WITHOUT ROWID
            ''')
            
            # Indexes pour performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_blacklist_severity ON blacklist_optimized(severity DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_blacklist_timestamp ON blacklist_optimized(timestamp DESC)')
            
            # Table performance metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_performance (
                    id INTEGER PRIMARY KEY,
                    token_address TEXT,
                    analysis_time_ms REAL,
                    risk_count INTEGER,
                    cached BOOLEAN,
                    timestamp REAL
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON analysis_performance(timestamp DESC)')
            
            conn.commit()
            return conn
            
        except Exception as e:
            logger.error(f"Erreur initialisation DB optimisée: {e}")
            raise
    
    def _load_risk_patterns(self) -> Dict[str, Any]:
        """Charge les modèles de risque depuis la config."""
        config = get_config()
        
        return {
            'holder_concentration': {
                'high_threshold': getattr(config, 'HOLDER_CONCENTRATION_THRESHOLD_HIGH', 0.5),
                'medium_threshold': getattr(config, 'HOLDER_CONCENTRATION_THRESHOLD_MEDIUM', 0.3),
                'min_holders': getattr(config, 'MIN_HOLDERS_COUNT_THRESHOLD', 10)
            },
            'liquidity_thresholds': {
                'min_liquidity_usd': getattr(config, 'MIN_LIQUIDITY_USD', 10000),
                'price_impact_threshold': getattr(config, 'PRICE_IMPACT_THRESHOLD', 0.05)
            },
            'transaction_velocity': {
                'high_velocity_threshold': getattr(config, 'HIGH_VELOCITY_TX_COUNT_THRESHOLD', 100),
                'time_window_hours': 1
            },
            'price_analysis': {
                'drop_threshold': getattr(config, 'RUGPULL_PRICE_DROP_THRESHOLD', -0.5),
                'volatility_threshold': 0.3
            }
        }
    
    async def analyze_token_security(
        self,
        token_address: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        use_cache: bool = True
    ) -> SecurityAnalysisResult:
        """Analyse optimisée de sécurité d'un token."""
        start_time = time.time()
        
        # Vérification cache
        if use_cache and token_address in self.analysis_cache:
            cached_result = self.analysis_cache[token_address]
            cached_result.cached = True
            self.stats['cache_hits'] += 1
            return cached_result
        
        # Validation format adresse
        if not self._is_valid_solana_address(token_address):
            return self._create_error_result(token_address, "invalid_address", 10, "Format d'adresse invalide", start_time)
        
        # Vérification blacklist cache
        if await self._is_blacklisted_cached(token_address):
            return self._create_error_result(token_address, "blacklisted", 10, "Token blacklisté", start_time, cached=True)
        
        # Soumission tâche au ResourceManager pour isolation CPU
        try:
            task_id = await self.resource_manager.submit_ai_task(
                task_func=self._perform_security_analysis,
                task_args=(token_address,),
                priority=priority,
                timeout=30
            )
            
            # Attendre résultat avec timeout
            result = await self._wait_for_analysis_result(task_id, token_address, start_time)
            
            # Cache résultat si valide
            if use_cache and result.is_safe is not None:
                self.analysis_cache[token_address] = result
            
            # Mise à jour stats
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur analyse sécurité {token_address}: {e}")
            self.stats['errors'] += 1
            return self._create_error_result(token_address, "analysis_error", 8, f"Erreur: {str(e)}", start_time)
    
    async def _perform_security_analysis(self, token_address: str) -> SecurityAnalysisResult:
        """Effectue l'analyse de sécurité avec parallélisation."""
        start_time = time.time()
        all_risks = []
        sources_used = []
        
        # Analyses parallèles pour performance maximale
        analysis_tasks = [
            self._analyze_token_info(token_address),
            self._analyze_holders_parallel(token_address),
            self._analyze_liquidity_parallel(token_address),
            self._analyze_rugpull_patterns(token_address)
        ]
        
        task_names = ["token_info", "holders", "liquidity", "rugpull"]
        
        try:
            # Exécution parallèle avec gather
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Traitement des résultats
            for i, result in enumerate(results):
                task_name = task_names[i]
                sources_used.append(task_name)
                
                if isinstance(result, Exception):
                    logger.warning(f"Erreur analyse {task_name}: {result}")
                    all_risks.append(SecurityRisk(
                        risk_type=f"{task_name}_error",
                        severity=4,
                        description=f"Erreur {task_name}: {str(result)}",
                        metadata={"task": task_name, "error": str(result)}
                    ))
                elif isinstance(result, list):
                    all_risks.extend(result)
                    
        except Exception as e:
            logger.error(f"Erreur analyse parallèle {token_address}: {e}")
            all_risks.append(SecurityRisk(
                risk_type="parallel_analysis_error",
                severity=6,
                description=f"Erreur analyse parallèle: {str(e)}",
                metadata={"error": str(e)}
            ))
        
        # Calcul score et niveau de risque
        risk_score, risk_level = self._calculate_risk_score(all_risks)
        is_safe = risk_score < 7.0
        
        # Ajout blacklist si nécessaire
        if not is_safe and risk_score >= 8.0:
            await self._add_to_blacklist_async(token_address, all_risks)
        
        analysis_time = (time.time() - start_time) * 1000
        self.stats['parallel_analyses'] += 1
        
        return SecurityAnalysisResult(
            token_address=token_address,
            is_safe=is_safe,
            risk_level=risk_level,
            risk_score=risk_score,
            risks=all_risks,
            analysis_time_ms=analysis_time,
            cached=False,
            sources_used=sources_used
        )
    
    async def _analyze_token_info(self, token_address: str) -> List[SecurityRisk]:
        """Analyse optimisée des informations token."""
        risks = []
        
        try:
            result = await self.market_data.get_token_info(token_address)
            
            if not result.get('success'):
                return [SecurityRisk("token_info_unavailable", 4, "Info token indisponible", {"error": result.get('error')})]
            
            token_info = result['data']
            
            # Vérifications métadonnées
            if not token_info.get('name') or not token_info.get('symbol'):
                risks.append(SecurityRisk("missing_metadata", 3, "Métadonnées manquantes", {"info": token_info}))
            
            # Analyse âge token
            created_at = token_info.get('created_at')
            if created_at:
                age_days = (time.time() - float(created_at)) / 86400
                
                if age_days < 1:
                    risks.append(SecurityRisk("very_new_token", 7, f"Token très récent: {age_days:.1f}h", {"age_days": age_days}))
                elif age_days < 7:
                    risks.append(SecurityRisk("new_token", 4, f"Token récent: {age_days:.1f}j", {"age_days": age_days}))
            
            return risks
            
        except Exception as e:
            return [SecurityRisk("token_info_error", 5, f"Erreur analyse info: {str(e)}", {"error": str(e)})]
    
    async def _analyze_holders_parallel(self, token_address: str) -> List[SecurityRisk]:
        """Analyse optimisée des détenteurs avec cache."""
        cache_key = f"holders_{token_address}"
        
        if cache_key in self.risk_cache:
            return self.risk_cache[cache_key]
        
        risks = []
        
        try:
            result = await self.market_data.get_token_holders(token_address, limit=100)
            
            if not result.get('success'):
                return [SecurityRisk("holders_data_unavailable", 3, "Données détenteurs indisponibles", {"error": result.get('error')})]
            
            holders_data = result['data'].get('holders', [])
            
            if not holders_data:
                return [SecurityRisk("no_holders_data", 3, "Aucune donnée détenteur", {})]
            
            patterns = self.risk_patterns['holder_concentration']
            
            # Analyse concentration (optimisée)
            non_verified = [h for h in holders_data if not h.get('is_verified', False)]
            
            if non_verified:
                largest_pct = max(h.get('percentage', 0) for h in non_verified)
                
                if largest_pct > patterns['high_threshold']:
                    risks.append(SecurityRisk("high_concentration", 8, f"Concentration élevée: {largest_pct*100:.1f}%", {"percentage": largest_pct}))
                elif largest_pct > patterns['medium_threshold']:
                    risks.append(SecurityRisk("medium_concentration", 5, f"Concentration modérée: {largest_pct*100:.1f}%", {"percentage": largest_pct}))
            
            # Nombre de détenteurs
            if len(holders_data) < patterns['min_holders']:
                risks.append(SecurityRisk("few_holders", 6, f"Peu de détenteurs: {len(holders_data)}", {"count": len(holders_data)}))
            
            # Cache résultat
            self.risk_cache[cache_key] = risks
            return risks
            
        except Exception as e:
            return [SecurityRisk("holders_analysis_error", 4, f"Erreur analyse détenteurs: {str(e)}", {"error": str(e)})]
    
    async def _analyze_liquidity_parallel(self, token_address: str) -> List[SecurityRisk]:
        """Analyse optimisée de liquidité."""
        risks = []
        
        try:
            result = await self.market_data.get_liquidity_data(token_address)
            
            if not result.get('success'):
                return [SecurityRisk("liquidity_data_unavailable", 4, "Données liquidité indisponibles", {"error": result.get('error')})]
            
            liquidity_data = result['data']
            liquidity_usd = liquidity_data.get('liquidity_usd', 0)
            
            patterns = self.risk_patterns['liquidity_thresholds']
            
            # Vérification liquidité minimale
            if liquidity_usd < patterns['min_liquidity_usd']:
                severity = 8 if liquidity_usd < 1000 else 6
                risks.append(SecurityRisk("low_liquidity", severity, f"Liquidité faible: ${liquidity_usd:,.0f}", {"liquidity_usd": liquidity_usd}))
            
            # Analyse distribution DEX
            dex_distribution = liquidity_data.get('dex_distribution', {})
            if dex_distribution:
                max_dex_share = max(dex_distribution.values())
                if max_dex_share > 0.8:
                    risks.append(SecurityRisk("concentrated_dex_liquidity", 5, f"Liquidité concentrée: {max_dex_share*100:.1f}%", {"max_share": max_dex_share}))
            
            return risks
            
        except Exception as e:
            return [SecurityRisk("liquidity_analysis_error", 4, f"Erreur analyse liquidité: {str(e)}", {"error": str(e)})]
    
    async def _analyze_rugpull_patterns(self, token_address: str) -> List[SecurityRisk]:
        """Analyse optimisée des modèles de rug pull."""
        risks = []
        
        try:
            # Analyse prix (parallèle)
            price_task = self.market_data.get_historical_prices(token_address, timeframe="1h", limit=48)
            tx_task = self.market_data.get_token_transactions(token_address, limit=100)
            
            price_result, tx_result = await asyncio.gather(price_task, tx_task, return_exceptions=True)
            
            # Analyse prix
            if not isinstance(price_result, Exception) and price_result.get('success'):
                prices = price_result['data']
                
                if len(prices) > 1:
                    price_changes = []
                    for i in range(1, len(prices)):
                        prev = prices[i-1].get('close', 0)
                        curr = prices[i].get('close', 0)
                        if prev > 0:
                            price_changes.append((curr - prev) / prev)
                    
                    if price_changes:
                        max_drop = min(price_changes)
                        if max_drop < self.risk_patterns['price_analysis']['drop_threshold']:
                            risks.append(SecurityRisk("significant_price_drop", 8, f"Chute brutale: {max_drop*100:.1f}%", {"max_drop": max_drop}))
                        
                        # Volatilité
                        volatility = self._calculate_volatility(price_changes)
                        if volatility > self.risk_patterns['price_analysis']['volatility_threshold']:
                            risks.append(SecurityRisk("high_volatility", 6, f"Volatilité élevée: {volatility*100:.1f}%", {"volatility": volatility}))
            
            # Analyse transactions
            if not isinstance(tx_result, Exception) and tx_result.get('success'):
                transactions = tx_result['data']
                
                # Vélocité transactions
                recent_count = len([tx for tx in transactions if tx.get('timestamp', 0) > time.time() - 3600])
                if recent_count > self.risk_patterns['transaction_velocity']['high_velocity_threshold']:
                    risks.append(SecurityRisk("high_transaction_velocity", 5, f"Vélocité élevée: {recent_count} tx/h", {"recent_count": recent_count}))
                
                # Wash trading
                if self._detect_wash_trading_optimized(transactions):
                    risks.append(SecurityRisk("wash_trading_pattern", 7, "Modèle wash trading détecté", {"tx_count": len(transactions)}))
            
            return risks
            
        except Exception as e:
            return [SecurityRisk("rugpull_analysis_error", 4, f"Erreur analyse rug pull: {str(e)}", {"error": str(e)})]
    
    def _calculate_volatility(self, price_changes: List[float]) -> float:
        """Calcule la volatilité (écart-type)."""
        if not price_changes:
            return 0.0
        
        mean = sum(price_changes) / len(price_changes)
        variance = sum((x - mean) ** 2 for x in price_changes) / len(price_changes)
        return variance ** 0.5
    
    def _detect_wash_trading_optimized(self, transactions: List[Dict[str, Any]]) -> bool:
        """Détection optimisée wash trading."""
        if len(transactions) < 10:
            return False
        
        # Analyse dernières 20 transactions
        recent_txs = transactions[-20:] if len(transactions) >= 20 else transactions
        address_freq = {}
        
        for tx in recent_txs:
            from_addr = tx.get('from_address', '')
            to_addr = tx.get('to_address', '')
            
            if from_addr:
                address_freq[from_addr] = address_freq.get(from_addr, 0) + 1
            if to_addr:
                address_freq[to_addr] = address_freq.get(to_addr, 0) + 1
        
        # Détection fréquence anormale
        if address_freq:
            max_freq = max(address_freq.values())
            avg_freq = sum(address_freq.values()) / len(address_freq)
            return max_freq > avg_freq * 3
        
        return False
    
    def _calculate_risk_score(self, risks: List[SecurityRisk]) -> Tuple[float, RiskLevel]:
        """Calcule score et niveau de risque avec pondération."""
        if not risks:
            return 0.0, RiskLevel.MINIMAL
        
        total_score = 0.0
        critical_count = 0
        
        # Pondération par type de risque
        weights = {
            'blacklisted': 2.0,
            'invalid_address': 2.0,
            'high_concentration': 1.5,
            'significant_price_drop': 1.5,
            'very_new_token': 1.3,
            'low_liquidity': 1.2
        }
        
        for risk in risks:
            weight = weights.get(risk.risk_type, 1.0)
            weighted_severity = risk.severity * weight
            total_score += weighted_severity
            
            if risk.severity >= 9:
                critical_count += 1
        
        # Score moyen avec bonus critiques
        avg_score = total_score / len(risks)
        final_score = min(10.0, avg_score + (critical_count * 0.5))
        
        # Niveau de risque
        if final_score >= 9:
            level = RiskLevel.CRITICAL
        elif final_score >= 7:
            level = RiskLevel.HIGH
        elif final_score >= 5:
            level = RiskLevel.MEDIUM
        elif final_score >= 3:
            level = RiskLevel.LOW
        else:
            level = RiskLevel.MINIMAL
        
        return final_score, level
    
    async def _is_blacklisted_cached(self, token_address: str) -> bool:
        """Vérification blacklist avec cache TTL."""
        cache_key = f"blacklist_{token_address}"
        
        if cache_key in self.blacklist_cache:
            return self.blacklist_cache[cache_key]
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT address FROM blacklist_optimized WHERE address = ? AND (expires_at IS NULL OR expires_at > ?)",
                (token_address, time.time())
            )
            
            is_blacklisted = cursor.fetchone() is not None
            self.blacklist_cache[cache_key] = is_blacklisted
            return is_blacklisted
            
        except Exception as e:
            logger.error(f"Erreur vérification blacklist: {e}")
            return False
    
    async def _add_to_blacklist_async(self, token_address: str, risks: List[SecurityRisk]) -> None:
        """Ajout blacklist asynchrone optimisé."""
        try:
            severe_risks = [r for r in risks if r.severity >= 8]
            if not severe_risks:
                return
            
            risk_score = sum(r.severity for r in severe_risks) / len(severe_risks)
            expires_at = time.time() + (30 * 24 * 3600)  # 30 jours
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO blacklist_optimized 
                (address, reason, severity, timestamp, metadata, risk_score, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                token_address,
                f"{len(severe_risks)} risques critiques",
                max(r.severity for r in severe_risks),
                time.time(),
                json.dumps([asdict(r) for r in severe_risks]),
                risk_score,
                expires_at
            ))
            
            self.conn.commit()
            
            # Invalider cache
            self.blacklist_cache.pop(f"blacklist_{token_address}", None)
            
        except Exception as e:
            logger.error(f"Erreur ajout blacklist: {e}")
    
    def _is_valid_solana_address(self, address: str) -> bool:
        """Validation optimisée adresse Solana."""
        if not isinstance(address, str) or len(address) != 44:
            return False
        
        base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return all(c in base58_chars for c in address)
    
    def _create_error_result(self, token_address: str, risk_type: str, severity: int, description: str, start_time: float, cached: bool = False) -> SecurityAnalysisResult:
        """Créer un résultat d'erreur standardisé."""
        return SecurityAnalysisResult(
            token_address=token_address,
            is_safe=False,
            risk_level=RiskLevel.CRITICAL if severity >= 9 else RiskLevel.HIGH,
            risk_score=float(severity),
            risks=[SecurityRisk(risk_type, severity, description, {"address": token_address})],
            analysis_time_ms=(time.time() - start_time) * 1000,
            cached=cached,
            sources_used=["validation" if "invalid" in risk_type else "blacklist"]
        )
    
    async def _wait_for_analysis_result(self, task_id: str, token_address: str, start_time: float) -> SecurityAnalysisResult:
        """Attendre résultat avec timeout optimisé."""
        timeout = 30
        check_interval = 0.1
        elapsed = 0
        
        while elapsed < timeout:
            try:
                status = await self.resource_manager.get_task_status(task_id)
                
                if status['status'] == 'completed':
                    return status.get('result', self._create_error_result(token_address, "no_result", 7, "Résultat manquant", start_time))
                elif status['status'] == 'failed':
                    error = status.get('error', 'Erreur inconnue')
                    return self._create_error_result(token_address, "task_failed", 7, f"Échec tâche: {error}", start_time)
                
                await asyncio.sleep(check_interval)
                elapsed += check_interval
                
            except Exception as e:
                logger.error(f"Erreur attente résultat: {e}")
                break
        
        return self._create_error_result(token_address, "analysis_timeout", 7, "Timeout analyse", start_time)
    
    def _update_stats(self, result: SecurityAnalysisResult) -> None:
        """Mise à jour statistiques performance."""
        self.stats['total_analyses'] += 1
        
        if result.cached:
            self.stats['cache_hits'] += 1
        
        # Moyenne mobile temps analyse
        current_avg = self.stats['avg_analysis_time']
        new_avg = (current_avg * 0.9) + (result.analysis_time_ms * 0.1)
        self.stats['avg_analysis_time'] = new_avg
        
        # Persistence en DB (asynchrone)
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO analysis_performance 
                (token_address, analysis_time_ms, risk_count, cached, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (result.token_address, result.analysis_time_ms, len(result.risks), result.cached, time.time()))
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Erreur sauvegarde stats: {e}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Statistiques performance complètes."""
        stats = self.stats.copy()
        
        # Stats cache
        stats['cache_stats'] = {
            'analysis_cache_size': len(self.analysis_cache),
            'risk_cache_size': len(self.risk_cache),
            'blacklist_cache_size': len(self.blacklist_cache),
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['total_analyses'])
        }
        
        # Stats ResourceManager
        try:
            rm_stats = await self.resource_manager.get_resource_stats()
            stats['resource_manager'] = rm_stats
        except Exception as e:
            stats['resource_manager'] = {"error": str(e)}
        
        return stats
    
    async def cleanup_cache(self) -> None:
        """Nettoie tous les caches."""
        self.analysis_cache.clear()
        self.risk_cache.clear()
        self.blacklist_cache.clear()
        logger.info("Caches nettoyés")
    
    async def close(self) -> None:
        """Fermeture propre."""
        try:
            self.thread_pool.shutdown(wait=True)
            self.conn.close()
            await self.cleanup_cache()
            logger.info("OptimizedSecurityChecker fermé")
        except Exception as e:
            logger.error(f"Erreur fermeture: {e}")

# Utilitaires pour migration depuis SecurityChecker original
async def migrate_from_legacy(
    legacy_db_path: str,
    optimized_db_path: str
) -> int:
    """
    Migre les données depuis l'ancien SecurityChecker.
    
    Args:
        legacy_db_path: Chemin ancienne DB
        optimized_db_path: Chemin nouvelle DB optimisée
        
    Returns:
        Nombre d'entrées migrées
    """
    try:
        # Connexion DBs
        legacy_conn = sqlite3.connect(legacy_db_path)
        optimized_conn = sqlite3.connect(optimized_db_path)
        
        # Migration blacklist
        legacy_cursor = legacy_conn.cursor()
        optimized_cursor = optimized_conn.cursor()
        
        legacy_cursor.execute("SELECT address, reason, severity, timestamp, metadata FROM blacklist")
        legacy_entries = legacy_cursor.fetchall()
        
        migrated_count = 0
        for entry in legacy_entries:
            address, reason, severity, timestamp, metadata = entry
            
            # Calcul expiration (30 jours depuis création)
            expires_at = timestamp + (30 * 24 * 3600)
            
            # Migration avec score par défaut
            risk_score = float(severity)
            
            optimized_cursor.execute('''
                INSERT OR IGNORE INTO blacklist_optimized 
                (address, reason, severity, timestamp, metadata, risk_score, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (address, reason, severity, timestamp, metadata, risk_score, expires_at))
            
            migrated_count += 1
        
        optimized_conn.commit()
        
        legacy_conn.close()
        optimized_conn.close()
        
        logger.info(f"Migration complétée: {migrated_count} entrées migrées")
        return migrated_count
        
    except Exception as e:
        logger.error(f"Erreur migration: {e}")
        return 0 