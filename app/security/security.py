import re
import logging
import time
import asyncio
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import aiohttp
import sqlite3
from dataclasses import dataclass
from app.config_v2 import get_config
from app.market.market_data import MarketDataProvider
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("security")

# Regex pour valider les adresses Solana (format Base58)
SOLANA_ADDRESS_PATTERN = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

# Password hashing context
# TODO: Consider making rounds/schemes configurable if needed via Config
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Security:
    """Handles API authentication (JWT) and password management."""

    def __init__(self):
        self.secret_key = get_config().security.jwt_secret_key
        self.algorithm = "HS256" # Standard algorithm for JWT
        self.expiration_seconds = get_config().security.jwt_expiration

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against a hashed one."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def get_password_hash(self, password: str) -> str:
        """Hashes a password."""
        return pwd_context.hash(password)

    def create_token(self, data: dict) -> str:
        """Creates a JWT token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(seconds=self.expiration_seconds)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Tuple[bool, str]:
        """Verifies a JWT token. Corresponds to task 1.6 requirement for API auth.
        Returns (is_valid, message_or_userid).
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # For now, just confirming token is valid and not expired.
            # logger.info(f"Token valid for user_id: {payload.get('user_id')}")
            return True, payload.get("user_id", "Token valid") # Or return payload itself if needed
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return False, "Token has expired"
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return False, "Invalid token"
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False, "Token verification failed"

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
           retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))) # Keep retry if MDP call might be retried for network issues
    async def _check_token_age_and_history(self, token_address: str) -> List[SecurityRisk]:
        """
        Vérifie l'âge et l'historique du token en utilisant MarketDataProvider.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        try:
            if not self.market_data:
                logger.warning("MarketDataProvider non disponible dans SecurityChecker pour _check_token_age_and_history.")
                risks.append(SecurityRisk(
                    risk_type="config_error",
                    severity=5,
                    description="MarketDataProvider non configuré pour vérifier l'âge du token.",
                    metadata={"token_address": token_address}
                ))
                return risks

            token_info_response = await self.market_data.get_token_info(token_address)
            
            if not token_info_response['success']:
                error_msg = f"Échec de la récupération des informations du token pour l'âge/historique: {token_info_response.get('error', 'Erreur inconnue de MarketDataProvider')}"
                logger.warning(f"{error_msg} (Token: {token_address})")
                risks.append(SecurityRisk(
                    risk_type="token_info_unavailable_age_check",
                    severity=4,
                    description="Impossible de récupérer les informations du token pour vérifier l'âge.",
                    metadata={"address": token_address, "source_error": token_info_response.get('error')}
                ))
                return risks # Cannot proceed without token info

            token_info_data = token_info_response['data']
            if not token_info_data:
                logger.warning(f"Aucune donnée d'information de token retournée par MarketDataProvider pour {token_address} lors de la vérification de l'âge.")
                risks.append(SecurityRisk(
                    risk_type="empty_token_info_age_check",
                    severity=4,
                    description="Données d'information de token vides reçues.",
                    metadata={"address": token_address}
                ))
                return risks

            # Vérifier l'âge du token à partir des données de MarketDataProvider
            # Assumons que MarketDataProvider pourrait fournir 'created_at' ou un champ similaire.
            # Si Jupiter /token-list est utilisé, il n'y a pas de `created_at`. DexScreener non plus directement.
            # Ce champ est donc hypothétique pour l'instant ou nécessite une source dédiée.
            # Pour la démo, nous allons simuler sa présence potentielle ou son absence.
            created_at_timestamp = token_info_data.get("created_at") # Hypothetical field
            # Alternative: check for 'first_seen_timestamp' or similar if available from source

            if created_at_timestamp:
                try:
                    token_age_seconds = time.time() - float(created_at_timestamp)
                    token_age_days = token_age_seconds / (60 * 60 * 24)
                    if token_age_days < 1:
                        risks.append(SecurityRisk(
                            risk_type="new_token_daily", # More specific type
                            severity=7,
                            description=f"Token créé il y a moins de 24 heures ({token_age_days:.1f} heures)",
                            metadata={"age_days": token_age_days, "created_at": created_at_timestamp}
                        ))
                    elif token_age_days < 7:
                        risks.append(SecurityRisk(
                            risk_type="new_token_weekly", # More specific type
                            severity=4,
                            description=f"Token créé il y a moins d'une semaine ({token_age_days:.1f} jours)",
                            metadata={"age_days": token_age_days, "created_at": created_at_timestamp}
                        ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Timestamp de création invalide '{created_at_timestamp}' pour {token_address}: {e}")
                    risks.append(SecurityRisk(
                        risk_type="invalid_creation_timestamp",
                        severity=3,
                        description="Timestamp de création du token invalide ou manquant.",
                        metadata={"address": token_address, "timestamp_value": str(created_at_timestamp)}
                    ))
            else:
                logger.info(f"Aucun timestamp de création explicite ('created_at') trouvé pour {token_address} dans les données de get_token_info.")
                # On pourrait ajouter un risque mineur ou une note si ce champ est attendu mais absent
                risks.append(SecurityRisk(
                    risk_type="creation_date_unknown",
                    severity=2, # Low severity, as it's informational
                    description="Date de création du token non disponible via get_token_info.",
                    metadata={"address": token_address, "token_info_keys": list(token_info_data.keys())}
                ))
            
            # Autres vérifications historiques (e.g., analyse de transactions) pourraient suivre ici
            # en utilisant self._get_recent_transactions(token_address)
            # Pour l'instant, cette méthode se concentre sur l'info de base du token.
            
            return risks
            
        except Exception as e:
            # This catches unexpected errors within this method's logic itself, 
            # not API errors from MDP which are handled above.
            logger.error(f"Erreur inattendue lors de la vérification de l'âge et l'historique du token {token_address}: {e}", exc_info=True)
            risks.append(SecurityRisk(
                risk_type="age_history_check_internal_error",
                severity=5, # Higher severity for internal errors
                description=f"Erreur interne lors de la vérification de l'âge/historique: {str(e)}",
                metadata={"address": token_address, "error_type": type(e).__name__}
            ))
            return risks

    async def _analyze_holder_distribution(self, token_address: str) -> List[SecurityRisk]:
        """
        Analyse la distribution des détenteurs du token.
        Utilise _get_token_holders qui retourne une réponse structurée.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        try:
            holder_response = await self._get_token_holders(token_address)
            
            if not holder_response['success']:
                error_msg = f"Impossible d'analyser la distribution des détenteurs car les données n'ont pas pu être récupérées: {holder_response.get('error')}"
                logger.warning(f"{error_msg} (Token: {token_address})")
                risks.append(SecurityRisk(
                    risk_type="holder_data_unavailable_for_analysis",
                    severity=3, # Severity might depend on how critical this check is
                    description="Données sur les détenteurs non disponibles pour l'analyse.",
                    metadata={"address": token_address, "source_error": holder_response.get('error')}
                ))
                return risks

            holder_data = holder_response['data'] # This should be like {"holders": [...]} 
            if not holder_data or "holders" not in holder_data or not isinstance(holder_data["holders"], list):
                logger.warning(f"Format de données des détenteurs invalide ou vide reçu de _get_token_holders pour {token_address}: {holder_data}")
                risks.append(SecurityRisk(
                    risk_type="invalid_holder_data_format",
                    severity=3,
                    description="Format de données des détenteurs invalide ou vide.",
                    metadata={"address": token_address, "received_data": holder_data}
                ))
                return risks
                
            holders = holder_data["holders"]
            if not holders: # Explicitly check for empty list of holders
                logger.info(f"Aucun détenteur retourné pour {token_address}. L'analyse de la distribution sera limitée.")
                # Depending on policy, this might be a minor risk or just an observation.
                # risks.append(SecurityRisk(...)) 
                # For now, proceed, concentration checks won't trigger.

            # Calculer la concentration de possession
            if holders: # Proceed only if holders list is not empty
                # Calculer le pourcentage détenu par le plus grand détenteur (non vérifié)
                # Ensure items in holders are dicts and have expected keys before accessing
                valid_holders_for_max = []
                for h_idx, h in enumerate(holders):
                    if isinstance(h, dict) and "percentage" in h:
                        valid_holders_for_max.append(h)
                    else:
                        logger.warning(f"Invalid holder entry at index {h_idx} for {token_address}: {h}. Skipping.")
                
                non_verified_holders = [h for h in valid_holders_for_max if not h.get("is_verified", False)]
                
                if non_verified_holders:
                    try:
                        largest_holder = max(non_verified_holders, key=lambda h_item: h_item.get("percentage", 0))
                        largest_percentage = largest_holder.get("percentage", 0)
                        
                        # Ensure percentage is a float or int before comparison
                        if not isinstance(largest_percentage, (float, int)):
                            logger.warning(f"Largest holder percentage is not a number for {token_address}: {largest_percentage}. Skipping concentration check.")
                        elif largest_percentage > get_config().HOLDER_CONCENTRATION_THRESHOLD_HIGH: # Use Config value
                            risks.append(SecurityRisk(
                                risk_type="high_concentration",
                                severity=8,
                                description=f"Un seul détenteur non vérifié possède {largest_percentage*100:.1f}% des tokens",
                                metadata={"holder_address": largest_holder.get("address"), "percentage": largest_percentage}
                            ))
                        elif largest_percentage > get_config().HOLDER_CONCENTRATION_THRESHOLD_MEDIUM: # Use Config value
                            risks.append(SecurityRisk(
                                risk_type="medium_concentration",
                                severity=5,
                                description=f"Un seul détenteur non vérifié possède {largest_percentage*100:.1f}% des tokens",
                                metadata={"holder_address": largest_holder.get("address"), "percentage": largest_percentage}
                            ))
                    except ValueError: # max() on empty sequence
                        logger.info(f"Aucun détenteur non vérifié trouvé pour {token_address} pour calculer la concentration max.")
                else:
                     logger.info(f"Aucun détenteur non vérifié (ou aucun détenteur avec 'percentage') trouvé pour {token_address} pour l'analyse de concentration.")
                
                # Calculer le nombre de détenteurs
                holder_count = len(holders) # Total holders including verified/unverified, valid/invalid entries filtered above might differ
                if holder_count < get_config().MIN_HOLDERS_COUNT_THRESHOLD: # Use Config value
                    risks.append(SecurityRisk(
                        risk_type="few_holders",
                        severity=6,
                        description=f"Le token n'a que {holder_count} détenteurs (Seuil: {get_config().MIN_HOLDERS_COUNT_THRESHOLD})",
                        metadata={"holder_count": holder_count}
                    ))
            else: # Case where holders list was initially empty
                risks.append(SecurityRisk(
                    risk_type="no_holders_data",
                    severity=3,
                    description=f"Aucune donnée de détenteur trouvée pour le token {token_address} pour l'analyse.",
                    metadata={"address": token_address}
                ))
            
            return risks
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'analyse des détenteurs pour {token_address}: {e}", exc_info=True)
            risks.append(SecurityRisk(
                risk_type="holder_analysis_internal_error",
                severity=4,
                description=f"Erreur interne lors de l'analyse des détenteurs: {str(e)}",
                metadata={"address": token_address, "error": str(e), "error_type": type(e).__name__}
            ))
            return risks

    async def _get_onchain_metrics(self, token_address: str) -> List[SecurityRisk]:
        """
        Analyse les métriques on-chain du token, y compris les informations sur le token et la liquidité.
        Utilise MarketDataProvider pour obtenir les données.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés liés aux métriques on-chain.
        """
        risks = []
        try:
            if not self.market_data:
                logger.warning("MarketDataProvider non disponible dans SecurityChecker pour _get_onchain_metrics.")
                risks.append(SecurityRisk(
                    risk_type="config_error_metrics", # More specific risk type
                    severity=5, # Adjusted severity
                    description="MarketDataProvider non configuré pour récupérer les métriques on-chain.",
                    metadata={"token_address": token_address}
                ))
                return risks # Cannot proceed without market_data

            # 1. Obtenir les informations générales du token
            token_info_result = await self.market_data.get_token_info(token_address)
            if not token_info_result['success']:
                error_msg = f"Échec de la récupération des informations du token {token_address} pour les métriques on-chain: {token_info_result.get('error', 'Erreur inconnue de MDP')}"
                logger.warning(error_msg)
                risks.append(SecurityRisk(
                    risk_type="token_info_fetch_failed_metrics",
                    severity=5,
                    description=error_msg,
                    metadata={"token_address": token_address, "source_error": token_info_result.get('error'), "raw_response": token_info_result.get('data')}
                ))
            else:
                token_info = token_info_result['data']
                if not token_info: # data can be None even if success is true, if API returns empty valid response
                    logger.warning(f"Aucune information de token (data est None/vide) retournée pour {token_address} par MDP.")
                    risks.append(SecurityRisk(
                        risk_type="empty_token_info_metrics",
                        severity=5,
                        description=f"Aucune information de token (data est None/vide) retournée pour {token_address} malgré une réponse réussie de MDP.",
                        metadata={"token_address": token_address}
                    ))
                else:
                    # Exemple d'analyse des informations du token
                    if not token_info.get('name') or not token_info.get('symbol'):
                        risks.append(SecurityRisk(
                            risk_type="missing_token_metadata_metrics",
                            severity=3,
                            description=f"Nom ou symbole manquant pour le token {token_address} dans les données de MDP.",
                            metadata={"token_address": token_address, "retrieved_info": token_info}
                        ))
                    # Add other checks on token_info if necessary, e.g., token_info.get('decimals') etc.
            
            # 2. Obtenir et analyser les données de liquidité
            liquidity_data_result = await self.market_data.get_liquidity_data(token_address)
            
            if not liquidity_data_result['success']:
                error_msg = f"Échec de la récupération des données de liquidité pour {token_address} pour les métriques on-chain: {liquidity_data_result.get('error', 'Erreur inconnue de MDP')}"
                logger.warning(error_msg)
                risks.append(SecurityRisk(
                    risk_type="liquidity_data_fetch_failed_metrics",
                    severity=7, # Higher severity as liquidity is crucial
                    description=error_msg,
                    metadata={"token_address": token_address, "source_error": liquidity_data_result.get('error'), "raw_response": liquidity_data_result.get('data')}
                ))
            else:
                liquidity_info = liquidity_data_result['data']
                if not liquidity_info or liquidity_info.get("liquidity_usd") is None:
                    logger.warning(f"Données de liquidité vides ou invalides (USD manquant) pour {token_address} de MDP: {liquidity_info}")
                    risks.append(SecurityRisk(
                        risk_type="empty_or_invalid_liquidity_data_metrics",
                        severity=6,
                        description=f"Données de liquidité vides ou invalides pour {token_address}. Liquidité USD manquante ou donnée None.",
                        metadata={"token_address": token_address, "retrieved_liquidity_info": liquidity_info}
                    ))
                else:
                    # Ensure liquidity_usd is float, default to 0 if conversion fails
                    try:
                        usd_liquidity = float(liquidity_info.get("liquidity_usd", 0))
                    except (ValueError, TypeError):
                        logger.warning(f"Impossible de convertir liquidity_usd en float pour {token_address}. Valeur: {liquidity_info.get('liquidity_usd')}. Utilisation de 0.")
                        usd_liquidity = 0.0
                        risks.append(SecurityRisk(
                            risk_type="invalid_liquidity_usd_format",
                            severity=4,
                            description="Format de liquidity_usd invalide.",
                            metadata={"token_address": token_address, "original_value": liquidity_info.get('liquidity_usd') }
                        ))

                    logger.info(f"Liquidité pour {token_address} (métriques on-chain): ${usd_liquidity:.2f} USD")

                    if usd_liquidity < get_config().MIN_LIQUIDITY_THRESHOLD_ERROR:
                        risks.append(SecurityRisk(
                            risk_type="critically_low_liquidity_metrics",
                            severity=9,
                            description=f"Liquidité critique (métriques): ${usd_liquidity:.2f} USD (Seuil: ${get_config().MIN_LIQUIDITY_THRESHOLD_ERROR}).",
                            metadata={"liquidity_usd": usd_liquidity, "threshold": get_config().MIN_LIQUIDITY_THRESHOLD_ERROR}
                        ))
                    elif usd_liquidity < get_config().MIN_LIQUIDITY_THRESHOLD_WARNING:
                        risks.append(SecurityRisk(
                            risk_type="low_liquidity_warning_metrics",
                            severity=6,
                            description=f"Faible liquidité (métriques): ${usd_liquidity:.2f} USD (Seuil avertissement: ${get_config().MIN_LIQUIDITY_THRESHOLD_WARNING}).",
                            metadata={"liquidity_usd": usd_liquidity, "threshold": get_config().MIN_LIQUIDITY_THRESHOLD_WARNING}
                        ))
                    
                    # TODO: Further liquidity depth analysis if data is available and structured for it.
                    # e.g., if liquidity_info contains depth information.
            
            # 3. Placeholder: Add calls to _get_recent_transactions if needed for other on-chain metrics
            # transaction_response = await self._get_recent_transactions(token_address)
            # if transaction_response['success'] and transaction_response['data']:
            #     # Analyze transactions for metrics like volume, unique addresses, etc.
            #     pass
            # else:
            #     logger.warning(f"Could not get transactions for on-chain metrics for {token_address}: {transaction_response.get('error')}")
            #     risks.append(SecurityRisk(...))

            return risks
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'analyse des métriques on-chain pour {token_address}: {str(e)}", exc_info=True)
            risks.append(SecurityRisk(
                risk_type="onchain_metrics_internal_error", # Specific internal error type
                severity=5,
                description=f"Erreur interne inattendue lors de l'analyse des métriques on-chain: {str(e)}",
                metadata={"token_address": token_address, "error_type": type(e).__name__, "error_details": str(e)}
            ))
            return risks

    async def _detect_rugpull_patterns(self, token_address: str) -> List[SecurityRisk]:
        """
        Détecte les modèles sophistiqués de rug pull en utilisant les données de MarketDataProvider.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        price_history_data: Optional[List[Dict[str, Any]]] = None
        transaction_history_data: Optional[List[Dict[str, Any]]] = None
        liquidity_history_data: Optional[List[Dict[str, Any]]] = None
        data_fetch_errors = False

        try:
            if not self.market_data:
                logger.warning("MarketDataProvider non disponible pour _detect_rugpull_patterns.")
                risks.append(SecurityRisk(
                    risk_type="config_error_rugpull", 
                    severity=5,
                    description="MarketDataProvider non configuré pour la détection de rugpull.",
                    metadata={"token_address": token_address}
                ))
                return risks
                
            # 1. Obtenir l'historique des prix
            # get_historical_prices from MDP already returns structured response
            price_response = await self.market_data.get_historical_prices(token_address, timeframe=get_config().RUGPULL_PRICE_TIMEFRAME, limit=get_config().RUGPULL_PRICE_LIMIT)
            if price_response['success'] and price_response['data'] is not None:
                price_history_data = price_response['data']
            else:
                data_fetch_errors = True
                logger.warning(f"Échec de la récupération de l'historique des prix pour {token_address} (rugpull detection): {price_response.get('error')}")
                risks.append(SecurityRisk(
                    risk_type="price_history_unavailable_rugpull",
                    severity=3, # Severity might be adjusted based on how critical this is
                    description="Historique des prix non disponible pour l'analyse de rugpull.",
                    metadata={"token_address": token_address, "source_error": price_response.get('error')}
                ))

            # 2. Obtenir les transactions récentes
            transaction_response = await self._get_recent_transactions(token_address, limit=get_config().RUGPULL_TRANSACTION_LIMIT)
            if transaction_response['success'] and transaction_response['data'] is not None:
                transaction_history_data = transaction_response['data']
            else:
                data_fetch_errors = True
                logger.warning(f"Échec de la récupération de l'historique des transactions pour {token_address} (rugpull detection): {transaction_response.get('error')}")
                risks.append(SecurityRisk(
                    risk_type="transaction_history_unavailable_rugpull",
                    severity=3,
                    description="Historique des transactions non disponible pour l'analyse de rugpull.",
                    metadata={"token_address": token_address, "source_error": transaction_response.get('error')}
                ))

            # 3. Obtenir l'historique de liquidité
            liquidity_hist_response = await self._get_liquidity_history(token_address, timeframe=get_config().RUGPULL_LIQUIDITY_TIMEFRAME, limit=get_config().RUGPULL_LIQUIDITY_LIMIT)
            if liquidity_hist_response['success'] and liquidity_hist_response['data'] is not None:
                liquidity_history_data = liquidity_hist_response['data']
            else:
                data_fetch_errors = True
                logger.warning(f"Échec de la récupération de l'historique de liquidité pour {token_address} (rugpull detection): {liquidity_hist_response.get('error')}")
                risks.append(SecurityRisk(
                    risk_type="liquidity_history_unavailable_rugpull",
                    severity=4, # Slightly higher as liquidity is key for rugpulls
                    description="Historique de liquidité non disponible pour l'analyse de rugpull.",
                    metadata={"token_address": token_address, "source_error": liquidity_hist_response.get('error')}
                ))
            
            # 4. Obtenir les détenteurs de tokens (pour l'analyse du comportement des gros portefeuilles)
            # Note: get_config().SECURITY_MAX_HOLDERS_TO_FETCH est utilisé par _get_token_holders
            # Cela peut être un appel coûteux, à utiliser judicieusement.
            token_holders_response = await self._get_token_holders(token_address) # _get_token_holders gère sa propre limite via Config
            token_holders_data: Optional[Dict[str, Any]] = None
            if token_holders_response['success'] and token_holders_response['data'] is not None:
                token_holders_data = token_holders_response['data'] # {'total_holders': int, 'top_holders': [{'address': str, 'pct_supply': float, 'ui_amount': float}]}
            else:
                # Not necessarily a data_fetch_error that stops all analysis, but a warning for specific checks.
                logger.warning(f"Échec de la récupération des détenteurs de tokens pour {token_address} (rugpull detection): {token_holders_response.get('error')}")
                risks.append(SecurityRisk(
                    risk_type="holder_data_unavailable_rugpull",
                    severity=2, # Lower severity, as other checks can proceed
                    description="Données des détenteurs non disponibles pour l'analyse de comportement.",
                    metadata={"token_address": token_address, "source_error": token_holders_response.get('error')}
                ))
            
            # Analyse des variations de prix soudaines
            if price_history_data and len(price_history_data) > 1: # Need at least 2 points to compare
                price_changes = []
                for i in range(1, len(price_history_data)):
                    prev_candle = price_history_data[i-1]
                    curr_candle = price_history_data[i]
                    # Ensure data is valid and keys exist
                    prev_price = prev_candle.get("close") # Using close price
                    curr_price = curr_candle.get("close")

                    if prev_price is not None and curr_price is not None and isinstance(prev_price, (float, int)) and isinstance(curr_price, (float, int)) and prev_price > 0:
                        try:
                            change = (float(curr_price) - float(prev_price)) / float(prev_price)
                            price_changes.append(change)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error calculating price change for {token_address}: prev={prev_price}, curr={curr_price}. Error: {e}")
                    elif prev_price == 0:
                        logger.debug(f"Previous price is 0, cannot calculate change for {token_address} at index {i-1}")
                
                if price_changes:
                    max_drop = min(price_changes) # min will find the largest negative change
                    if max_drop < get_config().RUGPULL_PRICE_DROP_THRESHOLD:  # e.g., -0.5 for 50% drop
                        risks.append(SecurityRisk(
                            risk_type="significant_price_drop", # More specific
                            severity=8,
                            description=f"Chute de prix brutale détectée: {max_drop*100:.1f}% en {get_config().RUGPULL_PRICE_TIMEFRAME} intervalle.",
                            metadata={"max_drop_percentage": max_drop, "timeframe": get_config().RUGPULL_PRICE_TIMEFRAME}
                        ))
            elif not price_history_data and not data_fetch_errors: # Data fetch was successful but list is empty/too short
                 logger.info(f"Historique des prix pour {token_address} est vide ou insuffisant pour l'analyse de chute de prix.")

            # Analyser les retraits de liquidité
            if liquidity_history_data and len(liquidity_history_data) > 1:
                recent_liquidity_changes = []
                # Ensure data is sorted by timestamp if not already (MDP should handle)
                for i in range(1, len(liquidity_history_data)):
                    prev_liq_point = liquidity_history_data[i-1]
                    curr_liq_point = liquidity_history_data[i]
                    prev_liq_usd = prev_liq_point.get("liquidity_usd")
                    curr_liq_usd = curr_liq_point.get("liquidity_usd")

                    if prev_liq_usd is not None and curr_liq_usd is not None and isinstance(prev_liq_usd, (float, int)) and isinstance(curr_liq_usd, (float, int)) and prev_liq_usd > 0:
                        try:
                            change = (float(curr_liq_usd) - float(prev_liq_usd)) / float(prev_liq_usd)
                            recent_liquidity_changes.append(change)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error calculating liquidity change for {token_address}: prev={prev_liq_usd}, curr={curr_liq_usd}. Error: {e}")
                    elif prev_liq_usd == 0:
                         logger.debug(f"Previous liquidity is 0, cannot calculate change for {token_address} at index {i-1}")
                
                if recent_liquidity_changes:
                    # Check for a large drop within a short recent window, e.g., last few data points
                    # For simplicity, checking overall min drop in the fetched history for now.
                    # More sophisticated: analyze drops in rolling windows or specifically recent ones.
                    largest_drop = min(recent_liquidity_changes) # min will find the largest negative change
                    if largest_drop < get_config().RUGPULL_LIQUIDITY_DROP_THRESHOLD:  # e.g., -0.3 for 30% drop
                        risks.append(SecurityRisk(
                            risk_type="significant_liquidity_drop", # More specific
                            severity=9,
                            description=f"Retrait important de liquidité détecté: {largest_drop*100:.1f}% en {get_config().RUGPULL_LIQUIDITY_TIMEFRAME} intervalle.",
                            metadata={"liquidity_drop_percentage": largest_drop, "timeframe": get_config().RUGPULL_LIQUIDITY_TIMEFRAME}
                        ))
            elif not liquidity_history_data and not data_fetch_errors:
                logger.info(f"Historique de liquidité pour {token_address} est vide ou insuffisant pour l'analyse de retrait.")
            
            # Analyser les transactions pour détecter des modèles suspects
            if transaction_history_data: # Check if data was successfully fetched
                if self._detect_wash_trading(transaction_history_data):
                    risks.append(SecurityRisk(
                        risk_type="wash_trading_detected", # More specific
                        severity=7,
                        description="Modèle de wash trading potentiellement détecté.",
                        metadata={"transaction_count": len(transaction_history_data)}
                    ))
                
                if self._detect_exchange_transfers(transaction_history_data):
                    risks.append(SecurityRisk(
                        risk_type="large_exchange_transfers_detected", # More specific
                        severity=6,
                        description="Transferts importants vers des adresses d'échange potentiellement détectés.",
                        metadata={"transaction_count": len(transaction_history_data)}
                    ))
                
                # Analyse de la vélocité des transferts
                velocity_risks = self._analyze_transaction_velocity(transaction_history_data, token_address)
                risks.extend(velocity_risks)

                # Analyse du comportement des gros portefeuilles (utilisant token_holders_data et transaction_history_data)
                large_holder_risks = self._analyze_large_holder_activity(transaction_history_data, token_holders_data, token_address)
                risks.extend(large_holder_risks)

            elif not transaction_history_data and not data_fetch_errors: # data_fetch_errors for transactions already logged
                 logger.info(f"Historique des transactions pour {token_address} est vide pour l'analyse de modèles avancés.")
            
            return risks
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la détection de modèles de rug pull pour {token_address}: {e}", exc_info=True)
            risks.append(SecurityRisk(
                risk_type="rugpull_detection_internal_error", # Specific internal error type
                severity=5, # Adjusted severity for internal errors
                description=f"Erreur interne lors de la détection de modèles de rug pull: {str(e)}",
                metadata={"token_address": token_address, "error_type": type(e).__name__, "error_details": str(e)}
            ))
            return risks

    def _analyze_transaction_velocity(self, transactions: List[Dict[str, Any]], token_address: str) -> List[SecurityRisk]:
        risks = []
        # TODO: Implement more sophisticated velocity analysis
        # - Look for sudden spikes in transaction volume or count.
        # - Consider transaction sizes relative to total supply or liquidity.
        # - Requires careful definition of "normal" vs "abnormal" velocity.
        
        if not transactions:
            return risks

        now = time.time()
        recent_tx_count = 0
        one_hour_ago = now - 3600
        
        for tx in transactions:
            if tx.get("blockTime") and tx["blockTime"] > one_hour_ago:
                recent_tx_count += 1
        
        HIGH_VELOCITY_TX_COUNT_THRESHOLD = getattr(Config, 'HIGH_VELOCITY_TX_COUNT_THRESHOLD', 100)

        if recent_tx_count > HIGH_VELOCITY_TX_COUNT_THRESHOLD:
            risks.append(SecurityRisk(
                risk_type="high_recent_transaction_velocity",
                severity=5,
                description=f"Volume de transactions élevé détecté récemment: {recent_tx_count} transactions dans la dernière heure (ou depuis le début des données fournies).",
                metadata={"recent_transaction_count": recent_tx_count, "threshold": HIGH_VELOCITY_TX_COUNT_THRESHOLD, "token_address": token_address}
            ))
            logger.info(f"High transaction velocity detected for {token_address}: {recent_tx_count} txns in last hour (approx).")

        return risks

    def _analyze_large_holder_activity(self, transactions: List[Dict[str, Any]], 
                                     token_holders_data: Optional[Dict[str, Any]], 
                                     token_address: str) -> List[SecurityRisk]:
        risks = []
        # TODO: Implement more sophisticated large holder activity analysis
        
        if not transactions or not token_holders_data or not token_holders_data.get('top_holders'):
            logger.debug(f"Données insuffisantes pour l'analyse de l'activité des gros détenteurs pour {token_address}.")
            return risks

        top_holders_list = token_holders_data.get('top_holders', [])
        if not top_holders_list:
            return risks

        NUM_TOP_HOLDERS_TO_ANALYZE = getattr(Config, 'NUM_TOP_HOLDERS_TO_ANALYZE', 5)
        MIN_PCT_SALE_BY_TOP_HOLDER = getattr(Config, 'MIN_PCT_SALE_BY_TOP_HOLDER', 0.5)

        # Make a copy to modify if needed (for avoiding duplicate alerts for same holder)
        top_n_holder_addresses_to_check = {holder['address'] for holder in top_holders_list[:NUM_TOP_HOLDERS_TO_ANALYZE]}

        for tx in transactions:
            source_owner = tx.get('source_owner')
            destination_owner = tx.get('destination_owner') # Useful for context, e.g. not another top holder or CEX
            ui_amount_transfer = tx.get('ui_amount')

            if source_owner in top_n_holder_addresses_to_check and ui_amount_transfer is not None:
                original_holder_info = next((h for h in top_holders_list if h['address'] == source_owner), None)
                if original_holder_info and original_holder_info.get('ui_amount', 0) > 0:
                    try:
                        transfer_amount_float = float(ui_amount_transfer)
                        original_holding_float = float(original_holder_info['ui_amount'])
                        
                        if original_holding_float > 0 and (transfer_amount_float / original_holding_float) >= MIN_PCT_SALE_BY_TOP_HOLDER:
                            risks.append(SecurityRisk(
                                risk_type="large_sale_by_top_holder",
                                severity=7,
                                description=f"Vente potentiellement importante ({transfer_amount_float} tokens, >= {MIN_PCT_SALE_BY_TOP_HOLDER*100:.0f}%) par un gros détenteur ({source_owner}).",
                                metadata={
                                    "holder_address": source_owner, 
                                    "transfer_amount": transfer_amount_float,
                                    "original_reported_holding": original_holding_float,
                                    "token_address": token_address,
                                    "destination": destination_owner,
                                    "transaction_signature": tx.get("signature") # Log signature for reference
                                 }
                            ))
                            logger.info(f"Potential large sale by top holder {source_owner} (tx: {tx.get('signature')}) for token {token_address}.")
                            top_n_holder_addresses_to_check.remove(source_owner) 
                            if not top_n_holder_addresses_to_check: break 
                    except ValueError:
                        logger.debug(f"Could not parse amounts for large holder sale analysis: {ui_amount_transfer}, {original_holder_info.get('ui_amount')}")
        return risks

    async def _analyze_liquidity_depth(self, token_address: str) -> List[SecurityRisk]:
        """
        Analyse la profondeur de la liquidité pour détecter des manipulations.
        Utilise MarketDataProvider.get_liquidity_data.
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Liste des risques détectés
        """
        risks = []
        try:
            if not self.market_data:
                logger.warning("MarketDataProvider non disponible pour _analyze_liquidity_depth.")
                risks.append(SecurityRisk(
                    risk_type="config_error_depth_analysis",
                    severity=5,
                    description="MarketDataProvider non configuré pour l'analyse de profondeur de liquidité.",
                    metadata={"token_address": token_address}
                ))
                return risks
                
            liquidity_response = await self.market_data.get_liquidity_data(token_address)
            
            if not liquidity_response['success']:
                error_msg = f"Impossible d'obtenir les données de liquidité pour l'analyse de profondeur: {liquidity_response.get('error', 'Erreur inconnue de MDP')}"
                logger.warning(f"{error_msg} (Token: {token_address})")
                risks.append(SecurityRisk(
                    risk_type="liquidity_data_unavailable_depth",
                    severity=4, # Severity might depend on how critical depth analysis is
                    description="Données de liquidité non disponibles pour l'analyse de profondeur.",
                    metadata={"token_address": token_address, "source_error": liquidity_response.get('error')}
                ))
                return risks

            liquidity_data = liquidity_response['data']
            if not liquidity_data:
                logger.warning(f"Données de liquidité vides (None) reçues de MDP pour {token_address} pour l'analyse de profondeur.")
                risks.append(SecurityRisk(
                    risk_type="empty_liquidity_data_depth",
                    severity=3,
                    description="Données de liquidité vides (None) pour l'analyse de profondeur.",
                    metadata={"token_address": token_address}
                ))
                return risks
            
            # MarketDataProvider.get_liquidity_data returns a flat dict primarily from _convert_dexscreener_format.
            # Actual order book depth ("depth_levels") would typically be in liquidity_data['raw_data'] 
            # if the source (e.g., DexScreener pair) provides it, or from a dedicated order book endpoint.
            # Let's assume the structure might be nested or require specific parsing from raw_data.
            # For this example, we'll hypothesize 'depth_levels' might exist in the returned 'data' or its 'raw_data'.
            
            depth_levels: Optional[List[Dict[str, Any]]] = None
            if isinstance(liquidity_data.get('raw_data'), dict):
                # Example: DexScreener specific path if depth is in raw_data.pairs[0].orderBook (hypothetical)
                # This needs to align with actual data structure from the API source via MDP
                # For now, a generic check:
                depth_levels = liquidity_data['raw_data'].get("depth_levels") # Or any other agreed upon key from MDP
            
            if not depth_levels and isinstance(liquidity_data, dict): # Fallback or direct key
                 depth_levels = liquidity_data.get("depth_levels")

            if not depth_levels or not isinstance(depth_levels, list):
                logger.info(f"Aucune donnée de 'depth_levels' trouvée ou format invalide pour {token_address} dans les données de liquidité. Profondeur non analysée.")
                # Not necessarily a high-severity risk, could be informational
                risks.append(SecurityRisk(
                    risk_type="depth_data_absent_or_invalid",
                    severity=2,
                    description="Données de 'depth_levels' non disponibles ou format invalide pour l'analyse.",
                    metadata={"token_address": token_address, "liquidity_data_keys": list(liquidity_data.keys()) if isinstance(liquidity_data, dict) else None}
                ))
                return risks # Cannot perform depth analysis without depth_levels
            
            # Analyser les niveaux de profondeur
            if depth_levels: # Should be true if we haven't returned above
                buy_orders = []
                sell_orders = []
                for level_idx, level in enumerate(depth_levels):
                    if not isinstance(level, dict) or "side" not in level or "price" not in level or "size" not in level:
                        logger.warning(f"Niveau de profondeur invalide à l'index {level_idx} pour {token_address}: {level}. Ignoré.")
                        continue
                    if level["side"] == "buy":
                        buy_orders.append(level)
                    elif level["side"] == "sell":
                        sell_orders.append(level)
                
                # Calculer le volume total des ordres
                buy_volume = sum(float(level["size"]) * float(level["price"]) for level in buy_orders if isinstance(level.get("size"), (int, float)) and isinstance(level.get("price"), (int, float)))
                sell_volume = sum(float(level["size"]) * float(level["price"]) for level in sell_orders if isinstance(level.get("size"), (int, float)) and isinstance(level.get("price"), (int, float)))
                
                # Calculer le ratio d'asymétrie
                total_volume = buy_volume + sell_volume
                if total_volume > 0:
                    asymmetry_ratio = abs(buy_volume - sell_volume) / total_volume
                    
                    if asymmetry_ratio > get_config().LIQUIDITY_ASYMMETRY_THRESHOLD_SEVERE: # Use Config
                        risks.append(SecurityRisk(
                            risk_type="severe_liquidity_asymmetry",
                            severity=8,
                            description=f"Asymétrie sévère de la liquidité: {asymmetry_ratio*100:.1f}%",
                            metadata={"asymmetry_ratio": asymmetry_ratio, "buy_volume_usd": buy_volume, "sell_volume_usd": sell_volume}
                        ))
                    elif asymmetry_ratio > get_config().LIQUIDITY_ASYMMETRY_THRESHOLD_MODERATE: # Use Config
                        risks.append(SecurityRisk(
                            risk_type="moderate_liquidity_asymmetry",
                            severity=5,
                            description=f"Asymétrie modérée de la liquidité: {asymmetry_ratio*100:.1f}%",
                            metadata={"asymmetry_ratio": asymmetry_ratio, "buy_volume_usd": buy_volume, "sell_volume_usd": sell_volume}
                        ))
                else:
                    logger.info(f"Volume total nul pour les ordres de profondeur pour {token_address}. Asymétrie non calculée.")
                
                # Calculer l'impact de prix pour différentes tailles d'ordres
                # Ensure sell_orders are sorted by price ascending for price impact calculation
                # (MarketDataProvider should ideally provide sorted data if it comes from an order book source)
                sorted_sell_orders = sorted([o for o in sell_orders if isinstance(o.get("price"), (int, float))], key=lambda x: float(x["price"])) 

                if sorted_sell_orders:
                    price_impact_1k = self._calculate_price_impact(sorted_sell_orders, get_config().PRICE_IMPACT_USD_AMOUNT_1K)
                    if price_impact_1k > get_config().PRICE_IMPACT_THRESHOLD_HIGH_1K: 
                        risks.append(SecurityRisk(
                            risk_type="high_price_impact_1k",
                            severity=6,
                            description=f"Impact de prix élevé pour {get_config().PRICE_IMPACT_USD_AMOUNT_1K} USD: {price_impact_1k*100:.2f}%",
                            metadata={"price_impact_usd": get_config().PRICE_IMPACT_USD_AMOUNT_1K, "impact_percentage": price_impact_1k}
                        ))
                    
                    price_impact_10k = self._calculate_price_impact(sorted_sell_orders, get_config().PRICE_IMPACT_USD_AMOUNT_10K)
                    if price_impact_10k > get_config().PRICE_IMPACT_THRESHOLD_HIGH_10K:
                        risks.append(SecurityRisk(
                            risk_type="high_price_impact_10k",
                            severity=7,
                            description=f"Impact de prix élevé pour {get_config().PRICE_IMPACT_USD_AMOUNT_10K} USD: {price_impact_10k*100:.2f}%",
                            metadata={"price_impact_usd": get_config().PRICE_IMPACT_USD_AMOUNT_10K, "impact_percentage": price_impact_10k}
                        ))
                else:
                    logger.info(f"Aucun ordre de vente ('sell_orders') trouvé ou valide pour {token_address} pour l'analyse d'impact de prix.")
            
            return risks
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'analyse de la profondeur de liquidité pour {token_address}: {e}", exc_info=True)
            risks.append(SecurityRisk(
                risk_type="liquidity_depth_internal_error", # Specific internal error type
                severity=4, # Adjusted severity
                description=f"Erreur interne lors de l'analyse de la profondeur de liquidité: {str(e)}",
                metadata={"token_address": token_address, "error_type": type(e).__name__, "error_details": str(e)}
            ))
            return risks

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
        """Récupère les détenteurs d'un token en utilisant MarketDataProvider.
        Args:
            token_address: Adresse du token.
        Returns:
            Dictionnaire structuré: {'success': bool, 'error': str|None, 'data': dict_with_holders_or_None}
        """
        if not self.market_data:
            logger.error("MarketDataProvider non initialisé dans SecurityChecker pour _get_token_holders.")
            return {'success': False, 'error': "MarketDataProvider not available", 'data': None}

        logger.debug(f"SecurityChecker: Appel de market_data.get_token_holders pour {token_address}")
        response = await self.market_data.get_token_holders(token_address=token_address, limit=get_config().SECURITY_MAX_HOLDERS_TO_FETCH) # Using a config value for limit
        
        if not response['success']:
            logger.warning(f"Échec de la récupération des détenteurs de token via MarketDataProvider pour {token_address}: {response['error']}")
            # Propagate the structured error
            return response
            
        # response['data'] should be like {"holders": [...]} as per MarketDataProvider spec
        if response['data'] is None or "holders" not in response['data']:
            logger.warning(f"Données de détenteurs de token inattendues ou vides de MarketDataProvider pour {token_address}: {response['data']}")
            return {'success': False, 'error': "Invalid or empty holder data from MarketDataProvider", 'data': response['data']}

        return {'success': True, 'error': None, 'data': response['data']}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))) # Keep retry for underlying MDP resilience
    async def _get_recent_transactions(self, token_address: str, limit: int = 100) -> Dict[str, Any]:
        """Récupère les transactions récentes pour un token via MarketDataProvider.
        Args:
            token_address: Adresse du token.
            limit: Nombre de transactions à retourner.
        Returns:
            Dictionnaire structuré: {'success': bool, 'error': str|None, 'data': list_of_transactions_or_None}
        """
        if not self.market_data:
            logger.error("MarketDataProvider non initialisé dans SecurityChecker pour _get_recent_transactions.")
            return {'success': False, 'error': "MarketDataProvider not available", 'data': None}

        logger.debug(f"SecurityChecker: Appel de market_data.get_token_transactions pour {token_address}, limit {limit}")
        response = await self.market_data.get_token_transactions(token_address=token_address, limit=limit)

        if not response['success']:
            logger.warning(f"Échec de la récupération des transactions de token via MarketDataProvider pour {token_address}: {response['error']}")
            return response # Propagate structured error

        # response['data'] should be a list of transactions
        if response['data'] is None or not isinstance(response['data'], list):
            logger.warning(f"Données de transactions de token inattendues ou invalides de MarketDataProvider pour {token_address}: {response['data']}")
            return {'success': False, 'error': "Invalid or empty transaction data from MarketDataProvider", 'data': response['data']}

        return {'success': True, 'error': None, 'data': response['data']}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))) # Keep retry for underlying MDP resilience
    async def _get_liquidity_history(self, token_address: str, timeframe: str = "15m", limit: int = 96) -> Dict[str, Any]:
        """Récupère l'historique de liquidité pour un token via MarketDataProvider.
        Args:
            token_address: Adresse du token.
            timeframe: Intervalle de temps.
            limit: Nombre de points de données.
        Returns:
            Dictionnaire structuré: {'success': bool, 'error': str|None, 'data': list_of_liquidity_points_or_None}
        """
        if not self.market_data:
            logger.error("MarketDataProvider non initialisé dans SecurityChecker pour _get_liquidity_history.")
            return {'success': False, 'error': "MarketDataProvider not available", 'data': None}

        logger.debug(f"SecurityChecker: Appel de market_data.get_liquidity_history pour {token_address}, timeframe {timeframe}, limit {limit}")
        response = await self.market_data.get_liquidity_history(token_address=token_address, timeframe=timeframe, limit=limit)
        
        if not response['success']:
            logger.warning(f"Échec de la récupération de l'historique de liquidité via MarketDataProvider pour {token_address}: {response['error']}")
            return response # Propagate structured error

        # response['data'] should be a list of liquidity data points
        if response['data'] is None or not isinstance(response['data'], list):
            logger.warning(f"Données d'historique de liquidité inattendues ou invalides de MarketDataProvider pour {token_address}: {response['data']}")
            return {'success': False, 'error': "Invalid or empty liquidity history data from MarketDataProvider", 'data': response['data']}
            
        return {'success': True, 'error': None, 'data': response['data']}

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