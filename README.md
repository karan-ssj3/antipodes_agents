# Antipodes AI Agent System

A multi-agent, backtested trading prototype with an interactive Streamlit UI, LLM-generated reports, and rolling A/B experiments.

## Orchestration (High-Level)
- LangGraph workflow (`src/workflow.py`):
  `data_loader → agents (valuation, sentiment, fundamental) → debate → coordinator → backtester → outputs`
- Strict `as_of_date` handling to avoid data leakage
- Outputs saved under `outputs/` and shown in the UI

## Core Logic (High-Level)
- Agents produce BUY/HOLD/SELL with scores; coordinator combines via weighted voting
- Backtester measures 90‑day forward performance vs equal-weight benchmark
- Optional debate step moderates isolated extreme views

## Quickstart
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Optional: .env with API keys (see Environment Variables below)
echo "OPENAI_API_KEY=..." >> .env
echo "FINANCIAL_DATASETS_API_KEY=..." >> .env
echo "LANGCHAIN_API_KEY=..." >> .env
echo "LANGCHAIN_PROJECT=antipodes-agents" >> .env

# Run UI
streamlit run streamlit_app.py

# Or CLI
python main.py --as-of-date 2025-04-01 --verbose
```

## Features
- Streamlit UI to run, inspect, and download results
- LLM Performance Report (markdown) and LLM Optimizer for parameters
- Rolling A/B experiments with CSV export and one‑click promotion
- Per‑ticker attribution CSV and performance chart

## Detailed Docs and Roadmap
- See `docs/overview.md` for architecture, agent logic, backtest details, LLM features, experiments, and roadmap

Note on keys and privacy
- Do not commit your `.env` file; this repo’s `.gitignore` is set to ignore it.
- LLM features (report/optimizer) require `OPENAI_API_KEY`. Without it, LLM options are disabled in the UI.
- Live price data requires `FINANCIAL_DATASETS_API_KEY`; otherwise the app uses `data/fallback_prices.csv`.
- Optional LangSmith tracing supports LangGraph/LangChain observability with `LANGCHAIN_API_KEY` and `LANGCHAIN_PROJECT`.

## Environment Variables (.env)

Environment is loaded via `pydantic-settings` and `python-dotenv`. Create a local `.env` in the project root.

- OPENAI_API_KEY
  - Used by: `src/llm/reporting.py`, `src/llm/optimizer.py`
  - Purpose: Enables LLM Performance Report and LLM Optimizer
  - If missing: LLM features are disabled (UI toggle is off)

- FINANCIAL_DATASETS_API_KEY
  - Used by: `src/data_loader.py` via `src/config.py`
  - Purpose: Fetches live price data from `https://api.financialdatasets.ai`
  - If missing: Uses fallback CSV at `data/fallback_prices.csv`

- LANGCHAIN_API_KEY (optional)
  - Used by: `src/config.py` for LangSmith tracing
  - Purpose: Enable observability/tracing for LangGraph/LangChain runs

- LANGCHAIN_PROJECT (optional)
  - Default: `antipodes-agents`
  - Purpose: Group traces under a project in LangSmith

Example `.env`:

```bash
# LLM (required for LLM features)
OPENAI_API_KEY=sk-...

# Live market data (optional; fallback CSV used if unset)
FINANCIAL_DATASETS_API_KEY=fd-...

# LangSmith tracing (optional)
# Enable v2 tracing by default if key is present
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_PROJECT=antipodes-agents
```

## Data Sources & Quality Controls

### Price Data Pipeline
- **Primary Source**: financialdatasets.ai API for AAPL, MSFT, NVDA, TSLA
- **Fallback System**: Realistic sample data with proper statistical properties
- **Quality Controls**: OHLC validation, volume consistency checks, temporal filtering
- **Leakage Prevention**: Multi-layer as_of_date enforcement with validation

