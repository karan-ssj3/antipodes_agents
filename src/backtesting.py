import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

from .models import CoordinatorResult, MarketData, BacktestResult, Rating, PortfolioPosition
from .config import config

class BacktestEngine:
    """
    Backtesting engine for agent decisions
    
    Methodology:
    1. Forward window: Exactly 3 months (90 days) from as_of_date
    2. Portfolio: Equal-weight all BUY-rated tickers
    3. Benchmark: Equal-weight all 4 tickers (25% each)
    4. Returns: Simple buy-and-hold returns
    5. Metrics: Total return, active return, Sharpe proxy
    """
    
    def __init__(self):
        self.name = "Backtest Engine"
    
    def run_backtest(self, 
                    coordinator_results: List[CoordinatorResult],
                    market_data: MarketData,
                    as_of_date: date) -> BacktestResult:
        """Run complete backtest analysis"""
        
        print(f"📊 Running backtest from {as_of_date}...")
        
        # Create portfolio weights from coordinator decisions
        portfolio_positions = self._create_portfolio_positions(coordinator_results)
        
        # Calculate forward returns
        forward_start = as_of_date + timedelta(days=1)
        forward_end = as_of_date + timedelta(days=config.trading.forward_window_days)
        
        portfolio_return = self._calculate_portfolio_return(
            portfolio_positions, market_data, forward_start, forward_end
        )
        
        benchmark_return = self._calculate_benchmark_return(
            market_data, forward_start, forward_end
        )
        
        # Calculate metrics
        active_return = portfolio_return - benchmark_return
        sharpe_ratio = self._calculate_sharpe_proxy(
            portfolio_positions, market_data, forward_start, forward_end
        )
        
        return BacktestResult(
            portfolio_return=portfolio_return,
            benchmark_return=benchmark_return,
            active_return=active_return,
            sharpe_ratio=sharpe_ratio,
            num_buy_positions=len([p for p in portfolio_positions if p.weight > 0]),
            start_date=forward_start,
            end_date=forward_end
        )
    
    def _create_portfolio_positions(self, 
                                   coordinator_results: List[CoordinatorResult]) -> List[PortfolioPosition]:
        """Create portfolio positions from coordinator decisions"""
        
        buy_positions = [r for r in coordinator_results if r.final_rating == Rating.BUY]
        
        if not buy_positions:
            # No BUY positions - equal weight everything or cash
            # For simplicity, equal weight all positions with HOLD rating
            hold_positions = [r for r in coordinator_results if r.final_rating == Rating.HOLD]
            if hold_positions:
                weight_per_position = 1.0 / len(hold_positions)
                positions = []
                for result in coordinator_results:
                    weight = weight_per_position if result.final_rating == Rating.HOLD else 0.0
                    positions.append(PortfolioPosition(
                        ticker=result.ticker,
                        weight=weight,
                        rating=result.final_rating
                    ))
                return positions
            else:
                # All SELL - return empty portfolio (cash)
                return [PortfolioPosition(ticker=r.ticker, weight=0.0, rating=r.final_rating) 
                       for r in coordinator_results]
        else:
            # Equal weight all BUY positions
            weight_per_buy = 1.0 / len(buy_positions)
            positions = []
            
            for result in coordinator_results:
                weight = weight_per_buy if result.final_rating == Rating.BUY else 0.0
                positions.append(PortfolioPosition(
                    ticker=result.ticker,
                    weight=weight,
                    rating=result.final_rating
                ))
                
            return positions
    
    def _calculate_portfolio_return(self,
                                   positions: List[PortfolioPosition],
                                   market_data: MarketData,
                                   start_date: date,
                                   end_date: date) -> float:
        """Calculate portfolio return over forward period"""
        
        total_return = 0.0
        
        for position in positions:
            if position.weight == 0:
                continue
                
            ticker_return = self._calculate_ticker_return(
                position.ticker, market_data, start_date, end_date
            )
            
            weighted_return = ticker_return * position.weight
            total_return += weighted_return
            
        return total_return
    
    def _calculate_benchmark_return(self,
                                   market_data: MarketData,
                                   start_date: date,
                                   end_date: date) -> float:
        """Calculate equal-weight benchmark return"""
        
        weight_per_ticker = 1.0 / len(config.trading.tickers)
        total_return = 0.0
        
        for ticker in config.trading.tickers:
            ticker_return = self._calculate_ticker_return(
                ticker, market_data, start_date, end_date
            )
            weighted_return = ticker_return * weight_per_ticker
            total_return += weighted_return
            
        return total_return
    
    def _calculate_ticker_return(self,
                                ticker: str,
                                market_data: MarketData,
                                start_date: date,
                                end_date: date) -> float:
        """Calculate simple return for a single ticker"""
        
        ticker_prices = market_data.get_ticker_prices(ticker)
        
        if not ticker_prices:
            print(f"  ⚠️  No price data for {ticker}")
            return 0.0
        
        # Sort prices by date
        sorted_prices = sorted(ticker_prices, key=lambda p: p.date)
        
        # Find closest start price (first price on or after start_date)
        start_price = None
        for price in sorted_prices:
            if price.date >= start_date:
                start_price = price.close_price
                break
        
        # Find closest end price (last price on or before end_date)
        end_price = None
        for price in reversed(sorted_prices):
            if price.date <= end_date:
                end_price = price.close_price
                break
        
        if start_price is None or end_price is None:
            print(f"  ⚠️  Missing price data for {ticker} in backtest period ({start_date} to {end_date})")
            if sorted_prices:
                print(f"      Available: {sorted_prices[0].date} to {sorted_prices[-1].date}")
            return 0.0
        
        return (end_price - start_price) / start_price
    
    def _calculate_sharpe_proxy(self,
                               positions: List[PortfolioPosition],
                               market_data: MarketData,
                               start_date: date,
                               end_date: date) -> float:
        """Calculate simple Sharpe-style ratio"""
        
        portfolio_return = self._calculate_portfolio_return(
            positions, market_data, start_date, end_date
        )
        
        # Simple proxy: return / assumed volatility
        # For this assessment, we'll use a simple heuristic
        assumed_daily_vol = 0.02  # 2% daily volatility assumption
        days_in_period = (end_date - start_date).days
        period_vol = assumed_daily_vol * np.sqrt(days_in_period)
        
        if period_vol == 0:
            return 0.0
            
        return portfolio_return / period_vol

