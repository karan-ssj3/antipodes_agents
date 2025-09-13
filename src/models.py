from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Literal
from datetime import datetime, date
from enum import Enum

# Enums for type safety
class Rating(str, Enum):
    """Agent rating enum"""
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"

class AgentType(str, Enum):
    """Types of agents in our system"""
    VALUATION = "valuation"
    SENTIMENT = "sentiment" 
    FUNDAMENTAL = "fundamental"
    COORDINATOR = "coordinator"

# Core data models
class StockPrice(BaseModel):
    """Stock price data point"""
    ticker: str
    date: date
    open_price: float = Field(gt=0, description="Opening price")
    high_price: float = Field(gt=0, description="High price")
    low_price: float = Field(gt=0, description="Low price")
    close_price: float = Field(gt=0, description="Closing price")
    volume: int = Field(ge=0, description="Trading volume")
    
    @validator('high_price')
    def high_must_be_highest(cls, v, values):
        if 'low_price' in values and v < values['low_price']:
            raise ValueError('High price must be >= low price')
        return v

class NewsItem(BaseModel):
    """News article for sentiment analysis"""
    ticker: str
    title: str
    snippet: str
    date: date
    source: str = Field(default="unknown")
    url: Optional[str] = None
    
    @validator('title', 'snippet')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text fields cannot be empty')
        return v.strip()

class FundamentalData(BaseModel):
    """Fundamental data for a ticker"""
    ticker: str
    revenue_growth: float = Field(description="Revenue growth rate")
    operating_margin: float = Field(description="Operating margin")
    debt_to_equity: float = Field(ge=0, description="Debt to equity ratio")
    capex_intensity: float = Field(ge=0, description="CapEx as % of revenue")
    quality_score: float = Field(ge=0, le=1, description="Overall quality score 0-1")

class AgentRating(BaseModel):
    """Individual agent's rating and score"""
    agent_type: AgentType
    ticker: str
    rating: Rating
    score: float = Field(ge=0, le=1, description="Confidence score 0-1")
    reasoning: str = Field(description="Why this rating was given")
    as_of_date: date

class CoordinatorResult(BaseModel):
    """Final coordinator decision"""
    ticker: str
    valuation_rating: Rating
    valuation_score: float
    sentiment_rating: Rating
    sentiment_score: float
    fundamental_rating: Rating
    fundamental_score: float
    final_rating: Rating
    final_score: float
    as_of_date: date

class PortfolioPosition(BaseModel):
    """Portfolio position"""
    ticker: str
    weight: float = Field(ge=0, le=1, description="Portfolio weight")
    rating: Rating
    
class BacktestResult(BaseModel):
    """Backtest performance results"""
    portfolio_return: float
    benchmark_return: float
    active_return: float
    sharpe_ratio: float
    num_buy_positions: int
    start_date: date
    end_date: date
    
    @property
    def outperformed(self) -> bool:
        return self.active_return > 0

# Collection models
class MarketData(BaseModel):
    """Collection of market data"""
    prices: List[StockPrice]
    as_of_date: date
    
    def get_ticker_prices(self, ticker: str) -> List[StockPrice]:
        """Get prices for a specific ticker"""
        return [p for p in self.prices if p.ticker == ticker]
    
    def get_latest_price(self, ticker: str) -> Optional[StockPrice]:
        """Get most recent price for ticker"""
        ticker_prices = self.get_ticker_prices(ticker)
        if not ticker_prices:
            return None
        return max(ticker_prices, key=lambda x: x.date)

class NewsData(BaseModel):
    """Collection of news data"""
    articles: List[NewsItem]
    as_of_date: date
    
    def get_ticker_news(self, ticker: str) -> List[NewsItem]:
        """Get news for a specific ticker"""
        return [n for n in self.articles if n.ticker == ticker]

class AgentDecisions(BaseModel):
    """Collection of all agent decisions"""
    ratings: List[AgentRating]
    coordinator_results: List[CoordinatorResult]
    as_of_date: date