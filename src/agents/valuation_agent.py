import numpy as np
from datetime import date
from typing import List

from .base_agent import BaseAgent
from ..models import AgentRating, Rating, AgentType, MarketData, NewsData, FundamentalData
from ..config import config

class ValuationAgent(BaseAgent):
    """
    Valuation/Momentum Agent
    
    Strategy: Risk-adjusted momentum using 20-day return / 60-day volatility
    Logic:
    1. Calculate 20-day return vs 60-day volatility
    2. Risk-adjusted momentum = return / volatility  
    3. Percentile ranking across universe
    4. Thresholds: >70th percentile=BUY, <30th=SELL, else HOLD
    """
    
    def __init__(self):
        super().__init__(AgentType.VALUATION, "Valuation/Momentum Agent")
        
    def analyze(self, market_data: MarketData, news_data: NewsData, 
                fundamental_data: List[FundamentalData], as_of_date: date) -> List[AgentRating]:
        """Generate valuation ratings for all tickers"""
        
        ratings = []
        momentum_scores = {}
        
        print(f"🔢 {self.name} analyzing...")
        
        # Calculate raw momentum scores
        for ticker in config.trading.tickers:
            ticker_prices = market_data.get_ticker_prices(ticker)
            score = self._calculate_momentum_score(ticker_prices, as_of_date)
            momentum_scores[ticker] = score
            
        # Convert to percentile rankings
        score_values = list(momentum_scores.values())
        
        for ticker in config.trading.tickers:
            raw_score = momentum_scores[ticker]
            percentile = self._score_to_percentile(raw_score, score_values)
            
            # Convert percentile to rating
            if percentile >= config.trading.buy_threshold:
                rating = Rating.BUY
            elif percentile <= config.trading.sell_threshold:
                rating = Rating.SELL
            else:
                rating = Rating.HOLD
                
            reasoning = f"Risk-adj momentum percentile: {percentile:.1%}"
            
            ratings.append(AgentRating(
                agent_type=self.agent_type,
                ticker=ticker,
                rating=rating,
                score=percentile,
                reasoning=reasoning,
                as_of_date=as_of_date
            ))
            
        return ratings
    
    def _calculate_momentum_score(self, prices: List, as_of_date: date) -> float:
        """Calculate risk-adjusted momentum score"""
        
        # Sort and filter prices
        sorted_prices = sorted(prices, key=lambda p: p.date)
        valid_prices = [p for p in sorted_prices if p.date <= as_of_date]
        
        if len(valid_prices) < 60:
            return 0.5  # Neutral score for insufficient data
            
        # 20-day return calculation
        recent_20 = valid_prices[-20:]
        return_20d = (recent_20[-1].close_price - recent_20[0].close_price) / recent_20[0].close_price
        
        # 60-day volatility calculation
        recent_60 = valid_prices[-60:]
        daily_returns = []
        
        for i in range(1, len(recent_60)):
            prev_close = recent_60[i-1].close_price
            curr_close = recent_60[i].close_price
            daily_return = (curr_close - prev_close) / prev_close
            daily_returns.append(daily_return)
            
        if len(daily_returns) < 10:
            return 0.5
            
        volatility_60d = np.std(daily_returns)
        
        # Risk-adjusted momentum
        if volatility_60d == 0:
            return 0.5
            
        risk_adj_momentum = return_20d / volatility_60d
        
        # Normalize using sigmoid
        normalized = 1 / (1 + np.exp(-risk_adj_momentum * 5))
        
        return max(0.0, min(1.0, normalized))
    
    def _score_to_percentile(self, score: float, all_scores: List[float]) -> float:
        """Convert raw score to percentile ranking"""
        if len(all_scores) <= 1:
            return 0.5
            
        rank = sum(1 for s in all_scores if s < score)
        return rank / len(all_scores)