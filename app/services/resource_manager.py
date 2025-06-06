"""
Resource Manager pour isolation des ressources IA.
Prévient la surcharge CPU 200% identifiée dans C17.
"""

import asyncio
import logging
import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import json
from datetime import datetime, timedelta

from app.config import get_config

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Priorités des tâches."""
    CRITICAL = 1    # Trading decisions (highest priority)
    HIGH = 2        # Market analysis
    MEDIUM = 3      # Backtesting
    LOW = 4         # Non-critical analysis

@dataclass
class ResourceQuota:
    """Configuration des quotas de ressources."""
    max_cpu_percent: float = 50.0    # Max 50% CPU
    max_memory_mb: int = 8192        # Max 8GB RAM (ajusté pour environnement WSL)
    max_concurrent_tasks: int = 3    # Max 3 tâches simultanées
    max_queue_size: int = 100        # Max 100 tâches en queue

@dataclass
class TaskMetrics:
    """Métriques d'une tâche."""
    task_id: str
    task_type: str
    priority: TaskPriority
    cpu_usage: float
    memory_usage: int
    duration: float
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # running, completed, failed, throttled

@dataclass
class SystemMetrics:
    """Métriques système actuelles."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: int
    active_tasks: int
    queued_tasks: int
    timestamp: float

class ResourceManager:
    """
    Gestionnaire de ressources IA avec isolation et quotas.
    
    Fonctionnalités:
    - Quotas CPU/RAM configurables
    - Queue prioritaire pour tâches IA
    - Throttling automatique en cas de surcharge
    - Monitoring temps réel des ressources
    - Circuit breaker pour protection système
    """
    
    def __init__(self, config=None, quota: Optional[ResourceQuota] = None):
        self.config = config or get_config()
        self.quota = quota or ResourceQuota()
        
        # État interne
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.task_history: List[TaskMetrics] = []
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running = False
        self.worker_task: Optional[asyncio.Task] = None
        
        # Threading pour monitoring système
        self.metrics_lock = threading.Lock()
        self.current_metrics: Optional[SystemMetrics] = None
        
        # Redis pour persistance des métriques
        self.redis_client: Optional[redis.asyncio.Redis] = None
        
        # Circuit breaker
        self.circuit_breaker_active = False
        self.circuit_breaker_count = 0
        self.circuit_breaker_threshold = 5  # 5 surcharges consécutives
        
        logger.info(f"ResourceManager initialized with quota: CPU {self.quota.max_cpu_percent}%, RAM {self.quota.max_memory_mb}MB")

    async def __aenter__(self):
        """Initialise les connexions asynchrones."""
        try:
            # Redis connection pour métriques
            self.redis_client = redis.asyncio.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                db=self.config.redis.db,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established for ResourceManager")
            
        except Exception as e:
            logger.warning(f"Redis connection failed for ResourceManager: {e}")
            # Continue sans Redis si nécessaire
            
        # Démarrer le worker et monitoring
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme les connexions."""
        await self.stop()
        if self.redis_client:
            await self.redis_client.aclose()
        logger.info("ResourceManager connections closed")

    async def start(self):
        """Démarre le gestionnaire de ressources."""
        if self.running:
            return
            
        self.running = True
        
        # Démarrer le worker de traitement des tâches
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        # Démarrer le monitoring système
        asyncio.create_task(self._monitoring_loop())
        
        logger.info("ResourceManager started")

    async def stop(self):
        """Arrête le gestionnaire de ressources."""
        if not self.running:
            return
            
        self.running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("ResourceManager stopped")

    # =================================
    # API PUBLIQUE - GESTION TÂCHES IA
    # =================================

    async def submit_ai_task(
        self, 
        task_func: Callable[..., Awaitable[Any]], 
        task_type: str = "ai_decision",
        priority: TaskPriority = TaskPriority.CRITICAL,
        timeout: float = 30.0,
        *args, 
        **kwargs
    ) -> str:
        """
        Soumet une tâche IA pour exécution avec gestion des ressources.
        
        Args:
            task_func: Fonction async à exécuter
            task_type: Type de tâche pour métriques
            priority: Priorité de la tâche
            timeout: Timeout en secondes
            *args, **kwargs: Arguments pour task_func
            
        Returns:
            task_id: Identifiant unique de la tâche
            
        Raises:
            ResourceExhaustedException: Si quotas dépassés
            CircuitBreakerException: Si circuit breaker actif
        """
        # Vérifier circuit breaker
        if self.circuit_breaker_active:
            raise CircuitBreakerException("Circuit breaker active - système surchargé")
        
        # Vérifier quotas
        await self._check_quotas()
        
        # Créer tâche
        task_id = f"{task_type}_{int(time.time() * 1000)}"
        
        # Ajouter à la queue avec priorité
        priority_value = priority.value
        task_item = (priority_value, time.time(), task_id, task_func, task_type, timeout, args, kwargs)
        
        try:
            self.task_queue.put_nowait(task_item)
            logger.info(f"Task {task_id} queued with priority {priority.name}")
            return task_id
        except asyncio.QueueFull:
            raise ResourceExhaustedException(f"Queue full (max {self.quota.max_queue_size})")

    async def get_task_status(self, task_id: str) -> Optional[TaskMetrics]:
        """Récupère le statut d'une tâche."""
        # Chercher dans les tâches actives
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # Chercher dans l'historique récent
        for task in reversed(self.task_history):
            if task.task_id == task_id:
                return task
                
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Annule une tâche si possible."""
        if task_id in self.active_tasks:
            # Marquer comme annulée
            self.active_tasks[task_id].status = "cancelled"
            logger.info(f"Task {task_id} marked for cancellation")
            return True
        return False

    async def get_system_metrics(self) -> SystemMetrics:
        """Retourne les métriques système actuelles."""
        with self.metrics_lock:
            if self.current_metrics:
                return self.current_metrics
            
        # Fallback si monitoring pas encore lancé
        return self._collect_system_metrics()

    async def get_resource_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes des ressources."""
        system_metrics = await self.get_system_metrics()
        
        stats = {
            'system': asdict(system_metrics),
            'quotas': asdict(self.quota),
            'active_tasks': len(self.active_tasks),
            'queued_tasks': self.task_queue.qsize(),
            'circuit_breaker_active': self.circuit_breaker_active,
            'task_history_size': len(self.task_history),
            'total_tasks_processed': len(self.task_history),
            'resource_utilization': {
                'cpu_utilization': system_metrics.cpu_percent / self.quota.max_cpu_percent,
                'memory_utilization': system_metrics.memory_used_mb / self.quota.max_memory_mb,
                'task_utilization': system_metrics.active_tasks / self.quota.max_concurrent_tasks
            }
        }
        
        # Ajouter stats par type de tâche
        task_types = {}
        for task in self.task_history[-100:]:  # 100 dernières tâches
            task_type = task.task_type
            if task_type not in task_types:
                task_types[task_type] = {
                    'count': 0,
                    'avg_duration': 0,
                    'avg_cpu': 0,
                    'success_rate': 0
                }
            
            task_types[task_type]['count'] += 1
            task_types[task_type]['avg_duration'] += task.duration
            task_types[task_type]['avg_cpu'] += task.cpu_usage
            if task.status == 'completed':
                task_types[task_type]['success_rate'] += 1
        
        # Calculer moyennes
        for task_type, stats_type in task_types.items():
            count = stats_type['count']
            if count > 0:
                stats_type['avg_duration'] /= count
                stats_type['avg_cpu'] /= count
                stats_type['success_rate'] /= count
        
        stats['task_types'] = task_types
        
        return stats

    # =================================
    # MÉTHODES PRIVÉES - GESTION INTERNE
    # =================================

    async def _worker_loop(self):
        """Boucle principale de traitement des tâches."""
        logger.info("ResourceManager worker started")
        
        while self.running:
            try:
                # Attendre une tâche avec timeout
                try:
                    priority, timestamp, task_id, task_func, task_type, timeout, args, kwargs = \
                        await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Vérifier si on peut exécuter la tâche
                if not await self._can_execute_task():
                    # Remettre en queue avec délai
                    await asyncio.sleep(0.1)
                    await self.task_queue.put((priority, timestamp, task_id, task_func, task_type, timeout, args, kwargs))
                    continue
                
                # Exécuter la tâche
                await self._execute_task(task_id, task_func, task_type, timeout, args, kwargs)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)
        
        logger.info("ResourceManager worker stopped")

    async def _execute_task(self, task_id: str, task_func: Callable, task_type: str, timeout: float, args: tuple, kwargs: dict):
        """Exécute une tâche avec monitoring des ressources."""
        start_time = time.time()
        
        # Créer métriques initiales
        task_metrics = TaskMetrics(
            task_id=task_id,
            task_type=task_type,
            priority=TaskPriority.CRITICAL,  # TODO: Récupérer de la queue
            cpu_usage=0.0,
            memory_usage=0,
            duration=0.0,
            start_time=start_time,
            status="running"
        )
        
        self.active_tasks[task_id] = task_metrics
        
        try:
            logger.info(f"Executing task {task_id} ({task_type})")
            
            # Exécuter avec timeout
            result = await asyncio.wait_for(task_func(*args, **kwargs), timeout=timeout)
            
            # Tâche terminée avec succès
            end_time = time.time()
            task_metrics.end_time = end_time
            task_metrics.duration = end_time - start_time
            task_metrics.status = "completed"
            
            logger.info(f"Task {task_id} completed in {task_metrics.duration:.2f}s")
            
        except asyncio.TimeoutError:
            task_metrics.status = "timeout"
            logger.warning(f"Task {task_id} timed out after {timeout}s")
            
        except Exception as e:
            task_metrics.status = "failed"
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            
        finally:
            # Finaliser métriques
            if task_metrics.end_time is None:
                task_metrics.end_time = time.time()
                task_metrics.duration = task_metrics.end_time - start_time
            
            # Collecter métriques système finales
            system_metrics = self._collect_system_metrics()
            task_metrics.cpu_usage = system_metrics.cpu_percent
            task_metrics.memory_usage = system_metrics.memory_used_mb
            
            # Déplacer vers historique
            self.active_tasks.pop(task_id, None)
            self.task_history.append(task_metrics)
            
            # Garder seulement les 1000 dernières tâches
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-1000:]
            
            # Persister métriques dans Redis
            await self._persist_task_metrics(task_metrics)

    async def _monitoring_loop(self):
        """Boucle de monitoring des ressources système."""
        logger.info("ResourceManager monitoring started")
        
        while self.running:
            try:
                # Collecter métriques
                metrics = self._collect_system_metrics()
                
                with self.metrics_lock:
                    self.current_metrics = metrics
                
                # Vérifier surcharge
                await self._check_system_overload(metrics)
                
                # Persister métriques
                await self._persist_system_metrics(metrics)
                
                await asyncio.sleep(1.0)  # Monitoring chaque seconde
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)
        
        logger.info("ResourceManager monitoring stopped")

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collecte les métriques système actuelles."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used // (1024 * 1024),
                active_tasks=len(self.active_tasks),
                queued_tasks=self.task_queue.qsize(),
                timestamp=time.time()
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, time.time())

    async def _check_quotas(self):
        """Vérifie si les quotas permettent une nouvelle tâche."""
        metrics = await self.get_system_metrics()
        
        # Vérifier CPU
        if metrics.cpu_percent > self.quota.max_cpu_percent:
            raise ResourceExhaustedException(f"CPU usage {metrics.cpu_percent}% exceeds quota {self.quota.max_cpu_percent}%")
        
        # Vérifier mémoire
        if metrics.memory_used_mb > self.quota.max_memory_mb:
            raise ResourceExhaustedException(f"Memory usage {metrics.memory_used_mb}MB exceeds quota {self.quota.max_memory_mb}MB")
        
        # Vérifier tâches simultanées
        if metrics.active_tasks >= self.quota.max_concurrent_tasks:
            raise ResourceExhaustedException(f"Active tasks {metrics.active_tasks} exceeds quota {self.quota.max_concurrent_tasks}")
        
        # Vérifier queue
        if metrics.queued_tasks >= self.quota.max_queue_size:
            raise ResourceExhaustedException(f"Queue size {metrics.queued_tasks} exceeds quota {self.quota.max_queue_size}")

    async def _can_execute_task(self) -> bool:
        """Vérifie si on peut exécuter une nouvelle tâche."""
        try:
            await self._check_quotas()
            return not self.circuit_breaker_active
        except ResourceExhaustedException:
            return False

    async def _check_system_overload(self, metrics: SystemMetrics):
        """Vérifie la surcharge système et active le circuit breaker si nécessaire."""
        overload = False
        
        # Critères de surcharge
        if (metrics.cpu_percent > self.quota.max_cpu_percent * 1.2 or  # 20% au-dessus du quota
            metrics.memory_used_mb > self.quota.max_memory_mb * 1.2):
            overload = True
        
        if overload:
            self.circuit_breaker_count += 1
            logger.warning(f"System overload detected {self.circuit_breaker_count}/{self.circuit_breaker_threshold}")
            
            if self.circuit_breaker_count >= self.circuit_breaker_threshold:
                self.circuit_breaker_active = True
                logger.error("Circuit breaker activated - system overloaded")
                
                # Programmer réactivation dans 30 secondes
                asyncio.create_task(self._reset_circuit_breaker_after_delay(30))
        else:
            # Réinitialiser compteur si pas de surcharge
            self.circuit_breaker_count = max(0, self.circuit_breaker_count - 1)

    async def _reset_circuit_breaker_after_delay(self, delay: float):
        """Réactive le circuit breaker après un délai."""
        await asyncio.sleep(delay)
        self.circuit_breaker_active = False
        self.circuit_breaker_count = 0
        logger.info("Circuit breaker reset - system recovered")

    async def _persist_task_metrics(self, metrics: TaskMetrics):
        """Persiste les métriques de tâche dans Redis."""
        if not self.redis_client:
            return
        
        try:
            key = f"resource_manager:task_metrics:{metrics.task_id}"
            # Convertir TaskPriority en valeur sérialisable
            metrics_dict = asdict(metrics)
            metrics_dict['priority'] = metrics_dict['priority'].value  # Convertir enum en int
            await self.redis_client.setex(key, 3600, json.dumps(metrics_dict))  # 1h TTL
        except Exception as e:
            logger.warning(f"Failed to persist task metrics: {e}")

    async def _persist_system_metrics(self, metrics: SystemMetrics):
        """Persiste les métriques système dans Redis."""
        if not self.redis_client:
            return
        
        try:
            key = "resource_manager:system_metrics:current"
            await self.redis_client.setex(key, 300, json.dumps(asdict(metrics)))  # 5 min TTL
            
            # Ajouter aux séries temporelles (garder 1h de données)
            ts_key = "resource_manager:system_metrics:timeseries"
            await self.redis_client.zadd(ts_key, {json.dumps(asdict(metrics)): metrics.timestamp})
            
            # Nettoyer anciennes données (> 1h)
            cutoff_time = time.time() - 3600
            await self.redis_client.zremrangebyscore(ts_key, 0, cutoff_time)
            
        except Exception as e:
            logger.warning(f"Failed to persist system metrics: {e}")


# =================================
# EXCEPTIONS PERSONNALISÉES
# =================================

class ResourceExhaustedException(Exception):
    """Exception levée quand les quotas de ressources sont dépassés."""
    pass

class CircuitBreakerException(Exception):
    """Exception levée quand le circuit breaker est actif."""
    pass


# =================================
# FACTORY FUNCTION
# =================================

async def create_resource_manager(config=None, quota: Optional[ResourceQuota] = None) -> ResourceManager:
    """Crée et initialise un ResourceManager."""
    manager = ResourceManager(config, quota)
    await manager.__aenter__()
    return manager 