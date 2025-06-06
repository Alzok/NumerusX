"""
Configuration refactorisée pour NumerusX v1.0.0
- Organisation en classes par domaine fonctionnel
- Élimination des duplications
- Validation automatique des configurations
- Support des configurations chiffrées amélioré
- Gestion d'erreurs robuste
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from cryptography.fernet import Fernet
from enum import Enum

# Setup logging pour la configuration
config_logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environnements d'exécution supportés."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class NetworkType(Enum):
    """Types de réseaux Solana supportés."""
    MAINNET = "mainnet-beta"
    DEVNET = "devnet"
    TESTNET = "testnet"


@dataclass
class ValidationResult:
    """Résultat de validation d'une configuration."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ConfigurationError(Exception):
    """Exception levée lors d'erreurs de configuration."""
    pass


class EncryptionService:
    """Service de chiffrement centralisé et amélioré."""
    
    _fernet_instance: Optional[Fernet] = None
    
    @classmethod
    def _get_fernet(cls) -> Optional[Fernet]:
        """Initialise et retourne l'instance Fernet."""
        if cls._fernet_instance is None:
            encryption_key = os.getenv("MASTER_ENCRYPTION_KEY")
            if not encryption_key:
                config_logger.warning("MASTER_ENCRYPTION_KEY not set - encrypted configurations will not work")
                return None
            
            try:
                cls._fernet_instance = Fernet(encryption_key.encode())
            except Exception as e:
                config_logger.error(f"Failed to initialize encryption: {e}")
                return None
        
        return cls._fernet_instance
    
    @classmethod
    def encrypt(cls, plaintext: str) -> Optional[str]:
        """Chiffre un texte en clair."""
        if not plaintext:
            return None
            
        fernet = cls._get_fernet()
        if not fernet:
            config_logger.warning("Encryption not available")
            return None
        
        try:
            encrypted_bytes = fernet.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            config_logger.error(f"Encryption failed: {e}")
            return None
    
    @classmethod
    def decrypt(cls, encrypted_text: str) -> Optional[str]:
        """Déchiffre un texte chiffré."""
        if not encrypted_text:
            return None
            
        fernet = cls._get_fernet()
        if not fernet:
            return None
        
        try:
            decrypted_bytes = fernet.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            config_logger.error(f"Decryption failed: {e}")
            return None


class BaseConfigSection:
    """Classe de base pour les sections de configuration."""
    
    def __init__(self):
        self._load_configuration()
        self._validate_configuration()
    
    def _load_configuration(self):
        """Charge la configuration depuis les variables d'environnement."""
        pass
    
    def _validate_configuration(self) -> ValidationResult:
        """Valide la configuration."""
        return ValidationResult(is_valid=True)
    
    def _get_env_value(self, key: str, default: Any = None, 
                      encrypted_key: Optional[str] = None,
                      value_type: type = str) -> Any:
        """
        Récupère une valeur d'environnement avec support du chiffrement.
        
        Args:
            key: Clé de la variable d'environnement
            default: Valeur par défaut
            encrypted_key: Clé de la version chiffrée (optionnel)
            value_type: Type de la valeur attendue
        """
        # Essayer d'abord la version chiffrée si disponible
        if encrypted_key:
            encrypted_value = os.getenv(encrypted_key)
            if encrypted_value:
                decrypted_value = EncryptionService.decrypt(encrypted_value)
                if decrypted_value:
                    return self._convert_type(decrypted_value, value_type)
                else:
                    config_logger.warning(f"Failed to decrypt {encrypted_key}, falling back to {key}")
        
        # Fallback sur la version en clair
        raw_value = os.getenv(key)
        if raw_value is None or raw_value == "":
            return default
        
        return self._convert_type(raw_value, value_type)
    
    def _convert_type(self, value: str, target_type: type) -> Any:
        """Convertit une valeur string vers le type voulu."""
        if target_type == bool:
            return value.lower() in ('true', '1', 't', 'yes', 'on')
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == list:
            return [item.strip() for item in value.split(',') if item.strip()]
        elif target_type == dict:
            return json.loads(value)
        else:
            return value


