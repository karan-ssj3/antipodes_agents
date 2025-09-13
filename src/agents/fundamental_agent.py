from datetime import date
from typing import List

from .base_agent import BaseAgent
from ..models import AgentRating, Rating, AgentType, MarketData, NewsData, FundamentalData
from ..config import config

class FundamentalAgent(BaseAgent):
    """
    Fundamental/Quality Agent
    
    Strategy: Composite fundamental score
    Logic:
    1. Revenue growth (25%), Operating margin (25%)
    2. Low leverage bonus (25%), CapEx efficiency (25%)  
    3. Composite score → percentile ranking
    4. Thresholds: >0.7=BUY, <0.4=SELL, else HOLD
    """
    
    def __init__(self):
        super().__init__(AgentType.FUNDAMENTAL, "Fundamental/Quality Agent")
        
    def analyze(self, market_data: MarketData, news_data: NewsData, 
                fundamental_data: List[FundamentalData], as_of_date: date) -> List[AgentRating]:
        """Generate fundamental ratings for all tickers"""
        
        ratings = []
        composite_scores = {}
        
        print(f"📊 {self.name} analyzing...")
        
        # Calculate composite scores
        for fund_data in fundamental_data:
            ticker = fund_data.ticker
            score = self._calculate_composite_score(fund_data)
            composite_scores[ticker] = score
            
        # Convert to percentile rankings
        score_values = list(composite_scores.values())
        
        for ticker in config.trading.tickers:
            if ticker not in composite_scores:
                # Missing fundamental data - default to neutral
                composite_score = 0.5
                percentile = 0.5
                reasoning = "No fundamental data available"
            else:
                composite_score = composite_scores[ticker]
                percentile = self._score_to_percentile(composite_score, score_values)
                reasoning = f"Composite quality: {composite_score:.3f}, percentile: {percentile:.1%}"
            
            # Use composite score thresholds
            if composite_score >= 0.7:
                rating = Rating.BUY
            elif composite_score <= 0.4:
                rating = Rating.SELL
            else:
                rating = Rating.HOLD
                
            ratings.append(AgentRating(
                agent_type=self.agent_type,
                ticker=ticker,
                rating=rating,
                score=composite_score,
                reasoning=reasoning,
                as_of_date=as_of_date
            ))
            
        return ratings
    
    def _calculate_composite_score(self, fund_data: FundamentalData) -> float:
        """Calculate composite fundamental score"""
        
        # Normalize each metric to 0-1 scale
        
        # 1. Revenue growth (25% weight)
        # Scale: 0% = 0.3, 10% = 0.7, 20%+ = 1.0
        growth_score = min(1.0, 0.3 + (fund_data.revenue_growth * 3.5))
        growth_score = max(0.0, growth_score)
        
        # 2. Operating margin (25% weight) 
        # Scale: 10% = 0.3, 25% = 0.7, 40%+ = 1.0
        margin_score = min(1.0, max(0.0, (fund_data.operating_margin - 0.1) / 0.3 * 0.7 + 0.3))
        
        # 3. Leverage score (25% weight) - lower is better
        # Scale: 0.5+ D/E = 0.0, 0.2 D/E = 0.7, 0.1 D/E = 1.0
        if fund_data.debt_to_equity >= 0.5:
            leverage_score = 0.0
        else:
            leverage_score = min(1.0, (0.5 - fund_data.debt_to_equity) / 0.4)
        
        # 4. CapEx efficiency (25% weight) - lower intensity is better for mature companies
        # Scale: 15%+ = 0.0, 8% = 0.5, 4% = 1.0
        if fund_data.capex_intensity >= 0.15:
            capex_score = 0.0
        else:
            capex_score = min(1.0, (0.15 - fund_data.capex_intensity) / 0.11)
        
        # Composite weighted average
        composite = (
            0.25 * growth_score +
            0.25 * margin_score + 
            0.25 * leverage_score +
            0.25 * capex_score
        )
        
        return max(0.0, min(1.0, composite))
    
    def _score_to_percentile(self, score: float, all_scores: List[float]) -> float:
        """Convert composite score to percentile ranking"""
        if len(all_scores) <= 1:
            return 0.5
            
        rank = sum(1 for s in all_scores if s < score)
        return rank / len(all_scores)