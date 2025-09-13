from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional
from datetime import datetime
import os

class APISettings(BaseSettings):
    """API configuration with environment variable support"""
    
    # Financial data API
    financial_datasets_api_key: Optional[str] = None
    financial_datasets_base_url: str = "https://api.financialdatasets.ai" 
    
    # OpenAI for LangChain (if we use it later)
    openai_api_key: Optional[str] = None
    
    # LangSmith for monitoring
    langchain_api_key: Optional[str] = None
    langchain_project: str = "antipodes-agents"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables

class TradingConfig(BaseModel):
    """Trading and backtesting configuration"""
    
    # Universe
    tickers: list[str] = ["AAPL", "MSFT", "NVDA", "TSLA"]
    
    # Agent weights for coordinator
    valuation_weight: float = 0.4
    sentiment_weight: float = 0.3
    fundamental_weight: float = 0.3
    
    # Backtest settings
    forward_window_days: int = 90
    
    # Rating thresholds
    buy_threshold: float = 0.7
    sell_threshold: float = 0.3

class AppConfig:
    """Main application configuration"""
    
    def __init__(self):
        self.api = APISettings()
        self.trading = TradingConfig()
        
    @property
    def has_financial_api_key(self) -> bool:
        """Check if we have the financial datasets API key"""
        return self.api.financial_datasets_api_key is not None
        
    def get_data_fallback_path(self) -> str:
        """Get path for fallback data"""
        return os.path.join("data", "fallback_prices.csv")

# Global config instance
config = AppConfig()