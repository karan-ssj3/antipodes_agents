# Antipodes AI Agent System

A sophisticated multi-agent trading system that combines momentum analysis, sentiment processing, and fundamental evaluation to generate stock ratings and backtest performance.

## Quick Start
```bash
# Setup
export FINANCIAL_DATASETS_API_KEY=your_key_here
pip install -r requirements.txt

# Run the system
python main.py --as-of-date 2025-07-01 --verbose


System Architecture
Multi-Agent Framework
The system employs three specialized agents coordinated through LangGraph:
Valuation Agent (40% weight)

Strategy: Risk-adjusted momentum using 20-day return / 60-day volatility
Logic: Percentile ranking with >70th percentile=BUY, <30th=SELL
Rationale: Captures short-term price momentum while accounting for risk

Sentiment Agent (30% weight)

Strategy: VADER sentiment analysis on recent headlines with recency weighting
Logic: Weighted sentiment >0.1=BUY, <-0.1=SELL, else HOLD
Rationale: Recent news sentiment often precedes price movements

Fundamental Agent (30% weight)

Strategy: Composite scoring across growth, profitability, leverage, and efficiency
Logic: Composite score >0.7=BUY, <0.4=SELL, else HOLD
Rationale: Quality fundamentals drive long-term performance

Coordinator

Strategy: Weighted voting with tie-breaking (BUY=2, HOLD=1, SELL=0)
Weights: Valuation 40%, Sentiment 30%, Fundamental 30%
Tie-breaking: Defaults to HOLD for stability

Data Sources & Leakage Controls
Price Data: financialdatasets.ai API with fallback to cached data
News Data: Hand-curated headlines from June 2025 (before July 1 decision date)
Fundamental Data: Manually researched metrics for quality assessment
Leakage Prevention:

Strict date filtering: No data after as_of_date used in agent decisions
Separate training/backtesting datasets
Comprehensive validation checks

Backtesting Methodology
Forward Window: Exactly 90 days from as_of_date
Portfolio: Equal-weight all BUY-rated tickers
Benchmark: Equal-weight all 4 tickers (25% each)
Metrics: Buy-and-hold returns with Sharpe proxy
Output Files

picks.csv: Individual agent ratings and final coordinator decisions
performance.csv: Portfolio vs benchmark returns and metrics
chart.png: Performance visualization

Agent Results Example
Ticker  Valuation  Sentiment  Fundamental  Final
AAPL    SELL       BUY        BUY         HOLD
MSFT    BUY        HOLD       BUY         BUY  
NVDA    HOLD       HOLD       BUY         HOLD
TSLA    SELL       HOLD       HOLD        HOLD

Portfolio: 100% MSFT (only BUY position)
Performance: 3.45% vs 10.33% benchmark (-6.88% active)
Technical Implementation
Framework: LangGraph for multi-agent orchestration
Data Models: Pydantic for type safety and validation
Sentiment: VADER sentiment analyzer with recency weighting
Visualization: Matplotlib for performance charts
Testing: Comprehensive test suite with individual agent validation
Limitations & Assumptions

Universe limited to 4 large-cap tech stocks (AAPL, MSFT, NVDA, TSLA)
News sentiment may not capture all market sentiment factors
Fundamental data manually curated (static snapshots)
No transaction costs, market impact, or rebalancing considered
Backtesting assumes perfect execution and liquidity

Time Accounting

Data pipeline & setup: 5 hours
Agent development: 7 hours
Backtesting & outputs: 4 hours
LangGraph integration: 2 hours
Documentation & testing: 2 hours
Total: 20 hours

AI Tool Usage
Used Claude 3.5 Sonnet for initial project structure, Pydantic model design, and code organization. All agent logic, business reasoning, and system architecture developed manually with focus on transparency and auditability.
Commands
bash# Main system
python main.py --as-of-date 2025-07-01

# Individual tests
python main.py test-config
python main.py test-all-agents
python main.py run-langgraph-workflow

# Help
python main.py --help
Dependencies
See requirements.txt for complete list. Key dependencies:

langgraph - Multi-agent orchestration
pydantic - Data validation
vaderSentiment - News sentiment analysis
pandas, numpy - Data processing
matplotlib - Visualization

Environment Variables
bashexport FINANCIAL_DATASETS_API_KEY=your_key_here  # Optional, fallback available
export OPENAI_API_KEY=your_key_here              # Optional
export LANGCHAIN_API_KEY=your_key_here           # Optional for monitoring
