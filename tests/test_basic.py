import unittest
import sys
from pathlib import Path
from datetime import date, timedelta
import pandas as pd

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.config import config
from src.data_loader import FinancialDataLoader, NewsLoader, FundamentalLoader
from src.models import StockPrice, MarketData, NewsItem, NewsData, Rating
from src.agents.valuation_agent import ValuationAgent
from src.agents.coordinator_agent import Coordinator
from src.backtesting import BacktestEngine

class TestDataLoader(unittest.TestCase):
    """Test data loading functionality"""
    
    def test_price_data_leakage_prevention(self):
        """Test that price data respects as_of_date"""
        loader = FinancialDataLoader()
        as_of_date = date(2024, 9, 1)
        start_date = as_of_date - timedelta(days=30)
        future_end_date = as_of_date + timedelta(days=30)  # Future date
        
        # Should automatically adjust end_date to as_of_date
        market_data = loader.fetch_stock_prices(
            ["AAPL"], start_date, future_end_date, as_of_date
        )
        
        # Verify no prices after as_of_date
        for price in market_data.prices:
            self.assertLessEqual(price.date, as_of_date, 
                               "Price data leaked beyond as_of_date")
    
    def test_news_data_leakage_prevention(self):
        """Test that news data respects as_of_date"""
        loader = NewsLoader()
        as_of_date = date(2025, 6, 15)  # Earlier than some sample news dates
        
        news_data = loader.load_news_data(as_of_date)
        
        # Verify no news after as_of_date
        for article in news_data.articles:
            self.assertLessEqual(article.date, as_of_date,
                               "News data leaked beyond as_of_date")

class TestAgentBehavior(unittest.TestCase):
    """Test agent rating logic"""
    
    def test_valuation_agent_returns_valid_ratings(self):
        """Test valuation agent produces valid outputs"""
        # Create sample market data
        prices = [
            StockPrice(ticker="AAPL", date=date(2024, 8, 1), 
                      open_price=180, high_price=185, low_price=178, 
                      close_price=182, volume=1000000),
            StockPrice(ticker="AAPL", date=date(2024, 8, 30), 
                      open_price=190, high_price=195, low_price=188, 
                      close_price=193, volume=1200000)
        ]
        market_data = MarketData(prices=prices, as_of_date=date(2024, 8, 30))
        
        agent = ValuationAgent()
        ratings = agent.analyze(market_data, NewsData(articles=[], as_of_date=date(2024, 8, 30)), 
                               [], date(2024, 8, 30))
        
        # Should return ratings for all tickers
        self.assertEqual(len(ratings), len(config.trading.tickers))
        
        for rating in ratings:
            # Valid rating enum
            self.assertIn(rating.rating, [Rating.BUY, Rating.HOLD, Rating.SELL])
            # Score in valid range
            self.assertGreaterEqual(rating.score, 0.0)
            self.assertLessEqual(rating.score, 1.0)
            # Has reasoning
            self.assertIsInstance(rating.reasoning, str)
            self.assertGreater(len(rating.reasoning), 0)

class TestCoordinator(unittest.TestCase):
    """Test coordinator logic"""
    
    def test_weighted_voting_math(self):
        """Test coordinator weighted voting calculations"""
        from src.models import AgentRating, AgentType
        
        # Create sample ratings
        val_ratings = [AgentRating(agent_type=AgentType.VALUATION, ticker="AAPL", 
                                  rating=Rating.BUY, score=0.8, reasoning="test", 
                                  as_of_date=date(2024, 9, 1))]
        sent_ratings = [AgentRating(agent_type=AgentType.SENTIMENT, ticker="AAPL", 
                                   rating=Rating.HOLD, score=0.5, reasoning="test", 
                                   as_of_date=date(2024, 9, 1))]
        fund_ratings = [AgentRating(agent_type=AgentType.FUNDAMENTAL, ticker="AAPL", 
                                   rating=Rating.SELL, score=0.2, reasoning="test", 
                                   as_of_date=date(2024, 9, 1))]
        
        coordinator = Coordinator()
        results = coordinator.coordinate(val_ratings, sent_ratings, fund_ratings, 
                                       date(2024, 9, 1))
        
        # Should return result for all configured tickers (4 total)
        self.assertEqual(len(results), 4)
        
        # Find the AAPL result
        aapl_result = next((r for r in results if r.ticker == "AAPL"), None)
        self.assertIsNotNone(aapl_result, "Should have result for AAPL")
        result = aapl_result
        
        # Verify ratings are preserved
        self.assertEqual(result.valuation_rating, Rating.BUY)
        self.assertEqual(result.sentiment_rating, Rating.HOLD)
        self.assertEqual(result.fundamental_rating, Rating.SELL)
        
        # Verify final rating is calculated
        self.assertIn(result.final_rating, [Rating.BUY, Rating.HOLD, Rating.SELL])

class TestBacktesting(unittest.TestCase):
    """Test backtesting calculations"""
    
    def test_return_calculation(self):
        """Test simple return calculation"""
        engine = BacktestEngine()
        
        # Create test price data with known return
        prices = [
            StockPrice(ticker="TEST", date=date(2024, 9, 1), 
                      open_price=100, high_price=105, low_price=98, 
                      close_price=100, volume=1000),
            StockPrice(ticker="TEST", date=date(2024, 12, 1), 
                      open_price=110, high_price=115, low_price=108, 
                      close_price=110, volume=1100)
        ]
        market_data = MarketData(prices=prices, as_of_date=date(2024, 12, 1))
        
        # Calculate return
        ret = engine._calculate_ticker_return("TEST", market_data, 
                                            date(2024, 9, 1), date(2024, 12, 1))
        
        # Should be 10% return (100 to 110)
        self.assertAlmostEqual(ret, 0.10, places=4)

class TestConfigurationIntegrity(unittest.TestCase):
    """Test configuration consistency"""
    
    def test_weights_sum_to_one(self):
        """Test that agent weights sum to 1.0"""
        total_weight = (config.trading.valuation_weight + 
                       config.trading.sentiment_weight + 
                       config.trading.fundamental_weight)
        self.assertAlmostEqual(total_weight, 1.0, places=2, 
                              msg="Agent weights should sum to 1.0")
    
    def test_thresholds_are_sensible(self):
        """Test that rating thresholds make sense"""
        self.assertGreater(config.trading.buy_threshold, 0.5, 
                          "Buy threshold should be > 50%")
        self.assertLess(config.trading.sell_threshold, 0.5, 
                       "Sell threshold should be < 50%")
        self.assertGreater(config.trading.buy_threshold, 
                          config.trading.sell_threshold,
                          "Buy threshold should be > sell threshold")

if __name__ == "__main__":
    unittest.main()