### News Data Management  
- **Source**: Hand-curated headlines from reputable financial sources (Reuters, Bloomberg, company press)
- **Coverage**: 4 articles per ticker from June 2025 (before July 1 decision date)
- **Processing**: VADER sentiment analysis with exponential decay weighting
- **Validation**: Date filtering prevents future information leakage

### Fundamental Data Curation
- **Methodology**: Manual research and compilation of key business metrics
- **Metrics**: Revenue growth, operating margins, leverage ratios, capital efficiency
- **Sources**: 10-K filings, earnings reports, financial databases
- **Update Frequency**: Quarterly refresh aligned with earnings calendar

## Backtesting Methodology

### Forward-Looking Performance Measurement
- **Window**: Exactly 90 days from as_of_date (aligns with quarterly rebalancing)
- **Portfolio Construction**: Equal-weight allocation among BUY-rated positions
- **Benchmark**: Equal-weight allocation across entire 4-ticker universe (25% each)
- **Return Calculation**: Simple buy-and-hold returns assuming perfect execution

### Performance Metrics
- **Total Return**: (End_Price - Start_Price) / Start_Price for portfolio and benchmark
- **Active Return**: Portfolio Return - Benchmark Return (key institutional metric)
- **Sharpe Proxy**: Portfolio Return / Estimated Period Volatility (simplified risk adjustment)
- **Position Count**: Number of BUY-rated positions for concentration risk assessment

### Validation & Controls
- **Temporal Separation**: Agents use only historical data up to as_of_date
- **Future Data**: Backtesting uses extended dataset including future prices
- **Missing Data**: Graceful handling with clear diagnostics when prices unavailable
- **Statistical Significance**: Single-period test for MVP, multi-period validation in production

## Design Philosophy & Trade-offs

### Institutional Investment Principles
**Transparency over Complexity**: Simple, explainable algorithms vs black-box optimization
- **Rationale**: Regulatory compliance and client communication requirements
- **Trade-off**: May sacrifice marginal performance for operational clarity

**Auditability over Optimization**: Complete decision trails vs maximum returns  
- **Rationale**: Fiduciary responsibility and risk management oversight
- **Trade-off**: Additional complexity for compliance vs streamlined execution

**Stability over Marginal Gains**: Conservative risk management vs aggressive positioning
- **Rationale**: Institutional preference for consistent returns over volatile outperformance  
- **Trade-off**: May miss upside opportunities to avoid downside risks

**Risk Control over Maximum Returns**: Defensive defaults and position limits
- **Rationale**: Capital preservation is primary mandate for institutional managers
- **Trade-off**: Lower expected returns for reduced risk of large losses

### Technical Architecture Trade-offs

**Agent Weight Selection (40/30/30):**
- **Decision**: Higher allocation to valuation (momentum) vs equal weighting
- **Rationale**: Empirical evidence for momentum persistence in 1-3 month horizons
- **Trade-off**: Factor concentration risk vs diversified approach
- **Alternative**: Dynamic weight adjustment based on market regime

**Rule-Based vs LLM Implementation:**
- **Decision**: Deterministic algorithms for MVP vs AI-native approach
- **Rationale**: Establish performance baseline and ensure regulatory compliance
- **Trade-off**: Simplicity and auditability vs sophisticated pattern recognition
- **Migration Path**: LLM enhancement of existing agents in Phase 2

**Static vs Dynamic Data:**
- **Decision**: Manual fundamental curation vs real-time data feeds
- **Rationale**: Data quality control and cost management for prototype
- **Trade-off**: Timeliness vs accuracy and system complexity
- **Evolution**: Automated ingestion with human validation checkpoints

## Assumptions & Limitations

### Market Structure Assumptions
- **Perfect Execution**: No transaction costs, market impact, or slippage considered
- **Infinite Liquidity**: Can trade any size in all positions without price movement
- **No Rebalancing**: Buy-and-hold strategy vs dynamic position management
- **Technology Sector Focus**: Results may not generalize to other sectors or market conditions

