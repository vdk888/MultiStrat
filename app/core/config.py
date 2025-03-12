import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Portfolio Management System"
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./portfolio_system.db")
    
    # Alpaca API configuration
    ALPACA_API_KEY: Optional[str] = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY: Optional[str] = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_BASE_URL: str = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    
    # Optimization configuration
    OPTIMIZATION_WORKERS: int = int(os.getenv("OPTIMIZATION_WORKERS", "1"))
    
    # Trading configuration
    TRADING_COSTS: Dict[str, float] = {
        "default": 0.0,  # Default trading cost as percentage
    }
    DEFAULT_RISK_PERCENT: float = 0.02  # Default risk per trade (2%)
    
    # Scheduler configuration
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "UTC"
    
    # Market hours
    MARKET_HOURS: Dict[str, Dict[str, Any]] = {
        "US_EQUITIES": {
            "timezone": "America/New_York",
            "start": "09:30",
            "end": "16:00",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    }
    
    # Data configuration
    DEFAULT_INTERVAL: str = "5m"  # 5-minute interval for data
    DEFAULT_INTERVAL_WEEKLY: str = "1wk"  # Weekly interval for data
    DEFAULT_LOOKBACK_DAYS: int = 30  # Default lookback period for data
    
    # validate interval format
    @validator("DEFAULT_INTERVAL")
    def validate_interval(cls, v):
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]
        if v not in valid_intervals:
            raise ValueError(f"Invalid interval: {v}. Must be one of {valid_intervals}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    """
    Get application settings
    """
    return Settings()
