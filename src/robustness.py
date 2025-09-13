from typing import List, Dict
from .models import AgentRating, AgentType
from .agents.coordinator_agent import Coordinator
from .config import config

class RobustnessChecker:
    """Test system sensitivity to parameter changes"""
    
    def test_weight_sensitivity(self, valuation_ratings: List[AgentRating],
                               sentiment_ratings: List[AgentRating], 
                               fundamental_ratings: List[AgentRating],
                               as_of_date) -> Dict:
        """Test different agent weight combinations"""
        
        weight_scenarios = [
            {"name": "Current", "val": 0.4, "sent": 0.3, "fund": 0.3},
            {"name": "Equal Weight", "val": 0.33, "sent": 0.33, "fund": 0.34},
            {"name": "Valuation Heavy", "val": 0.6, "sent": 0.2, "fund": 0.2},
            {"name": "Fundamental Heavy", "val": 0.2, "sent": 0.2, "fund": 0.6},
        ]
        
        results = {}
        
        # Store original weights
        original_weights = (
            config.trading.valuation_weight,
            config.trading.sentiment_weight,
            config.trading.fundamental_weight
        )
        
        for scenario in weight_scenarios:
            # Set new weights
            config.trading.valuation_weight = scenario["val"]
            config.trading.sentiment_weight = scenario["sent"] 
            config.trading.fundamental_weight = scenario["fund"]
            
            # Re-coordinate with new weights
            coordinator = Coordinator()
            coord_results = coordinator.coordinate(
                valuation_ratings, sentiment_ratings, fundamental_ratings, as_of_date
            )
            
            # Store results
            results[scenario["name"]] = {
                r.ticker: r.final_rating.value for r in coord_results
            }
        
        # Restore original weights
        config.trading.valuation_weight = original_weights[0]
        config.trading.sentiment_weight = original_weights[1] 
        config.trading.fundamental_weight = original_weights[2]
        
        return results
    
    def print_sensitivity_analysis(self, results: Dict):
        """Print weight sensitivity analysis"""
        
        print("🔍 WEIGHT SENSITIVITY ANALYSIS")
        print("-" * 40)
        print(f"{'Ticker':<6} {'Current':<8} {'Equal':<8} {'Val Heavy':<10} {'Fund Heavy':<10}")
        print("-" * 45)
        
        for ticker in config.trading.tickers:
            row = f"{ticker:<6}"
            for scenario in ["Current", "Equal Weight", "Valuation Heavy", "Fundamental Heavy"]:
                rating = results[scenario][ticker]
                row += f" {rating:<8}"
            print(row)