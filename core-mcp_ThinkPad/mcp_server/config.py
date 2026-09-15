"""Configuration management for the 5G Core MCP server."""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Server configuration from environment variables."""
    
    # Flask settings
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "8085"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    # MCP settings
    MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8086"))
    MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "http")
    
    # Server identification
    MCP_SERVER_NAME: str = os.getenv("MCP_SERVER_NAME", "5g-core-mcp")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Data storage: choose between 'memory' or 'postgresql'
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "postgresql")
    
    # In-memory storage settings (legacy)
    MAX_REPORTS: int = int(os.getenv("MAX_REPORTS", "100"))
    MAX_UE_VOLUME_REPORTS: int = int(os.getenv("MAX_UE_VOLUME_REPORTS", "100"))
    
    # PostgreSQL settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "callback_server")
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() == "true"
    
    # SMF (Service Management Function) settings for event subscriptions
    SMF_BASE_URL: str = os.getenv(
        "SMF_BASE_URL",
        "http://192.168.70.133:8080/nsmf_event-exposure/v1/subscriptions"
    )
    SMF_PAYLOAD: str = os.getenv(
    "SMF_PAYLOAD",
    '{"notifId": "notifSMF", "notifUri": "https://172.17.0.1/callbacks/volume", "ImmeRep": true, "expiry": "2025-11-27T10:45:00Z", "notifMethod": "PERIODIC", "repPeriod": 30, "eventSubs": [{"event": "QOS_MON", "ueIpAddr": {"ipv4Addr": "12.1.1.2"}, "upfEvents": [{"type": "QOS_MONITORING", "immediateFlag": true, "measurementTypes": ["VOLUME_MEASUREMENT"], "granularityOfMeasurement": "PER_SESSION"}]}]}'
    )
    HTTP_VERSION: int = int(os.getenv("HTTP_VERSION", "2"))
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def __str__(self) -> str:
        """String representation of configuration."""
        storage_info = ""
        if self.STORAGE_TYPE == "postgresql":
            storage_info = f"\n  Database: {self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            storage_info = f"\n  Max Reports (Memory): {self.MAX_REPORTS}"
        
        return f"""
Configuration:
  Flask: {self.FLASK_HOST}:{self.FLASK_PORT}
  MCP: {self.MCP_HOST}:{self.MCP_PORT} ({self.MCP_TRANSPORT})
  Log Level: {self.LOG_LEVEL}
  Storage Type: {self.STORAGE_TYPE}{storage_info}
  SMF Subscription URL: {self.SMF_BASE_URL}
  HTTP Version: {self.HTTP_VERSION}
"""


# Global config instance
config = Config()