@dataclass
class ApplicationConfig(BaseConfigSection):
    """Configuration générale de l'application."""
    
    app_name: str = "NumerusX"
    version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    dev_mode: bool = False
    cors_allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    
    def _load_configuration(self):
        self.app_name = self._get_env_value("APP_NAME", "NumerusX")
        self.version = self._get_env_value("APP_VERSION", "1.0.0")
        
        env_str = self._get_env_value("ENVIRONMENT", "development")
        try:
            self.environment = Environment(env_str)
        except ValueError:
            config_logger.warning(f"Invalid environment '{env_str}', using development")
            self.environment = Environment.DEVELOPMENT
        
        self.debug = self._get_env_value("DEBUG", False, value_type=bool)
        self.dev_mode = self._get_env_value("DEV_MODE", False, value_type=bool)
        self.cors_allowed_origins = self._get_env_value("CORS_ALLOWED_ORIGINS", "*", value_type=list)


@dataclass
class SecurityConfig(BaseConfigSection):
    """Configuration de sécurité et authentification."""
    
    jwt_secret_key: str = "change_in_production"
    jwt_expiration: int = 3600
    auth_provider_jwks_uri: Optional[str] = None
    auth_provider_issuer: Optional[str] = None
    auth_provider_audience: Optional[str] = None
    auth_provider_algorithms: str = "RS256"
    
    def _load_configuration(self):
        self.jwt_secret_key = self._get_env_value(
            "JWT_SECRET_KEY", 
            "change_in_production",
            encrypted_key="ENCRYPTED_JWT_SECRET_KEY"
        )
        self.jwt_expiration = self._get_env_value("JWT_EXPIRATION", 3600, value_type=int)
        
        # Configuration OIDC
        self.auth_provider_jwks_uri = self._get_env_value("AUTH_PROVIDER_JWKS_URI")
        self.auth_provider_issuer = self._get_env_value("AUTH_PROVIDER_ISSUER") 
        self.auth_provider_audience = self._get_env_value("AUTH_PROVIDER_AUDIENCE")
        self.auth_provider_algorithms = self._get_env_value("AUTH_PROVIDER_ALGORITHMS", "RS256")
    
    def _validate_configuration(self) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        if self.jwt_secret_key == "change_in_production":
            result.warnings.append("JWT secret key should be changed in production")
        
        if not self.auth_provider_jwks_uri:
            result.warnings.append("Auth provider JWKS URI not configured")
        
        return result