### System Limitations
- **Universe Constraint**: Limited to 4 large-cap technology stocks
- **Data Coverage**: News sentiment may miss important information sources
- **Temporal Scope**: 90-day backtesting window may not capture longer-term dynamics  
- **Parameter Sensitivity**: Fixed thresholds may not adapt to changing market conditions

### Implementation Simplifications
- **Equal Weight Construction**: Simplified vs sophisticated portfolio optimization
- **Static Agent Weights**: Fixed allocation vs dynamic regime-dependent weighting
- **Single Period Testing**: One backtest vs comprehensive walk-forward validation
- **Fundamental Snapshots**: Manual updates vs real-time fundamental tracking

## Dependencies & Technical Stack

### Core Framework Dependencies
```
langgraph==0.0.26         # Multi-agent workflow orchestration
pydantic==2.4.2           # Data validation and type safety  
pandas==2.1.1             # Data processing and analysis
numpy==1.24.3             # Numerical computations
matplotlib==3.7.2         # Performance visualization
requests==2.31.0          # API integration
```

### Specialized Libraries
```
vaderSentiment==3.3.2     # Financial news sentiment analysis
pydantic-settings==2.0.3  # Environment-based configuration
pathlib                   # Modern file path handling
datetime                  # Temporal data management
typing                    # Type annotations for code clarity
```

### Development & Testing
```
pytest==7.4.3            # Test framework
unittest                 # Python standard testing library
traceback                # Error debugging and reporting
```

## Time Investment Breakdown

### Development Phase Allocation (20 Hours Total)
- **System Architecture & Design**: 3 hours (foundation planning and LangGraph setup)
- **Data Pipeline Development**: 4 hours (API integration, fallback mechanisms, validation)
- **Agent Implementation**: 8 hours (valuation, sentiment, fundamental agents + coordinator)
- **Backtesting Engine**: 2 hours (performance calculation and output generation)
- **Testing & Validation**: 1 hour (test suite development and execution)
- **Documentation**: 2 hours (README, code comments, system documentation)

### Feature Priority Matrix
- **Core Requirements**: 16 hours (agents, coordinator, backtesting, outputs)
- **Bonus Features**: 3 hours (debate round, rolling decisions, robustness testing)  
- **Production Polish**: 1 hour (error handling, logging, CLI interface)

### Quality vs Speed Trade-offs
- **Prioritized**: Correctness, leakage prevention, clear documentation
- **Deferred**: Advanced error recovery, comprehensive logging, performance optimization
- **Future Work**: LLM integration, RAG enhancement, dynamic parameter adjustment

## AI Tool Usage & Development Process

### Claude AI Assistant Integration
- **Project Structure**: Used Claude for initial repository layout and file organization
- **Code Templates**: Generated boilerplate for Pydantic models and base classes
- **Documentation**: Assisted with README structure and technical explanations
- **Code Review**: Validated implementation patterns and architectural decisions

### Human-Led Development Areas
- **Financial Logic**: All investment algorithms and business rules developed manually
- **Agent Strategies**: Risk-adjusted momentum, sentiment analysis, and fundamental scoring designed based on finance domain expertise
- **System Architecture**: LangGraph workflow design and multi-agent coordination patterns
- **Production Engineering**: Error handling, testing, and deployment considerations

### AI-Assisted vs Manual Development
**AI-Enhanced Areas** (~30% of codebase):
- Project scaffolding and configuration management
- Pydantic model definitions and type annotations  
- CLI interface and command-line argument handling
- Basic file I/O and data loading infrastructure

**Manually Developed Areas** (~70% of codebase):
- All financial algorithms and investment logic
- Agent coordination and weighted voting mathematics
- Backtesting methodology and performance attribution
- Business logic, trade-offs, and strategic decisions

This hybrid approach leveraged AI for accelerated development while ensuring all critical financial logic and business decisions were human-designed with proper domain expertise.