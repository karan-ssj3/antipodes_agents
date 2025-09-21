from typing import TypedDict, List, Dict
from datetime import date, timedelta
import json
from langgraph.graph import StateGraph, END

from .models import (
    MarketData, NewsData, FundamentalData, AgentRating, 
    CoordinatorResult, BacktestResult, Rating
)
from .agents.valuation_agent import ValuationAgent
from .agents.sentiment_agent import SentimentAgent
from .agents.fundamental_agent import FundamentalAgent
from .agents.coordinator_agent import Coordinator
from .agents.debate_coordinator import DebateCoordinator
from .data_loader import FinancialDataLoader, NewsLoader, FundamentalLoader
from .backtesting import BacktestEngine, OutputGenerator
from .config import config


class AgentWorkflowState(TypedDict):
    """Shared state across the multi-agent workflow"""
    # Input parameters
    as_of_date: date
    
    # Loaded data
    market_data: MarketData
    news_data: NewsData
    fundamental_data: List[FundamentalData]
    backtest_data: MarketData  
    
    # Agent outputs
    valuation_ratings: List[AgentRating]
    sentiment_ratings: List[AgentRating]
    fundamental_ratings: List[AgentRating]
    
    # Final results
    coordinator_results: List[CoordinatorResult]
    backtest_result: BacktestResult
    
    # Execution tracking
    completed_agents: List[str]
    errors: List[str]
    output_files: Dict[str, str]