@dataclass 
class DatabaseConfig(BaseConfigSection):
    """Configuration de base de données."""
    
    database_url: str = ""
    db_path: str = ""
    
    def _load_configuration(self):
        default_db_path = os.path.join("data", "numerusx.db")
        self.db_path = self._get_env_value("DB_PATH", default_db_path)
        self.database_url = self._get_env_value(
            "DATABASE_URL", 
            f"sqlite:///{self.db_path}"
        )
    
    def ensure_db_directory(self) -> str:
        """Crée le répertoire de la base de données si nécessaire."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return self.db_path


class RedisConfig(BaseConfigSection):
    """Configuration Redis."""
    
    def __init__(self):
        self.host: str = "localhost"
        self.port: int = 6379
        self.password: Optional[str] = None
        self.db: int = 0
        self.url: str = ""
        super().__init__()
    
    def _load_configuration(self):
        self.host = self._get_env_value("REDIS_HOST", "localhost")
        self.port = self._get_env_value("REDIS_PORT", 6379, value_type=int)
        self.password = self._get_env_value(
            "REDIS_PASSWORD",
            encrypted_key="ENCRYPTED_REDIS_PASSWORD"
        )
        self.db = self._get_env_value("REDIS_DB", 0, value_type=int)
        
        # Construction de l'URL
        if self.password:
            default_url = f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        else:
            default_url = f"redis://{self.host}:{self.port}/{self.db}"
        
        self.url = self._get_env_value("REDIS_URL", default_url)


@dataclass
class SolanaConfig(BaseConfigSection):
    """Configuration Solana et blockchain."""
    
    rpc_url: str = "https://api.mainnet-beta.solana.com"
    network: NetworkType = NetworkType.MAINNET
    wallet_path: str = ""
    backup_wallet_path: Optional[str] = None
    private_key_bs58: Optional[str] = None
    default_fee_lamports: int = 5000
    
    # Token mint addresses
    sol_mint: str = "So11111111111111111111111111111111111111112"
    usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    usdt_mint: str = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
    
    def _load_configuration(self):
        self.rpc_url = self._get_env_value("SOLANA_RPC_URL", self.rpc_url)
        
        network_str = self._get_env_value("SOLANA_NETWORK", "mainnet-beta")
        try:
            self.network = NetworkType(network_str)
        except ValueError:
            config_logger.warning(f"Invalid Solana network '{network_str}', using mainnet")
            self.network = NetworkType.MAINNET
        
        self.wallet_path = self._get_env_value(
            "WALLET_PATH", 
            os.path.join("keys", "solana_wallet.json")
        )
        self.backup_wallet_path = self._get_env_value("BACKUP_WALLET_PATH")
        
        # Clé privée chiffrée ou en clair
        self.private_key_bs58 = self._get_env_value(
            "SOLANA_PRIVATE_KEY_BS58",
            encrypted_key="ENCRYPTED_SOLANA_PRIVATE_KEY_BS58"
        )
        
        self.default_fee_lamports = self._get_env_value(
            "DEFAULT_FEE_PER_SIGNATURE_LAMPORTS", 
            5000, 
            value_type=int
        )


@dataclass
class JupiterConfig(BaseConfigSection):
    """Configuration Jupiter DEX."""
    
    api_key: Optional[str] = None
    lite_api_hostname: str = "https://lite-api.jup.ag"
    pro_api_hostname: str = "https://api.jup.ag"
    
    # API paths
    swap_api_path: str = "/swap/v1"
    price_api_path: str = "/price/v2"
    token_api_path: str = "/tokens/v1"
    trigger_api_path: str = "/trigger/v1"
    recurring_api_path: str = "/recurring/v1"
    
    # Transaction parameters
    default_slippage_bps: int = 50
    dynamic_compute_unit_limit: bool = True
    compute_unit_price_micro_lamports: Optional[str] = None
    priority_fee_level: str = "Default"
    wrap_and_unwrap_sol: bool = True
    only_direct_routes: bool = False
    restrict_intermediate_tokens: bool = True
    swap_mode: str = "ExactIn"
    max_retries: int = 3
    
    def _load_configuration(self):
        self.api_key = self._get_env_value(
            "JUPITER_API_KEY",
            encrypted_key="ENCRYPTED_JUPITER_API_KEY"
        )
        
        self.lite_api_hostname = self._get_env_value("JUPITER_LITE_API_HOSTNAME", self.lite_api_hostname)
        self.pro_api_hostname = self._get_env_value("JUPITER_PRO_API_HOSTNAME", self.pro_api_hostname)
        
        # API paths
        self.swap_api_path = self._get_env_value("JUPITER_SWAP_API_PATH", self.swap_api_path)
        self.price_api_path = self._get_env_value("JUPITER_PRICE_API_PATH", self.price_api_path)
        self.token_api_path = self._get_env_value("JUPITER_TOKEN_API_PATH", self.token_api_path)
        self.trigger_api_path = self._get_env_value("JUPITER_TRIGGER_API_PATH", self.trigger_api_path)
        self.recurring_api_path = self._get_env_value("JUPITER_RECURRING_API_PATH", self.recurring_api_path)
        
        # Transaction parameters
        self.default_slippage_bps = self._get_env_value("JUPITER_DEFAULT_SLIPPAGE_BPS", 50, value_type=int)
        self.dynamic_compute_unit_limit = self._get_env_value("JUPITER_DYNAMIC_COMPUTE_UNIT_LIMIT", True, value_type=bool)
        self.compute_unit_price_micro_lamports = self._get_env_value("JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS")
        self.priority_fee_level = self._get_env_value("JUPITER_PRIORITY_FEE_LEVEL", "Default")
        self.wrap_and_unwrap_sol = self._get_env_value("JUPITER_WRAP_AND_UNWRAP_SOL", True, value_type=bool)
        self.only_direct_routes = self._get_env_value("JUPITER_ONLY_DIRECT_ROUTES", False, value_type=bool)
        self.restrict_intermediate_tokens = self._get_env_value("JUPITER_RESTRICT_INTERMEDIATE_TOKENS", True, value_type=bool)
        self.swap_mode = self._get_env_value("JUPITER_SWAP_MODE", "ExactIn")
        self.max_retries = self._get_env_value("JUPITER_MAX_RETRIES", 3, value_type=int)
    
    def get_quote_url(self) -> str:
        """Construit l'URL de quote Jupiter."""
        return f"{self.lite_api_hostname.rstrip('/')}{self.swap_api_path.rstrip('/')}/quote"
    
    def get_swap_url(self) -> str:
        """Construit l'URL de swap Jupiter."""
        return f"{self.lite_api_hostname.rstrip('/')}{self.swap_api_path.rstrip('/')}/swap"
    
    def get_price_url(self) -> str:
        """Construit l'URL de prix Jupiter."""
        return f"{self.lite_api_hostname.rstrip('/')}{self.price_api_path.rstrip('/')}"


