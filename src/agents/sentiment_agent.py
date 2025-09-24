from datetime import date
from typing import List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .base_agent import BaseAgent
from ..models import AgentRating, Rating, AgentType, MarketData, NewsData, FundamentalData
from ..config import config

class SentimentAgent(BaseAgent):
    """
    News/Sentiment Agent
    
    Strategy: VADER sentiment analysis with recency weighting
    Logic:
    1. Use VADER sentiment on headlines + snippets
    2. Weight recent news more heavily (exponential decay)
    3. Average weighted sentiment → percentile ranking
    4. Thresholds: >0.1=BUY, <-0.1=SELL, else HOLD
    """
    
    def __init__(self):
        super().__init__(AgentType.SENTIMENT, "News/Sentiment Agent")
        self.analyzer = SentimentIntensityAnalyzer()
        
    def analyze(self, market_data: MarketData, news_data: NewsData, 
                fundamental_data: List[FundamentalData], as_of_date: date) -> List[AgentRating]:
        """Generate sentiment ratings for all tickers"""
        
        ratings = []
        sentiment_scores = {}
        
        print(f"📰 {self.name} analyzing...")
        
        # Calculate sentiment scores for each ticker
        for ticker in config.trading.tickers:
            ticker_news = news_data.get_ticker_news(ticker)
            score = self._calculate_sentiment_score(ticker_news, as_of_date)
            sentiment_scores[ticker] = score
            
        # Convert to percentile rankings
        score_values = list(sentiment_scores.values())
        
        for ticker in config.trading.tickers:
            raw_score = sentiment_scores[ticker]
            percentile = self._score_to_percentile(raw_score, score_values)
            
            # Convert sentiment to rating using different thresholds
            if raw_score > 0.1:
                rating = Rating.BUY
            elif raw_score < -0.1:
                rating = Rating.SELL
            else:
                rating = Rating.HOLD
                
            reasoning = f"Weighted sentiment: {raw_score:.3f}, percentile: {percentile:.1%}"
            
            ratings.append(AgentRating(
                agent_type=self.agent_type,
                ticker=ticker,
                rating=rating,
                score=(raw_score + 1) / 2,  # Normalize -1,1 to 0,1
                reasoning=reasoning,
                as_of_date=as_of_date
            ))
            
        return ratings
    
    def _calculate_sentiment_score(self, news_items: List, as_of_date: date) -> float:
        """Calculate weighted sentiment score"""
        
        if not news_items:
            return 0.0  
            
        weighted_scores = []
        
        for article in news_items:
            # Combine title and snippet for analysis
            text = f"{article.title}. {article.snippet}"
            
            # Get VADER sentiment
            sentiment = self.analyzer.polarity_scores(text)
            compound_score = sentiment['compound']  # Range: -1 to +1
            
            # Calculate recency weight (exponential decay)
            days_old = (as_of_date - article.date).days
            recency_weight = 0.9 ** max(0, days_old)  # Decay factor
            
            weighted_score = compound_score * recency_weight
            weighted_scores.append(weighted_score)
            
        # Average weighted sentiment
        if weighted_scores:
            avg_sentiment = sum(weighted_scores) / len(weighted_scores)
        else:
            avg_sentiment = 0.0
            
        return avg_sentiment
    
    def _score_to_percentile(self, score: float, all_scores: List[float]) -> float:
        """Convert sentiment score to percentile ranking"""
        if len(all_scores) <= 1:
            return 0.5
            
        rank = sum(1 for s in all_scores if s < score)
        return rank / len(all_scores)