class OutputGenerator:
    """Generate required CSV and PNG outputs"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_picks_csv(self, coordinator_results: List[CoordinatorResult]) -> str:
        """Generate picks.csv file"""
        
        picks_data = []
        
        for result in coordinator_results:
            picks_data.append({
                'ticker': result.ticker,
                'valuation_rating': result.valuation_rating.value,
                'valuation_score': round(result.valuation_score, 3),
                'sentiment_rating': result.sentiment_rating.value,
                'sentiment_score': round(result.sentiment_score, 3),
                'fundamental_rating': result.fundamental_rating.value,
                'fundamental_score': round(result.fundamental_score, 3),
                'final_rating': result.final_rating.value,
                'final_score': round(result.final_score, 3)
            })
        
        df = pd.DataFrame(picks_data)
        picks_file = self.output_dir / "picks.csv"
        df.to_csv(picks_file, index=False)
        
        print(f"✅ Generated {picks_file}")
        return str(picks_file)
    
    def generate_performance_csv(self, backtest_result: BacktestResult) -> str:
        """Generate performance.csv file"""
        
        performance_data = [
            {'metric': 'portfolio_return', 'value': round(backtest_result.portfolio_return, 4)},
            {'metric': 'benchmark_return', 'value': round(backtest_result.benchmark_return, 4)},
            {'metric': 'active_return', 'value': round(backtest_result.active_return, 4)},
            {'metric': 'sharpe_ratio', 'value': round(backtest_result.sharpe_ratio, 3)},
            {'metric': 'num_buy_positions', 'value': backtest_result.num_buy_positions}
        ]
        
        df = pd.DataFrame(performance_data)
        performance_file = self.output_dir / "performance.csv"
        df.to_csv(performance_file, index=False)
        
        print(f"✅ Generated {performance_file}")
        return str(performance_file)
    
    def generate_chart(self, 
                      backtest_result: BacktestResult,
                      portfolio_positions: List[PortfolioPosition]) -> str:
        """Generate performance chart PNG"""
        
        # Create simple performance visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Simple bar chart of returns
        categories = ['Portfolio', 'Benchmark', 'Active']
        returns = [
            backtest_result.portfolio_return,
            backtest_result.benchmark_return, 
            backtest_result.active_return
        ]
        
        colors = ['blue' if r >= 0 else 'red' for r in returns]
        
        bars = ax.bar(categories, returns, color=colors, alpha=0.7)
        
        # Add value labels on bars
        for bar, value in zip(bars, returns):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                   f'{value:.1%}', ha='center', va='bottom')
        
        ax.set_ylabel('Return')
        ax.set_title(f'Portfolio Performance vs Benchmark\n'
                    f'({backtest_result.start_date} to {backtest_result.end_date})')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Format y-axis as percentages
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
        
        plt.tight_layout()
        
        chart_file = self.output_dir / "chart.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Generated {chart_file}")
        return str(chart_file)