@dataclass
class TradingConfig(BaseConfigSection):
    """Configuration des paramètres de trading."""
    
    base_asset: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
    slippage_bps: int = 50
    min_liquidity_usd: float = 10000.0
    max_open_positions: int = 5
    max_order_size_usd: float = 1000.0
    min_order_value_usd: float = 10.0
    trade_confidence_threshold: float = 0.65
    trading_update_interval_seconds: int = 60
    initial_portfolio_balance_usd: float = 1000.0
    
    # Paramètres avancés
    signal_expiry_seconds: int = 300
    price_check_interval_seconds: int = 30
    order_update_interval_seconds: int = 15
    execute_market_orders: bool = True
    auto_close_positions: bool = True
    transaction_confirmation_timeout_seconds: int = 120
    transaction_confirmation_poll_interval_seconds: int = 5
    
    # Retry configuration
    send_transaction_retry_attempts: int = 3
    send_transaction_retry_multiplier: float = 1.0
    send_transaction_retry_min_wait: float = 1.0
    send_transaction_retry_max_wait: float = 5.0
    
    def _load_configuration(self):
        self.base_asset = self._get_env_value("BASE_ASSET", self.base_asset)
        self.slippage_bps = self._get_env_value("SLIPPAGE_BPS", 50, value_type=int)
        self.min_liquidity_usd = self._get_env_value("MIN_LIQUIDITY_USD", 10000.0, value_type=float)
        self.max_open_positions = self._get_env_value("MAX_OPEN_POSITIONS", 5, value_type=int)
        self.max_order_size_usd = self._get_env_value("MAX_ORDER_SIZE_USD", 1000.0, value_type=float)
        self.min_order_value_usd = self._get_env_value("MIN_ORDER_VALUE_USD", 10.0, value_type=float)
        self.trade_confidence_threshold = self._get_env_value("TRADE_CONFIDENCE_THRESHOLD", 0.65, value_type=float)
        self.trading_update_interval_seconds = self._get_env_value("TRADING_UPDATE_INTERVAL_SECONDS", 60, value_type=int)
        self.initial_portfolio_balance_usd = self._get_env_value("INITIAL_PORTFOLIO_BALANCE_USD", 1000.0, value_type=float)
        
        # Paramètres avancés
        self.signal_expiry_seconds = self._get_env_value("SIGNAL_EXPIRY_SECONDS", 300, value_type=int)
        self.price_check_interval_seconds = self._get_env_value("PRICE_CHECK_INTERVAL_SECONDS", 30, value_type=int)
        self.order_update_interval_seconds = self._get_env_value("ORDER_UPDATE_INTERVAL_SECONDS", 15, value_type=int)
        self.execute_market_orders = self._get_env_value("EXECUTE_MARKET_ORDERS", True, value_type=bool)
        self.auto_close_positions = self._get_env_value("AUTO_CLOSE_POSITIONS", True, value_type=bool)
        self.transaction_confirmation_timeout_seconds = self._get_env_value("TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS", 120, value_type=int)
        self.transaction_confirmation_poll_interval_seconds = self._get_env_value("TRANSACTION_CONFIRMATION_POLL_INTERVAL_SECONDS", 5, value_type=int)
        
        # Retry configuration
        self.send_transaction_retry_attempts = self._get_env_value("SEND_TRANSACTION_RETRY_ATTEMPTS", 3, value_type=int)
        self.send_transaction_retry_multiplier = self._get_env_value("SEND_TRANSACTION_RETRY_MULTIPLIER", 1.0, value_type=float)
        self.send_transaction_retry_min_wait = self._get_env_value("SEND_TRANSACTION_RETRY_MIN_WAIT", 1.0, value_type=float)
        self.send_transaction_retry_max_wait = self._get_env_value("SEND_TRANSACTION_RETRY_MAX_WAIT", 5.0, value_type=float)


@dataclass
class APIConfig(BaseConfigSection):
    """Configuration de l'API et services externes."""
    
    host: str = "0.0.0.0"
    port: int = 8000
    rate_limit_wait_seconds: float = 0.2
    rate_limits: Dict[str, Dict] = field(default_factory=dict)
    
    # Services externes
    dexscreener_api_url: str = "https://api.dexscreener.com/latest/dex"
    dexscreener_api_key: Optional[str] = None
    
    def _load_configuration(self):
        self.host = self._get_env_value("API_HOST", "0.0.0.0")
        self.port = self._get_env_value("API_PORT", 8000, value_type=int)
        self.rate_limit_wait_seconds = self._get_env_value("DEFAULT_API_RATE_LIMIT_WAIT_SECONDS", 0.2, value_type=float)
        
        # Rate limits par service
        default_rate_limits = {
            "jupiter": {"limit": 100, "window_seconds": 60, "default_wait": 0.2},
            "dexscreener": {"limit": 120, "window_seconds": 60, "default_wait": 0.5},
            "raydium": {"limit": 100, "window_seconds": 60, "default_wait": 0.2}
        }
        self.rate_limits = self._get_env_value("API_RATE_LIMITS", default_rate_limits, value_type=dict)
        
        # Services externes
        self.dexscreener_api_url = self._get_env_value("DEXSCREENER_API_URL", self.dexscreener_api_url)
        self.dexscreener_api_key = self._get_env_value(
            "DEXSCREENER_API_KEY",
            encrypted_key="ENCRYPTED_DEXSCREENER_API_KEY"
        )


