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
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
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
    
    def _get_env_value(self, key: str, default: Any = None, value_type: type = str) -> Any:
        """
        Récupère une valeur d'environnement avec conversion de type.
        
        Args:
            key: Clé de la variable d'environnement
            default: Valeur par défaut
            value_type: Type de la valeur attendue
        """
        raw_value = os.getenv(key, default)
        if raw_value is None:
            return None
        
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
    debug: bool = False
    dev_mode: bool = False
    cors_allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    
    def _load_configuration(self):
        self.app_name = self._get_env_value("APP_NAME", "NumerusX")
        self.version = self._get_env_value("APP_VERSION", "1.0.0")
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
        self.jwt_secret_key = self._get_env_value("JWT_SECRET_KEY", "change_in_production")
        self.jwt_expiration = self._get_env_value("JWT_EXPIRATION", 3600, value_type=int)
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


@dataclass
class RedisConfig(BaseConfigSection):
    """Configuration Redis."""
    
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    url: str = ""
    
    def _load_configuration(self):
        self.host = self._get_env_value("REDIS_HOST", "localhost")
        self.port = self._get_env_value("REDIS_PORT", 6379, value_type=int)
        self.password = self._get_env_value("REDIS_PASSWORD")
        self.db = self._get_env_value("REDIS_DB", 0, value_type=int)
        
        # Construction de l'URL
        password_part = f":{self.password}@" if self.password else ""
        self.url = self._get_env_value(
            "REDIS_URL",
            f"redis://{password_part}{self.host}:{self.port}/{self.db}"
        )


@dataclass
class SolanaConfig(BaseConfigSection):
    """Configuration Solana et blockchain."""
    
    rpc_url: str = "https://api.mainnet-beta.solana.com"
    network: str = "mainnet-beta"
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
        self.network = self._get_env_value("SOLANA_NETWORK", "mainnet-beta")
        self.wallet_path = self._get_env_value(
            "WALLET_PATH", 
            os.path.join("keys", "solana_wallet.json")
        )
        self.backup_wallet_path = self._get_env_value("BACKUP_WALLET_PATH")
        self.private_key_bs58 = self._get_env_value("SOLANA_PRIVATE_KEY_BS58")
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
    default_slippage_bps: int = 50
    max_retries: int = 3
    
    def _load_configuration(self):
        self.api_key = self._get_env_value("JUPITER_API_KEY")
        self.lite_api_hostname = self._get_env_value("JUPITER_LITE_API_HOSTNAME", self.lite_api_hostname)
        self.pro_api_hostname = self._get_env_value("JUPITER_PRO_API_HOSTNAME", self.pro_api_hostname)
        self.default_slippage_bps = self._get_env_value("JUPITER_DEFAULT_SLIPPAGE_BPS", 50, value_type=int)
        self.max_retries = self._get_env_value("JUPITER_MAX_RETRIES", 3, value_type=int)


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
    
    def _load_configuration(self):
        self.base_asset = self._get_env_value("BASE_ASSET", self.base_asset)
        self.slippage_bps = self._get_env_value("SLIPPAGE_BPS", 50, value_type=int)
        self.min_liquidity_usd = self._get_env_value("MIN_LIQUIDITY_USD", 10000.0, value_type=float)
        self.max_open_positions = self._get_env_value("MAX_OPEN_POSITIONS", 5, value_type=int)
        self.max_order_size_usd = self._get_env_value("MAX_ORDER_SIZE_USD", 1000.0, value_type=float)
        self.min_order_value_usd = self._get_env_value("MIN_ORDER_VALUE_USD", 10.0, value_type=float)
        self.trade_confidence_threshold = self._get_env_value("TRADE_CONFIDENCE_THRESHOLD", 0.65, value_type=float)


@dataclass
class APIConfig(BaseConfigSection):
    """Configuration de l'API et services externes."""
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    def _load_configuration(self):
        self.host = self._get_env_value("API_HOST", "0.0.0.0")
        self.port = self._get_env_value("API_PORT", 8000, value_type=int)


class ConfigV2:
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


# Instance globale de configuration
_config_instance: Optional[ConfigV2] = None


def get_config() -> ConfigV2:
    """Retourne l'instance de configuration globale (singleton)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigV2()
    return _config_instance


def reload_config() -> ConfigV2:
    """Recharge la configuration depuis les variables d'environnement."""
    global _config_instance
    _config_instance = ConfigV2()
    return _config_instance 