class AgentWorkflow:
    """LangGraph-powered multi-agent trading workflow"""
    
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(AgentWorkflowState)
        
        # Add nodes
        workflow.add_node("data_loader", self._data_loader_node)
        workflow.add_node("valuation_agent", self._valuation_agent_node)
        workflow.add_node("sentiment_agent", self._sentiment_agent_node)
        workflow.add_node("fundamental_agent", self._fundamental_agent_node)
        workflow.add_node("coordinator", self._coordinator_node)
        workflow.add_node("backtester", self._backtester_node)
        workflow.add_node("output_generator", self._output_generator_node)
        workflow.add_node("debate_coordinator", self._debate_coordinator_node)
        
        
        # Define the workflow
        workflow.set_entry_point("data_loader")
        
        # Sequential flow for data loading
        workflow.add_edge("data_loader", "valuation_agent")
        workflow.add_edge("valuation_agent", "sentiment_agent")
        workflow.add_edge("sentiment_agent", "fundamental_agent")
        
        # Coordinator waits for all agents
        workflow.add_edge("fundamental_agent", "debate_coordinator") 
        workflow.add_edge("debate_coordinator", "coordinator")
        
        # Backtesting and output generation
        workflow.add_edge("coordinator", "backtester")
        workflow.add_edge("backtester", "output_generator")
        workflow.add_edge("output_generator", END)
        
        return workflow.compile()
    
    def run(self, as_of_date: date) -> AgentWorkflowState:
        """Execute the complete multi-agent workflow"""
        
        print("Starting LangGraph Multi-Agent Workflow")
        print("=" * 50)
        
        # Initialize state
        initial_state = AgentWorkflowState(
            as_of_date=as_of_date,
            completed_agents=[],
            errors=[],
            output_files={}
        )
        
        # Execute workflow
        try:
            final_state = self.workflow.invoke(initial_state)
            print("\n✅ Workflow completed successfully!")
            return final_state
        except Exception as e:
            print(f"\n❌ Workflow failed: {e}")
            raise e
    
    def _data_loader_node(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Node: Load all required data"""
        
        print(" Node: Data Loader")
        
        try:
            as_of_date = state["as_of_date"]
            start_date = as_of_date - timedelta(days=120)
            
            # Load training data (for agent decisions)
            price_loader = FinancialDataLoader()
            market_data = price_loader.fetch_stock_prices(
                config.trading.tickers, start_date, as_of_date, as_of_date
            )
            
            # Load future data (for backtesting only - no redundant historical data)
            future_start = as_of_date + timedelta(days=1)
            future_end = as_of_date + timedelta(days=config.trading.forward_window_days + 10)
            backtest_data = price_loader.fetch_stock_prices(
                config.trading.tickers, future_start, future_end, future_end
            )
            
            # Load news and fundamental data
            news_loader = NewsLoader()
            news_data = news_loader.load_news_data(as_of_date)
            
            fundamental_loader = FundamentalLoader()
            fundamental_data = fundamental_loader.load_fundamental_data()
            
            # Update state
            state["market_data"] = market_data
            state["backtest_data"] = backtest_data
            state["news_data"] = news_data
            state["fundamental_data"] = fundamental_data
            
            print(f"  ✅ Loaded {len(market_data.prices)} training records")
            print(f"  ✅ Loaded {len(backtest_data.prices)} backtest records")
            print(f"  ✅ Loaded {len(news_data.articles)} news articles")
            print(f"  ✅ Loaded {len(fundamental_data)} fundamental records")
            
        except Exception as e:
            state["errors"].append(f"Data loading failed: {e}")
            raise e
        
        return state
    
    def _valuation_agent_node(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Node: Valuation/Momentum Agent"""
        
        print("🔢 Node: Valuation Agent")
        
        try:
            agent = ValuationAgent()
            ratings = agent.analyze(
                state["market_data"], 
                state["news_data"],
                state["fundamental_data"],
                state["as_of_date"]
            )
            
            state["valuation_ratings"] = ratings
            state["completed_agents"].append("valuation")
            
            print(f"  ✅ Generated {len(ratings)} valuation ratings")
            
        except Exception as e:
            state["errors"].append(f"Valuation agent failed: {e}")
            raise e
        
        return state
    
    def _sentiment_agent_node(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Node: Sentiment Agent"""
        
        print("📰 Node: Sentiment Agent")
        
        try:
            agent = SentimentAgent()
            ratings = agent.analyze(
                state["market_data"],
                state["news_data"], 
                state["fundamental_data"],
                state["as_of_date"]
            )
            
            state["sentiment_ratings"] = ratings
            state["completed_agents"].append("sentiment")
            
            print(f"  ✅ Generated {len(ratings)} sentiment ratings")
            
        except Exception as e:
            state["errors"].append(f"Sentiment agent failed: {e}")
            raise e
        
        return state
    
    def _fundamental_agent_node(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Node: Fundamental Agent"""
        
        print("📊 Node: Fundamental Agent")
        
        try:
            agent = FundamentalAgent()
            ratings = agent.analyze(
                state["market_data"],
                state["news_data"],
                state["fundamental_data"],
                state["as_of_date"]
            )
            
            state["fundamental_ratings"] = ratings
            state["completed_agents"].append("fundamental")
            
            print(f"  ✅ Generated {len(ratings)} fundamental ratings")
            
        except Exception as e:
            state["errors"].append(f"Fundamental agent failed: {e}")
            raise e
        
        return state
    
    def _debate_coordinator_node(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Node: Debate Coordinator - agents revise ratings once"""
        
        print("🗣️ Node: Debate Coordinator")
        
        try:
            debate_coord = DebateCoordinator()
            
            # Package initial ratings by agent type
            initial_ratings = {
                "valuation": state["valuation_ratings"],
                "sentiment": state["sentiment_ratings"], 
                "fundamental": state["fundamental_ratings"]
            }
            
            # Conduct debate
            revised_ratings = debate_coord.conduct_debate(
                initial_ratings, 
                state["market_data"], 
                state["as_of_date"]
            )
            
            # Update state with revised ratings
            # Convert back to agent-type lists
            state["valuation_ratings"] = [revised_ratings[ticker]["valuation"] 
                                          for ticker in config.trading.tickers]
            state["sentiment_ratings"] = [revised_ratings[ticker]["sentiment"]
                                          for ticker in config.trading.tickers] 
            state["fundamental_ratings"] = [revised_ratings[ticker]["fundamental"]
                                            for ticker in config.trading.tickers]
            
            revisions_made = sum(1 for ticker in revised_ratings.values() 
                                for agent_results in ticker.values()
                                if "debate" in agent_results.reasoning)
            
            print(f"  ✅ Completed debate round ({revisions_made} revisions made)")
        
        except Exception as e:
            state["errors"].append(f"Debate coordinator failed: {e}")
            raise e
        
        return state
    
    def _coordinator_node(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Node: Coordinator"""
        
        print("🎯 Node: Coordinator")
        
        try:
            coordinator = Coordinator()
            results = coordinator.coordinate(
                state["valuation_ratings"],
                state["sentiment_ratings"],
                state["fundamental_ratings"],
                state["as_of_date"]
            )
            
            state["coordinator_results"] = results
            
            buy_count = len([r for r in results if r.final_rating == Rating.BUY])
            print(f"  ✅ Coordinated {len(results)} decisions ({buy_count} BUY positions)")
            
        except Exception as e:
            state["errors"].append(f"Coordinator failed: {e}")
            raise e
        
        return state
    
    def _backtester_node(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Node: Backtester"""
        
        print("📈 Node: Backtester")
        
        try:
            engine = BacktestEngine()
            result = engine.run_backtest(
                state["coordinator_results"],
                state["backtest_data"],
                state["as_of_date"]
            )
            
            state["backtest_result"] = result
            
            print(f"  ✅ Portfolio return: {result.portfolio_return:.2%}")
            print(f"  ✅ Active return: {result.active_return:.2%}")
            
        except Exception as e:
            state["errors"].append(f"Backtester failed: {e}")
            raise e
        
        return state
    
    
    def _output_generator_node(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Node: Output Generator"""
        
        print("📁 Node: Output Generator")
        
        try:
            generator = OutputGenerator()
            
            # Generate all output files
            picks_file = generator.generate_picks_csv(state["coordinator_results"])
            performance_file = generator.generate_performance_csv(state["backtest_result"])
            
            # Create portfolio positions for chart (must match backtester logic)
            from .models import PortfolioPosition
            from .backtesting import BacktestEngine
            
            # Use the same logic as the backtester
            backtest_engine = BacktestEngine()
            portfolio_positions = backtest_engine._create_portfolio_positions(state["coordinator_results"])
            
            chart_file = generator.generate_chart(state["backtest_result"], portfolio_positions)
            
            # Update state with file paths
            state["output_files"] = {
                "picks": picks_file,
                "performance": performance_file,
                "chart": chart_file
            }
            
            print(f"  ✅ Generated 3 output files")
            
        except Exception as e:
            state["errors"].append(f"Output generation failed: {e}")
            raise e
        
        return state