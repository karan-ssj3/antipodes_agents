#!/usr/bin/env python3
"""
Antipodes AI Agent System
Main entry point for the multi-agent trading system
"""

import click
from datetime import datetime, date
from pathlib import Path
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.config import config
from src.data_loader import FinancialDataLoader, NewsLoader, FundamentalLoader
from src.models import MarketData

@click.command()
@click.option(
    '--as-of-date', 
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=datetime(2024, 9, 1).strftime("%Y-%m-%d"),
    help='Decision date for the agents (YYYY-MM-DD format). Default: 2024-09-01'
)
@click.option(
    '--lookback-days',
    type=int,
    default=120,
    help='Days of historical data to fetch. Default: 120'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    default='outputs',
    help='Directory for output files. Default: outputs'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def main(as_of_date: datetime, lookback_days: int, output_dir: str, verbose: bool):
    """
    Antipodes AI Agent System
    
    Run the multi-agent trading system to generate stock ratings and backtest results.
    
    Example:
        python main.py --as-of-date 2025-07-01 --verbose
    """
    
    # Convert to date object
    decision_date = as_of_date.date()
    
    print("🚀 Antipodes AI Agent System")
    print("=" * 50)
    print(f"📅 Decision Date: {decision_date}")
    print(f"📊 Lookback Period: {lookback_days} days")
    print(f"📁 Output Directory: {output_dir}")
    print(f"🎯 Universe: {', '.join(config.trading.tickers)}")
    print(f"🤖 Framework: LangGraph Multi-Agent Orchestration")
    print()
    
    # Ensure output directory exists
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        # Run the LangGraph workflow
        from src.workflow import AgentWorkflow
        
        workflow = AgentWorkflow()
        final_state = workflow.run(decision_date)
        
        # Display summary results
        results = final_state["coordinator_results"]
        backtest = final_state["backtest_result"]
        
        print(f"\n🎯 FINAL RESULTS SUMMARY")
        print("=" * 30)
        
        buy_positions = [r for r in results if r.final_rating.value == "BUY"]
        hold_positions = [r for r in results if r.final_rating.value == "HOLD"]
        sell_positions = [r for r in results if r.final_rating.value == "SELL"]
        
        print(f"BUY: {len(buy_positions)} positions - {[r.ticker for r in buy_positions]}")
        print(f"HOLD: {len(hold_positions)} positions - {[r.ticker for r in hold_positions]}")  
        print(f"SELL: {len(sell_positions)} positions - {[r.ticker for r in sell_positions]}")
        
        print(f"\nPortfolio Return: {backtest.portfolio_return:.2%}")
        print(f"Active Return: {backtest.active_return:.2%}")
        
        print(f"\n📁 Generated Files:")
        for name, path in final_state["output_files"].items():
            print(f"  • {path}")
            
        print(f"\n✅ System completed successfully!")
        
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        if verbose:
            traceback.print_exc()
        sys.exit(1)

def load_data_pipeline(decision_date: date, lookback_days: int, verbose: bool) -> bool:
    """Load and validate all data sources"""
    
    try:
        # Calculate date ranges
        from datetime import timedelta
        start_date = decision_date - timedelta(days=lookback_days)
        
        print(f"📊 Loading price data from {start_date} to {decision_date}")
        
        # Initialize data loaders
        price_loader = FinancialDataLoader()
        news_loader = NewsLoader()
        fundamental_loader = FundamentalLoader()
        
        # Load price data
        market_data = price_loader.fetch_stock_prices(
            tickers=config.trading.tickers,
            start_date=start_date,
            end_date=decision_date,
            as_of_date=decision_date
        )
        
        print(f"✅ Loaded {len(market_data.prices)} price records")
        
        # Validate data coverage
        for ticker in config.trading.tickers:
            ticker_prices = market_data.get_ticker_prices(ticker)
            latest = market_data.get_latest_price(ticker)
            
            if verbose:
                print(f"   {ticker}: {len(ticker_prices)} records, latest: {latest.date if latest else 'None'}")
            
            if not ticker_prices:
                print(f"⚠️  Warning: No price data for {ticker}")
        
        # Load news data
        print("📰 Loading news data...")
        news_data = news_loader.load_news_data(decision_date)
        print(f"✅ Loaded {len(news_data.articles)} news articles")
        
        if verbose:
            for ticker in config.trading.tickers:
                ticker_news = news_data.get_ticker_news(ticker)
                print(f"   {ticker}: {len(ticker_news)} articles")
        
        # Load fundamental data
        print("📋 Loading fundamental data...")
        fundamental_data = fundamental_loader.load_fundamental_data()
        print(f"✅ Loaded fundamental data for {len(fundamental_data)} tickers")
        
        if verbose:
            for fund in fundamental_data:
                print(f"   {fund.ticker}: Quality={fund.quality_score:.2f}, Growth={fund.revenue_growth:.1%}")
        
        # Data validation summary
        print("\n📊 DATA VALIDATION SUMMARY")
        print("-" * 30)
        print(f"Price records: {len(market_data.prices)}")
        print(f"News articles: {len(news_data.articles)}")
        print(f"Fundamental records: {len(fundamental_data)}")
        print(f"Date range: {start_date} to {decision_date}")
        
        # Check for leakage
        future_prices = [p for p in market_data.prices if p.date > decision_date]
        future_news = [n for n in news_data.articles if n.date > decision_date]
        
        if future_prices or future_news:
            print(f"❌ DATA LEAKAGE DETECTED!")
            print(f"   Future prices: {len(future_prices)}")
            print(f"   Future news: {len(future_news)}")
            return False
        
        print("✅ No data leakage detected")
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        if verbose:
            traceback.print_exc()
        return False

@click.group()
def cli():
    """Antipodes AI Agent System CLI"""
    pass

# Add subcommands for testing individual components
@cli.command()
def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    print(f"API Key present: {config.has_financial_api_key}")
    print(f"Trading universe: {config.trading.tickers}")
    print(f"Agent weights: V={config.trading.valuation_weight}, S={config.trading.sentiment_weight}, F={config.trading.fundamental_weight}")
    print("✅ Configuration loaded successfully")

@cli.command()
def test_data():
    """Test data loading without running full pipeline"""
    from datetime import timedelta
    
    decision_date = date(2024, 9, 1)
    start_date = decision_date - timedelta(days=30)
    
    loader = FinancialDataLoader()
    data = loader.fetch_stock_prices(
        config.trading.tickers, 
        start_date, 
        decision_date, 
        decision_date
    )
    print(f"✅ Successfully loaded {len(data.prices)} price records")

@cli.command()
@click.option('--as-of-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              default=datetime(2025, 7, 1).strftime("%Y-%m-%d"))
def test_valuation_agent(as_of_date: datetime):
    """Test the ValuationAgent with loaded data"""
    from src.agents.valuation_agent import ValuationAgent
    from src.data_loader import FinancialDataLoader, NewsLoader, FundamentalLoader
    from datetime import timedelta
    
    decision_date = as_of_date.date()
    start_date = decision_date - timedelta(days=120)
    
    print("🧪 Testing ValuationAgent")
    print("=" * 30)
    
    # Load data
    print("📊 Loading data...")
    price_loader = FinancialDataLoader()
    market_data = price_loader.fetch_stock_prices(
        config.trading.tickers, start_date, decision_date, decision_date
    )
    
    news_loader = NewsLoader()
    news_data = news_loader.load_news_data(decision_date)
    
    fundamental_loader = FundamentalLoader()
    fundamental_data = fundamental_loader.load_fundamental_data()
    
    # Test ValuationAgent
    print("\n🔢 Testing ValuationAgent...")
    agent = ValuationAgent()
    ratings = agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    print(f"Agent: {agent}")
    print("Results:")
    for rating in ratings:
        print(f"  {rating.ticker}: {rating.rating.value} (score: {rating.score:.3f}) - {rating.reasoning}")
    
    print(f"\n✅ ValuationAgent test complete - {len(ratings)} ratings generated")
    
@cli.command()
@click.option('--as-of-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              default=datetime(2025, 7, 1).strftime("%Y-%m-%d"))
def test_both_agents(as_of_date: datetime):
    """Test both ValuationAgent and SentimentAgent"""
    from src.agents.valuation_agent import ValuationAgent
    from src.agents.sentiment_agent import SentimentAgent
    from src.data_loader import FinancialDataLoader, NewsLoader, FundamentalLoader
    from datetime import timedelta
    
    decision_date = as_of_date.date()
    start_date = decision_date - timedelta(days=120)
    
    print("🧪 Testing Both Agents")
    print("=" * 30)
    
    # Load data
    print("📊 Loading data...")
    price_loader = FinancialDataLoader()
    market_data = price_loader.fetch_stock_prices(
        config.trading.tickers, start_date, decision_date, decision_date
    )
    
    news_loader = NewsLoader()
    news_data = news_loader.load_news_data(decision_date)
    
    fundamental_loader = FundamentalLoader()
    fundamental_data = fundamental_loader.load_fundamental_data()
    
    # Test both agents
    print("\n🔢 Testing ValuationAgent...")
    val_agent = ValuationAgent()
    val_ratings = val_agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    print("\n📰 Testing SentimentAgent...")
    sent_agent = SentimentAgent()
    sent_ratings = sent_agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    # Display results side by side
    print("\n📊 COMPARISON RESULTS")
    print("-" * 50)
    print(f"{'Ticker':<6} {'Valuation':<15} {'Sentiment':<15}")
    print("-" * 50)
    
    for ticker in config.trading.tickers:
        val_rating = next(r for r in val_ratings if r.ticker == ticker)
        sent_rating = next(r for r in sent_ratings if r.ticker == ticker)
        
        val_display = f"{val_rating.rating.value} ({val_rating.score:.2f})"
        sent_display = f"{sent_rating.rating.value} ({sent_rating.score:.2f})"
        
        print(f"{ticker:<6} {val_display:<15} {sent_display:<15}")
    
    print(f"\n✅ Both agents tested successfully")
    
@cli.command()
@click.option('--as-of-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              default=datetime(2025, 7, 1).strftime("%Y-%m-%d"))
def test_all_agents(as_of_date: datetime):
    """Test all three agents together"""
    from src.agents.valuation_agent import ValuationAgent
    from src.agents.sentiment_agent import SentimentAgent
    from src.agents.fundamental_agent import FundamentalAgent
    from src.data_loader import FinancialDataLoader, NewsLoader, FundamentalLoader
    from datetime import timedelta
    
    decision_date = as_of_date.date()
    start_date = decision_date - timedelta(days=120)
    
    print("🧪 Testing All Three Agents")
    print("=" * 40)
    
    # Load data
    print("📊 Loading data...")
    price_loader = FinancialDataLoader()
    market_data = price_loader.fetch_stock_prices(
        config.trading.tickers, start_date, decision_date, decision_date
    )
    
    news_loader = NewsLoader()
    news_data = news_loader.load_news_data(decision_date)
    
    fundamental_loader = FundamentalLoader()
    fundamental_data = fundamental_loader.load_fundamental_data()
    
    # Test all agents
    print("\n🔢 Testing ValuationAgent...")
    val_agent = ValuationAgent()
    val_ratings = val_agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    print("\n📰 Testing SentimentAgent...")
    sent_agent = SentimentAgent()
    sent_ratings = sent_agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    print("\n📊 Testing FundamentalAgent...")
    fund_agent = FundamentalAgent()
    fund_ratings = fund_agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    # Display comprehensive results
    print("\n📊 COMPREHENSIVE AGENT COMPARISON")
    print("-" * 65)
    print(f"{'Ticker':<6} {'Valuation':<15} {'Sentiment':<15} {'Fundamental':<15}")
    print("-" * 65)
    
    for ticker in config.trading.tickers:
        val_rating = next(r for r in val_ratings if r.ticker == ticker)
        sent_rating = next(r for r in sent_ratings if r.ticker == ticker)
        fund_rating = next(r for r in fund_ratings if r.ticker == ticker)
        
        val_display = f"{val_rating.rating.value} ({val_rating.score:.2f})"
        sent_display = f"{sent_rating.rating.value} ({sent_rating.score:.2f})"
        fund_display = f"{fund_rating.rating.value} ({fund_rating.score:.2f})"
        
        print(f"{ticker:<6} {val_display:<15} {sent_display:<15} {fund_display:<15}")
    
    print(f"\n✅ All three agents tested successfully")
@cli.command()
@click.option('--as-of-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              default=datetime(2025, 7, 1).strftime("%Y-%m-%d"))
def test_full_system(as_of_date: datetime):
    """Test the complete multi-agent system with coordinator"""
    from src.agents.valuation_agent import ValuationAgent
    from src.agents.sentiment_agent import SentimentAgent
    from src.agents.fundamental_agent import FundamentalAgent
    from src.agents.coordinator_agent import Coordinator
    from src.data_loader import FinancialDataLoader, NewsLoader, FundamentalLoader
    from src.models import Rating
    from datetime import timedelta
    
    decision_date = as_of_date.date()
    start_date = decision_date - timedelta(days=120)
    
    print("🚀 Testing Complete Multi-Agent System")
    print("=" * 50)
    
    # Load data
    print("📊 Loading data...")
    price_loader = FinancialDataLoader()
    market_data = price_loader.fetch_stock_prices(
        config.trading.tickers, start_date, decision_date, decision_date
    )
    
    news_loader = NewsLoader()
    news_data = news_loader.load_news_data(decision_date)
    
    fundamental_loader = FundamentalLoader()
    fundamental_data = fundamental_loader.load_fundamental_data()
    
    # Run all agents
    print("\n🤖 Running All Agents...")
    val_agent = ValuationAgent()
    val_ratings = val_agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    sent_agent = SentimentAgent()
    sent_ratings = sent_agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    fund_agent = FundamentalAgent()
    fund_ratings = fund_agent.analyze(market_data, news_data, fundamental_data, decision_date)
    
    # Coordinate final decisions
    coordinator = Coordinator()
    final_results = coordinator.coordinate(val_ratings, sent_ratings, fund_ratings, decision_date)
    
    # Display final results
    print("\n🎯 FINAL COORDINATED RESULTS")
    print("=" * 80)
    print(f"{'Ticker':<6} {'Val':<8} {'Sent':<8} {'Fund':<8} {'FINAL':<12} {'Score':<8} {'Weights':<15}")
    print("=" * 80)
    
    for result in final_results:
        weights_display = f"V:{config.trading.valuation_weight}/S:{config.trading.sentiment_weight}/F:{config.trading.fundamental_weight}"
        
        print(f"{result.ticker:<6} "
              f"{result.valuation_rating.value:<8} "
              f"{result.sentiment_rating.value:<8} "
              f"{result.fundamental_rating.value:<8} "
              f"{result.final_rating.value:<12} "
              f"{result.final_score:.3f}{'':4} "
              f"{weights_display}")
    
    # Show portfolio implications
    buy_positions = [r for r in final_results if r.final_rating == Rating.BUY]
    hold_positions = [r for r in final_results if r.final_rating == Rating.HOLD]
    sell_positions = [r for r in final_results if r.final_rating == Rating.SELL]
    
    print(f"\n📊 PORTFOLIO SUMMARY")
    print("-" * 30)
    print(f"BUY positions: {len(buy_positions)} - {[r.ticker for r in buy_positions]}")
    print(f"HOLD positions: {len(hold_positions)} - {[r.ticker for r in hold_positions]}")
    print(f"SELL positions: {len(sell_positions)} - {[r.ticker for r in sell_positions]}")
    
    if buy_positions:
        print(f"\nPortfolio allocation (equal weight BUY positions):")
        weight_per_position = 1.0 / len(buy_positions)
        for position in buy_positions:
            print(f"  {position.ticker}: {weight_per_position:.1%}")
    else:
        print("\nNo BUY positions - portfolio would be in cash")
    
    print(f"\n✅ Complete system test successful!")
    return final_results

@cli.command()
@click.option('--as-of-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              default=datetime(2025, 7, 1).strftime("%Y-%m-%d"))
def test_backtest(as_of_date: datetime):
    """Test the complete system with backtesting and outputs"""
    from src.agents.valuation_agent import ValuationAgent
    from src.agents.sentiment_agent import SentimentAgent
    from src.agents.fundamental_agent import FundamentalAgent
    from src.agents.coordinator_agent import Coordinator
    from src.data_loader import FinancialDataLoader, NewsLoader, FundamentalLoader
    from src.backtesting import BacktestEngine, OutputGenerator
    from datetime import timedelta
    
    decision_date = as_of_date.date()
    start_date = decision_date - timedelta(days=120)
    
    print("🧪 Testing Complete System with Backtesting")
    print("=" * 55)
    
    # Load training data (up to as_of_date - for agents)
    print("📊 Loading training data for agent decisions...")
    price_loader = FinancialDataLoader()
    training_data = price_loader.fetch_stock_prices(
        config.trading.tickers, start_date, decision_date, decision_date
    )
    
    # Load future data (for backtesting only - no redundant historical data)
    print("📈 Loading future data for backtesting...")
    future_start = decision_date + timedelta(days=1)
    future_end = decision_date + timedelta(days=config.trading.forward_window_days + 10)
    backtest_data = price_loader.fetch_stock_prices(
        config.trading.tickers, future_start, future_end, future_end
    )
    
    news_loader = NewsLoader()
    news_data = news_loader.load_news_data(decision_date)
    
    fundamental_loader = FundamentalLoader()
    fundamental_data = fundamental_loader.load_fundamental_data()
    
    print(f"✅ Training data: {len(training_data.prices)} records (up to {decision_date})")
    print(f"✅ Backtest data: {len(backtest_data.prices)} records (includes future data)")
    
    # Run agents (using only training data)
    print("\n🤖 Running agent analysis...")
    val_agent = ValuationAgent()
    val_ratings = val_agent.analyze(training_data, news_data, fundamental_data, decision_date)
    
    sent_agent = SentimentAgent()
    sent_ratings = sent_agent.analyze(training_data, news_data, fundamental_data, decision_date)
    
    fund_agent = FundamentalAgent()
    fund_ratings = fund_agent.analyze(training_data, news_data, fundamental_data, decision_date)
    
    coordinator = Coordinator()
    coordinator_results = coordinator.coordinate(val_ratings, sent_ratings, fund_ratings, decision_date)
    
    # Run backtest (using extended data with future prices)
    print("\n📈 Running backtest...")
    backtest_engine = BacktestEngine()
    backtest_result = backtest_engine.run_backtest(coordinator_results, backtest_data, decision_date)
    
    # Generate outputs
    print("\n📁 Generating output files...")
    output_gen = OutputGenerator()
    
    picks_file = output_gen.generate_picks_csv(coordinator_results)
    performance_file = output_gen.generate_performance_csv(backtest_result)
    
    # Create portfolio positions for chart
    buy_positions = [r for r in coordinator_results if r.final_rating.value == "BUY"]
    portfolio_positions = []
    if buy_positions:
        weight = 1.0 / len(buy_positions)
        for result in coordinator_results:
            from src.models import PortfolioPosition
            pos = PortfolioPosition(
                ticker=result.ticker,
                weight=weight if result.final_rating.value == "BUY" else 0.0,
                rating=result.final_rating
            )
            portfolio_positions.append(pos)
    else:
        # No BUY positions - create equal-weight portfolio
        weight = 1.0 / len(coordinator_results)
        for result in coordinator_results:
            from src.models import PortfolioPosition
            pos = PortfolioPosition(
                ticker=result.ticker,
                weight=weight,
                rating=result.final_rating
            )
            portfolio_positions.append(pos)
    
    chart_file = output_gen.generate_chart(backtest_result, portfolio_positions)
    
    # Display results summary
    print(f"\n📊 BACKTEST RESULTS SUMMARY")
    print("-" * 40)
    print(f"Portfolio Return: {backtest_result.portfolio_return:.2%}")
    print(f"Benchmark Return: {backtest_result.benchmark_return:.2%}") 
    print(f"Active Return: {backtest_result.active_return:.2%}")
    print(f"Sharpe Ratio: {backtest_result.sharpe_ratio:.3f}")
    print(f"BUY Positions: {backtest_result.num_buy_positions}")
    print(f"Period: {backtest_result.start_date} to {backtest_result.end_date}")
    
    if backtest_result.active_return > 0:
        print("🎉 Portfolio OUTPERFORMED benchmark!")
    else:
        print("📉 Portfolio underperformed benchmark")
    
    print(f"\n📁 OUTPUT FILES GENERATED:")
    print(f"  • {picks_file}")
    print(f"  • {performance_file}")
    print(f"  • {chart_file}")
    
    print(f"\n✅ Complete system test with backtesting successful!")
    
@cli.command()
@click.option('--as-of-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              default=datetime(2025, 7, 1).strftime("%Y-%m-%d"))
def run_langgraph_workflow(as_of_date: datetime):
    """Run the complete system using LangGraph orchestration"""
    from src.workflow import AgentWorkflow
    
    decision_date = as_of_date.date()
    
    print(f"🎯 Running Antipodes AI Agent System")
    print(f"📅 Decision Date: {decision_date}")
    print(f"🔧 Framework: LangGraph Multi-Agent Orchestration")
    print()
    
    # Initialize and run workflow
    workflow = AgentWorkflow()
    final_state = workflow.run(decision_date)
    
    # Display final results
    results = final_state["coordinator_results"]
    backtest = final_state["backtest_result"]
    
    print(f"\n🎯 FINAL TRADING DECISIONS")
    print("=" * 40)
    for result in results:
        print(f"{result.ticker}: {result.final_rating.value} (score: {result.final_score:.3f})")
    
    buy_positions = [r for r in results if r.final_rating.value == "BUY"]
    
    print(f"\n📊 BACKTEST PERFORMANCE")
    print("-" * 30)
    print(f"Portfolio Return: {backtest.portfolio_return:.2%}")
    print(f"Benchmark Return: {backtest.benchmark_return:.2%}")
    print(f"Active Return: {backtest.active_return:.2%}")
    print(f"Sharpe Ratio: {backtest.sharpe_ratio:.3f}")
    
    if backtest.active_return > 0:
        print("🎉 OUTPERFORMED benchmark!")
    else:
        print("📉 Underperformed benchmark")
    
    print(f"\n📁 OUTPUT FILES:")
    for name, path in final_state["output_files"].items():
        print(f"  • {name}: {path}")
    
    if final_state["errors"]:
        print(f"\n⚠️ Errors encountered:")
        for error in final_state["errors"]:
            print(f"  • {error}")
    
    print(f"\n✅ LangGraph workflow completed successfully!")

@cli.command()
def test_rolling_decisions():
    """Test system stability across multiple dates (bonus requirement)"""
    from src.workflow import AgentWorkflow
    
    test_dates = [
        date(2025, 5, 1),
        date(2025, 6, 1), 
        date(2025, 7, 1)
    ]
    
    print("📊 Testing Rolling Decisions Across Multiple Dates")
    print("=" * 55)
    
    results_by_date = {}
    
    for test_date in test_dates:
        print(f"\n📅 Running system for: {test_date}")
        
        try:
            workflow = AgentWorkflow()
            final_state = workflow.run(test_date)
            
            # Extract decision data
            decisions = {}
            for result in final_state["coordinator_results"]:
                decisions[result.ticker] = {
                    "rating": result.final_rating.value,
                    "score": result.final_score,
                    "val_rating": result.valuation_rating.value,
                    "sent_rating": result.sentiment_rating.value,
                    "fund_rating": result.fundamental_rating.value
                }
            
            results_by_date[test_date.isoformat()] = decisions
            
        except Exception as e:
            print(f"  ❌ Failed for {test_date}: {e}")
            continue
    
    # Stability Analysis
    print(f"\n📈 SYSTEM STABILITY ANALYSIS")
    print("=" * 35)
    print(f"{'Ticker':<6} {'Ratings Across Dates':<25} {'Stability':<12}")
    print("-" * 45)
    
    for ticker in config.trading.tickers:
        try:
            ratings = [results_by_date[d][ticker]["rating"] for d in results_by_date.keys()]
            stability_score = 1 - (len(set(ratings)) - 1) / (len(ratings) - 1) if len(ratings) > 1 else 1.0
            
            print(f"{ticker:<6} {' -> '.join(ratings):<25} {stability_score:.1%}")
            
        except KeyError:
            print(f"{ticker:<6} {'DATA MISSING':<25} {'N/A'}")
    
    print(f"\n✅ Rolling decisions test completed")
    return results_by_date

@cli.command()
@click.option('--as-of-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              default=datetime(2025, 7, 1).strftime("%Y-%m-%d"))
def test_robustness(as_of_date: datetime):
    """Test robustness to weight changes (bonus requirement)"""
    from src.workflow import AgentWorkflow
    from src.robustness import RobustnessChecker
    
    decision_date = as_of_date.date()
    
    print("🔍 Testing System Robustness")
    print("=" * 35)
    
    # Run base system
    workflow = AgentWorkflow()
    final_state = workflow.run(decision_date)
    
    # Extract agent ratings
    val_ratings = final_state["valuation_ratings"]
    sent_ratings = final_state["sentiment_ratings"] 
    fund_ratings = final_state["fundamental_ratings"]
    
    # Test weight sensitivity
    checker = RobustnessChecker()
    sensitivity_results = checker.test_weight_sensitivity(
        val_ratings, sent_ratings, fund_ratings, decision_date
    )
    
    checker.print_sensitivity_analysis(sensitivity_results)
    
    print(f"\n✅ Robustness testing completed")

if __name__ == "__main__":
    # If run with no arguments, run main command with defaults
    if len(sys.argv) == 1:
        main()
    else:
        # Check if it's a subcommand (starts with a command name, not an option)
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            cli()
        else:
            # Check if it's a main command (has --verbose, --as-of-date, etc.)
            main_options = ['--verbose', '-v', '--as-of-date', '--lookback-days', '--output-dir']
            if any(opt in sys.argv for opt in main_options):
                main()
            else:
                cli()