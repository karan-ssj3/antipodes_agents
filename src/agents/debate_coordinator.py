from typing import Dict, List
from datetime import date
from ..models import AgentRating, MarketData, Rating
from ..config import config

class DebateCoordinator:
    """
    Single debate round where agents can revise ratings based on peer input
    """
    
    def conduct_debate(self, initial_ratings: Dict[str, List[AgentRating]], 
                      market_data: MarketData, as_of_date: date) -> Dict[str, List[AgentRating]]:
        
        print("🗣️ Conducting agent debate round...")
        
        revised_ratings = {}
        
        for ticker in config.trading.tickers:
            # Get initial ratings for this ticker
            val_rating = next(r for r in initial_ratings["valuation"] if r.ticker == ticker)
            sent_rating = next(r for r in initial_ratings["sentiment"] if r.ticker == ticker) 
            fund_rating = next(r for r in initial_ratings["fundamental"] if r.ticker == ticker)
            
            # Simple debate rules - agents adjust if isolated
            debate_context = {
                "ratings": [val_rating.rating, sent_rating.rating, fund_rating.rating],
                "scores": [val_rating.score, sent_rating.score, fund_rating.score]
            }
            
            # Revision logic
            revised_val = self._agent_revision(val_rating, debate_context, "valuation")
            revised_sent = self._agent_revision(sent_rating, debate_context, "sentiment")
            revised_fund = self._agent_revision(fund_rating, debate_context, "fundamental")
            
            revised_ratings[ticker] = {
                "valuation": revised_val,
                "sentiment": revised_sent, 
                "fundamental": revised_fund
            }
            
        return revised_ratings
    
    def _agent_revision(self, original_rating: AgentRating, context: dict, agent_type: str) -> AgentRating:
        """Simple revision rules"""
        
        # Get all ratings except the current agent's rating
        all_ratings = context["ratings"]
        other_ratings = [r for i, r in enumerate(all_ratings) if i != self._get_agent_index(agent_type)]
        
        # Rule: If agent is alone in extreme position, moderate slightly
        if original_rating.rating == Rating.BUY and all(r != Rating.BUY for r in other_ratings):
            # Moderate BUY if alone
            new_score = original_rating.score * 0.8
            new_rating = Rating.HOLD if new_score < config.trading.buy_threshold else Rating.BUY
            reasoning = f"Moderated from solo BUY position (debate)"
            
        elif original_rating.rating == Rating.SELL and all(r != Rating.SELL for r in other_ratings):
            # Moderate SELL if alone  
            new_score = original_rating.score * 0.8 + 0.2
            new_rating = Rating.HOLD if new_score > config.trading.sell_threshold else Rating.SELL
            reasoning = f"Moderated from solo SELL position (debate)"
            
        else:
            # No revision needed
            return original_rating
            
        return AgentRating(
            agent_type=original_rating.agent_type,
            ticker=original_rating.ticker,
            rating=new_rating,
            score=new_score,
            reasoning=reasoning,
            as_of_date=original_rating.as_of_date
        )
    
    def _get_agent_index(self, agent_type: str) -> int:
        """Get the index of the agent in the ratings list"""
        agent_order = ["valuation", "sentiment", "fundamental"]
        return agent_order.index(agent_type)