class NumerusXConfig:
    """Configuration principale refactorisée pour NumerusX v1.0.0."""
    
    def __init__(self):
        self.app = ApplicationConfig()
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.solana = SolanaConfig()
        self.jupiter = JupiterConfig()
        self.trading = TradingConfig()
        self.api = APIConfig()
        
        self._validate_all_configurations()
    
    def _validate_all_configurations(self):
        """Valide toutes les configurations."""
        sections = [
            ("Application", self.app),
            ("Security", self.security),
            ("Database", self.database),
            ("Redis", self.redis),
            ("Solana", self.solana),
            ("Jupiter", self.jupiter),
            ("Trading", self.trading),
            ("API", self.api)
        ]
        
        all_errors = []
        all_warnings = []
        
        for section_name, section in sections:
            result = section._validate_configuration()
            if not result.is_valid:
                all_errors.extend([f"{section_name}: {error}" for error in result.errors])
            all_warnings.extend([f"{section_name}: {warning}" for warning in result.warnings])
        
        if all_errors:
            error_msg = "Configuration errors found:\n" + "\n".join(all_errors)
            config_logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        if all_warnings:
            warning_msg = "Configuration warnings:\n" + "\n".join(all_warnings)
            config_logger.warning(warning_msg)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la configuration en dictionnaire."""
        return {
            "app": self.app.__dict__,
            "security": self.security.__dict__,
            "database": self.database.__dict__,
            "redis": self.redis.__dict__,
            "solana": self.solana.__dict__,
            "jupiter": self.jupiter.__dict__,
            "trading": self.trading.__dict__,
            "api": self.api.__dict__
        }
    
    def get_log_config(self) -> Dict[str, Any]:
        """Retourne la configuration de logging."""
        log_dir = os.getenv("LOG_DIR", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": os.getenv("LOG_LEVEL", "INFO")
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": os.path.join(log_dir, "numerusx.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "formatter": "default",
                    "level": os.getenv("LOG_LEVEL", "INFO")
                }
            },
            "root": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "handlers": ["console", "file"]
            }
        }


# Instance globale de configuration
_config_instance: Optional[NumerusXConfig] = None


def get_config() -> NumerusXConfig:
    """Retourne l'instance de configuration globale (singleton)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = NumerusXConfig()
    return _config_instance


def reload_config() -> NumerusXConfig:
    """Recharge la configuration depuis les variables d'environnement."""
    global _config_instance
    _config_instance = NumerusXConfig()
    return _config_instance


# Compatibilité avec l'ancien système
class Config:
    """Wrapper pour maintenir la compatibilité avec l'ancienne configuration."""
    
    def __init__(self):
        # Créer directement l'instance pour éviter la récursion
        self._new_config = NumerusXConfig()
    
    def __getattr__(self, name: str) -> Any:
        """Redirecte les accès aux attributs vers la nouvelle configuration."""
        # Mapping des anciens noms vers les nouveaux
        mapping = {
            "DATABASE_URL": lambda: self._new_config.database.database_url,
            "REDIS_URL": lambda: self._new_config.redis.url,
            "SOLANA_RPC_URL": lambda: self._new_config.solana.rpc_url,
            "JUPITER_DEFAULT_SLIPPAGE_BPS": lambda: self._new_config.jupiter.default_slippage_bps,
            "BASE_ASSET": lambda: self._new_config.trading.base_asset,
            "JWT_SECRET_KEY": lambda: self._new_config.security.jwt_secret_key,
            "API_HOST": lambda: self._new_config.api.host,
            "API_PORT": lambda: self._new_config.api.port,
        }
        
        if name in mapping:
            return mapping[name]()
        
        # Fallback sur les variables d'environnement
        return os.getenv(name)
    
    @classmethod
    def get_db_path(cls):
        """Compatibilité pour get_db_path."""
        return get_config().database.ensure_db_directory() 