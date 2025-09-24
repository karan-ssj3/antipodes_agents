from datetime import date
from typing import List, Dict

from .base_agent import BaseAgent
from ..models import (
    AgentRating, CoordinatorResult, Rating, AgentType,
    MarketData, NewsData, FundamentalData
)
from ..config import config

class Coordinator(BaseAgent):
    """
    Coordinator combines all agent decisions
    
    Strategy: Weighted voting with tie-breaking
    Logic:
    1. Weighted vote: Valuation 40%, Sentiment 30%, Fundamental 30%
    2. Numeric conversion: BUY=2, HOLD=1, SELL=0
    3. Weighted average → round to nearest rating
    4. Tie-break: Default to HOLD for stability
    """
    
    def __init__(self):
        super().__init__(AgentType.COORDINATOR, "Coordinator")
        
    def coordinate(self, 
                  valuation_ratings: List[AgentRating],
                  sentiment_ratings: List[AgentRating], 
                  fundamental_ratings: List[AgentRating],
                  as_of_date: date) -> List[CoordinatorResult]:
        """Coordinate all agent decisions into final ratings"""
        
        results = []
        
        print(f"🎯 {self.name} coordinating decisions...")
        
        for ticker in config.trading.tickers:
            # Get ratings from each agent
            val_rating = next((r for r in valuation_ratings if r.ticker == ticker), None)
            sent_rating = next((r for r in sentiment_ratings if r.ticker == ticker), None)
            fund_rating = next((r for r in fundamental_ratings if r.ticker == ticker), None)
            
            if not all([val_rating, sent_rating, fund_rating]):
                # Missing data - default to HOLD
                final_rating = Rating.HOLD
                final_score = 0.5
                reasoning = "Missing agent data - defaulting to HOLD"
            else:
                final_rating, final_score = self._calculate_final_rating({
                    'valuation': val_rating,
                    'sentiment': sent_rating,
                    'fundamental': fund_rating
                })
            
            result = CoordinatorResult(
                ticker=ticker,
                valuation_rating=val_rating.rating if val_rating else Rating.HOLD,
                valuation_score=val_rating.score if val_rating else 0.5,
                sentiment_rating=sent_rating.rating if sent_rating else Rating.HOLD,
                sentiment_score=sent_rating.score if sent_rating else 0.5,
                fundamental_rating=fund_rating.rating if fund_rating else Rating.HOLD,
                fundamental_score=fund_rating.score if fund_rating else 0.5,
                final_rating=final_rating,
                final_score=final_score,
                as_of_date=as_of_date
            )
            
            results.append(result)
            
        return results
    
    def _calculate_final_rating(self, agent_ratings: Dict[str, AgentRating]) -> tuple[Rating, float]:
        """Calculate weighted final rating"""
        
        # Convert ratings to numeric values (0-1 scale for simplicity)
        rating_values = {
            Rating.SELL: 0.0,
            Rating.HOLD: 0.5, 
            Rating.BUY: 1.0
        }
        
        # Get weights from config
        weights = {
            'valuation': config.trading.valuation_weight,
            'sentiment': config.trading.sentiment_weight,
            'fundamental': config.trading.fundamental_weight
        }
        
        # Calculate weighted score (already in 0-1 range)
        weighted_sum = 0.0
        for agent_name, rating_obj in agent_ratings.items():
            numeric_rating = rating_values[rating_obj.rating]
            weight = weights[agent_name]
            weighted_sum += numeric_rating * weight
            
        # Use config thresholds directly (no multiplication needed)
        buy_threshold = config.trading.buy_threshold    # 0.7
        sell_threshold = config.trading.sell_threshold  # 0.3
        
        if weighted_sum >= buy_threshold:
            final_rating = Rating.BUY
        elif weighted_sum <= sell_threshold:
            final_rating = Rating.SELL
        else:
            final_rating = Rating.HOLD
            
        # Final score is already in 0-1 range (no division needed)
        final_score = weighted_sum
        
        return final_rating, final_score
    
    # Implement required abstract method (not used for coordinator)
    def analyze(self, market_data: MarketData, news_data: NewsData, 
                fundamental_data: List[FundamentalData], as_of_date: date) -> List[AgentRating]:
        """Not used - coordinator uses coordinate() method instead"""
        return []
    
    