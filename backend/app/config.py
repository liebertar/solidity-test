"""
Application Configuration

Enterprise-grade configuration management using Pydantic Settings.
Supports environment variables, secrets management, and validation.
"""

import os
from typing import Optional, List, Any, Dict
from enum import Enum
from pathlib import Path

from pydantic import BaseSettings, validator, Field
from pydantic.networks import PostgresDsn, RedisDsn


class Environment(str, Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging level options"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NetworkConfig(str, Enum):
    """Blockchain network configurations"""
    MAINNET = "mainnet"
    SEPOLIA = "sepolia"
    POLYGON = "polygon"
    MUMBAI = "mumbai"
    LOCALHOST = "localhost"


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    
    All settings can be overridden via environment variables with APP_ prefix.
    For example: APP_DEBUG=true, APP_DATABASE_URL=postgresql://...
    """
    
    # Application Settings
    APP_NAME: str = Field(default="Art Platform API", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    TESTING: bool = Field(default=False, description="Testing mode")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, description="Environment")
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port", ge=1, le=65535)
    WORKERS: int = Field(default=1, description="Number of workers", ge=1)
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    
    # Security Settings
    SECRET_KEY: str = Field(..., description="Application secret key", min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration")
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt rounds", ge=4, le=31)
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS origins"
    )
    
    # Database Settings
    DATABASE_URL: PostgresDsn = Field(..., description="PostgreSQL database URL")
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database pool size", ge=1)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow", ge=0)
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis Settings
    REDIS_URL: RedisDsn = Field(..., description="Redis URL for caching")
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis connection pool size", ge=1)
    REDIS_TIMEOUT: int = Field(default=5, description="Redis timeout in seconds", ge=1)
    
    # Blockchain Settings
    BLOCKCHAIN_NETWORK: NetworkConfig = Field(default=NetworkConfig.LOCALHOST, description="Blockchain network")
    ALCHEMY_API_KEY: str = Field(..., description="Alchemy API key for Ethereum access")
    PRIVATE_KEY: str = Field(..., description="Private key for blockchain operations", min_length=64)
    CONTRACT_DEPLOY_GAS_LIMIT: int = Field(default=5000000, description="Gas limit for contract deployment")
    DEFAULT_GAS_PRICE: int = Field(default=20000000000, description="Default gas price in Wei")
    
    # NFT Contract Settings
    NFT_CONTRACT_ADDRESS: Optional[str] = Field(default=None, description="Deployed NFT contract address")
    MARKETPLACE_CONTRACT_ADDRESS: Optional[str] = Field(default=None, description="Deployed marketplace contract address")
    PLATFORM_TREASURY_ADDRESS: str = Field(..., description="Platform treasury wallet address")
    PLATFORM_FEE_BPS: int = Field(default=250, description="Platform fee in basis points (2.5%)", ge=0, le=10000)
    MINTING_FEE_ETH: float = Field(default=0.001, description="Minting fee in ETH", ge=0)
    
    # IPFS Settings
    IPFS_NODE_URL: str = Field(default="http://localhost:5001", description="IPFS node URL")
    PINATA_API_KEY: Optional[str] = Field(default=None, description="Pinata API key")
    PINATA_SECRET_KEY: Optional[str] = Field(default=None, description="Pinata secret key")
    IPFS_GATEWAY_URL: str = Field(default="https://gateway.pinata.cloud", description="IPFS gateway URL")
    
    # File Upload Settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes (10MB)")
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/webp"],
        description="Allowed image MIME types"
    )
    UPLOAD_DIRECTORY: str = Field(default="uploads", description="Upload directory path")
    
    # AI Verification Settings
    SYNTHID_API_URL: Optional[str] = Field(default=None, description="SynthID API URL")
    SYNTHID_API_KEY: Optional[str] = Field(default=None, description="SynthID API key")
    AI_VERIFICATION_THRESHOLD: float = Field(default=0.8, description="AI verification confidence threshold")
    
    # C2PA Settings
    C2PA_SIGNING_KEY: Optional[str] = Field(default=None, description="C2PA signing private key")
    C2PA_CERT_PATH: Optional[str] = Field(default=None, description="C2PA certificate path")
    
    # Celery Settings (Background Tasks)
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", description="Celery result backend")
    CELERY_TASK_SERIALIZER: str = Field(default="json", description="Celery task serializer")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", description="Celery result serializer")
    
    # Monitoring Settings
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    PROMETHEUS_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=8080, description="Metrics server port")
    
    # Logging Settings
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json or text)")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    LOG_ROTATION: str = Field(default="1 day", description="Log rotation interval")
    LOG_RETENTION: str = Field(default="30 days", description="Log retention period")
    
    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests per window")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")
    
    # Email Settings (for notifications)
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    SMTP_USE_TLS: bool = Field(default=True, description="Use TLS for SMTP")
    FROM_EMAIL: str = Field(default="noreply@artplatform.com", description="From email address")
    
    # Webhook Settings
    WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Webhook secret for verification")
    WEBHOOK_TIMEOUT: int = Field(default=30, description="Webhook timeout in seconds")
    
    # Feature Flags
    ENABLE_PUBLIC_MINTING: bool = Field(default=False, description="Enable public minting")
    ENABLE_AI_VERIFICATION: bool = Field(default=True, description="Enable AI verification")
    ENABLE_C2PA_VERIFICATION: bool = Field(default=True, description="Enable C2PA verification")
    ENABLE_MARKETPLACE: bool = Field(default=True, description="Enable marketplace features")
    ENABLE_AUCTIONS: bool = Field(default=True, description="Enable auction features")
    
    class Config:
        env_prefix = "APP_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        validate_assignment = True
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("CORS origins must be a list or comma-separated string")
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v) -> str:
        """Validate database URL format"""
        if isinstance(v, str):
            return v
        raise ValueError("Database URL must be a string")
    
    @validator("REDIS_URL", pre=True)
    def validate_redis_url(cls, v) -> str:
        """Validate Redis URL format"""
        if isinstance(v, str):
            return v
        raise ValueError("Redis URL must be a string")
    
    @validator("PRIVATE_KEY")
    def validate_private_key(cls, v) -> str:
        """Validate private key format"""
        if not v.startswith("0x"):
            v = "0x" + v
        if len(v) != 66:
            raise ValueError("Private key must be 64 characters (32 bytes)")
        return v
    
    @validator("PLATFORM_TREASURY_ADDRESS", "NFT_CONTRACT_ADDRESS", "MARKETPLACE_CONTRACT_ADDRESS")
    def validate_ethereum_address(cls, v) -> Optional[str]:
        """Validate Ethereum address format"""
        if v is None:
            return None
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format")
        return v.lower()
    
    @validator("PLATFORM_FEE_BPS")
    def validate_platform_fee(cls, v) -> int:
        """Validate platform fee is within reasonable bounds"""
        if v > 10000:  # 100%
            raise ValueError("Platform fee cannot exceed 100%")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.TESTING or self.ENVIRONMENT == Environment.TESTING
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic"""
        return str(self.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def minting_fee_wei(self) -> int:
        """Get minting fee in Wei"""
        return int(self.MINTING_FEE_ETH * 10**18)
    
    def get_contract_address(self, contract_type: str) -> Optional[str]:
        """Get contract address by type"""
        addresses = {
            "nft": self.NFT_CONTRACT_ADDRESS,
            "marketplace": self.MARKETPLACE_CONTRACT_ADDRESS,
        }
        return addresses.get(contract_type.lower())


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings (for dependency injection)"""
    return settings 