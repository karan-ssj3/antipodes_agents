# Antipodes AI Agent System

A production-ready multi-agent trading system demonstrating institutional-grade portfolio construction with bias reduction, stability testing, and comprehensive risk controls.

## Executive Summary

Built a sophisticated multi-agent framework that mirrors real investment committee workflows, with three specialized agents coordinating through weighted voting to generate stock ratings and backtest performance. The system emphasizes transparency, auditability, and production deployment readiness while establishing a scalable foundation for advanced AI integration.

---

# What’s New (UI + LLM + Experiments)

- Streamlit UI (`streamlit_app.py`) to run the whole workflow interactively
- LLM Performance Report: generates `outputs/performance_report.md` with grounded attribution
- LLM Optimizer: proposes parameter changes (weights/thresholds/window) as JSON
- Rolling A/B Experiments: compare Baseline vs Variant across multiple dates
- Per‑ticker Attribution CSV: `outputs/attribution.csv` with return and contribution
- Config Versioning: save promoted configs to `outputs/experiments/configs/` and roll back via UI

# PART I: CURRENT IMPLEMENTATION

## System Architecture

### Multi-Agent Framework
**Valuation Agent (40% weight)** - Risk-adjusted momentum analysis
- Strategy: 20-day return / 60-day volatility with percentile ranking
- Logic: Captures price momentum while normalizing for risk exposure
- Implementation: Cross-sectional ranking prevents absolute threshold drift
- Rationale: Momentum effects dominate 1-3 month horizons (our backtest window)

**Sentiment Agent (30% weight)** - News sentiment with recency weighting  
- Strategy: VADER analysis with exponential decay for recent headlines
- Logic: Combines title + snippet analysis with 0.9^days decay weighting
- Implementation: Absolute thresholds (-0.1 to +0.1) for meaningful sentiment interpretation
- Rationale: Recent news sentiment often precedes price movements, decay reflects information half-life

**Fundamental Agent (30% weight)** - Composite quality scoring
- Strategy: Equal-weight Growth + Profitability + Leverage + Efficiency metrics
- Logic: Revenue growth (25%), Operating margin (25%), D/E ratio (25%), CapEx intensity (25%)
- Implementation: Industry-appropriate scaling with absolute quality thresholds (0.7 BUY, 0.4 SELL)
- Rationale: Quality fundamentals provide stability anchor preventing momentum chasing into poor businesses

**Coordinator** - Weighted voting with sophisticated tie-breaking
- Strategy: Converts ratings to 0-2 scale, applies agent weights, converts back to BUY/HOLD/SELL
- Logic: Uses config thresholds (0.7/0.3) scaled to 0-2 coordinate system (1.4/0.6)
- Implementation: Mathematical weighted averaging with defensive defaults for missing data
- Rationale: Democratic decision-making with expertise weighting reflects investment committee best practices

## Advanced Features Implemented

### Debate Round - Bias Reduction Mechanism
- **Isolation Detection**: Identifies agents holding extreme positions without peer support
- **Mathematical Moderation**: 0.8x score reduction for isolated BUY/SELL positions  
- **Audit Trail**: Preserves original reasoning while documenting debate influence
- **Single Round Limit**: Prevents analysis paralysis while reducing overconfidence bias

### Rolling Decisions - Stability Validation
- **Multi-Date Testing**: Validates decision consistency across 2025-05-01, 2025-06-01, 2025-07-01
- **Stability Scoring**: Measures rating consistency using (1 - unique_ratings/total_ratings)
- **Agent Reliability**: Identifies which specialists provide stable vs volatile recommendations

### Robustness Checks - Parameter Sensitivity Analysis
- **Weight Scenarios**: Current (40/30/30), Equal (33/33/34), Valuation Heavy (60/20/20), Fundamental Heavy (20/20/60)
- **Decision Mapping**: Shows which stocks are weight-sensitive vs stable across scenarios
- **Risk Assessment**: Identifies decisions that depend on specific parameter choices vs robust signals

## Production Engineering Features

### Data Integrity
- **Temporal Filtering**: Multi-layer as_of_date enforcement prevents all forms of look-ahead bias
- **API Integration**: financialdatasets.ai with comprehensive error handling and timeout controls
- **Fallback Mechanisms**: Realistic sample data generation maintains system availability during API outages
- **Validation Pipeline**: Pydantic models ensure type safety and constraint compliance throughout

### Risk Management  
- **Graceful Degradation**: System continues operating with reduced functionality rather than failing
- **Error Isolation**: Component failures don't cascade through the entire system
- **Audit Logging**: Complete decision trail for regulatory compliance and performance attribution
- **Missing Data Handling**: Conservative defaults (HOLD, neutral scores) when information unavailable

### Scalability Architecture
- **BaseAgent Template**: Abstract class enables rapid specialist addition without workflow modification
- **LangGraph Orchestration**: Node-based execution allows parallel processing and complex dependencies
- **Type Safety**: Pydantic models throughout ensure data integrity at all system boundaries
- **Modular Design**: Clean separation enables independent testing, deployment, and scaling

## Technical Implementation Details

### Agent Design Rationale

**Valuation Agent Implementation:**
- **20-day/60-day Window Choice**: Balances signal strength (20d) with stable volatility estimation (60d)
- **Risk Adjustment Logic**: return/volatility prevents high-beta stocks appearing strong through volatility alone  
- **Percentile Ranking**: Maintains consistent selectivity across different market volatility regimes
- **Sigmoid Normalization**: Factor=5 provides meaningful differentiation without saturation effects

**Sentiment Agent Implementation:**
- **VADER Selection**: Optimized for social media/news text vs academic sentiment tools
- **Recency Weighting**: 0.9^days decay reflects empirical news impact half-life in equity markets
- **Title+Snippet Strategy**: Balances information richness with processing efficiency
- **Absolute Thresholds**: Sentiment has meaningful interpretation independent of relative ranking

**Fundamental Agent Implementation:**
- **Four-Factor Framework**: Revenue growth, margins, leverage, capital efficiency capture business quality comprehensively
- **Equal Weighting**: Prevents single-metric optimization while requiring balanced excellence
- **Industry Scaling**: Technology company benchmarks (10-40% margins, <0.5 D/E) appropriate for universe
- **Absolute Quality Standards**: High-quality businesses deserve premium regardless of relative universe ranking

## Results & Performance

### Current System Performance (2025-07-01)
```
Agent Analysis Results:
AAPL: SELL (Val) | BUY (Sent) | BUY (Fund) → HOLD (conflicting signals, debate moderation)
MSFT: BUY (Val)  | HOLD (Sent)| BUY (Fund) → BUY (strong momentum + fundamentals consensus)  
NVDA: HOLD (Val) | HOLD (Sent)| BUY (Fund) → HOLD (quality company, mixed signals)
TSLA: SELL (Val) | HOLD (Sent)| HOLD (Fund)→ HOLD (weak momentum, average quality)

Portfolio Construction: 100% MSFT (only BUY rating)
Performance: 3.45% portfolio vs 10.33% benchmark = -6.88% active return
Sharpe Proxy: 0.85 (conservative approach reduces volatility)
```

### Decision Attribution Analysis
- **Conservative Bias**: System defaults to HOLD when signals conflict (institutional risk management)
- **Single Position Risk**: Equal-weight BUY rule created concentrated exposure
- **Quality Filter Effect**: Fundamental agent prevented momentum chasing into declining names
- **Debate Impact**: AAPL moderated from potential BUY to HOLD due to conflicting signals

## Testing & Validation

### Comprehensive Test Suite (8 tests, all passing)
- **Data Leakage Prevention**: Validates temporal filtering across price and news data
- **Agent Output Validation**: Ensures all agents produce valid ratings with proper reasoning
- **Mathematical Correctness**: Verifies coordinator weighted voting calculations  
- **Configuration Integrity**: Confirms weights sum to 1.0 and thresholds are sensible
- **End-to-End Integration**: Full workflow completion with expected outputs
- **Return Calculation**: Backtesting math validation with known test cases

---

# PART II: STRATEGIC VISION & EXPANSION ROADMAP

## System Extensibility Architecture

### BaseAgent Template Scalability
The abstract base class architecture enables rapid specialist addition without system modifications:

**Current Pattern:**
```python
class NewAgent(BaseAgent):
    def analyze(self, market_data, news_data, fundamental_data, as_of_date):
        # Specialized analysis logic
        return [AgentRating(...)]
```

**Expansion Benefits:**
- **Zero Integration Friction**: New agents automatically integrate with coordinator and workflow
- **Consistent Interface**: All agents receive same data inputs and produce compatible outputs
- **Parallel Development**: Multiple specialists can be developed simultaneously without conflicts
- **A/B Testing Ready**: Easy to swap agent implementations for performance comparison

### LangGraph Orchestration Advantages
The node-based execution framework provides enterprise-grade workflow management:

**Current Capabilities:**
- Sequential execution with state management
- Error isolation and recovery
- Complete audit trails
- Modular component testing

**Production Scaling:**
- **Parallel Processing**: Multiple agents can analyze simultaneously for latency reduction
- **Complex Dependencies**: Support for conditional workflows and decision trees  
- **Dynamic Reconfiguration**: Runtime agent enabling/disabling for different market regimes
- **Performance Monitoring**: Built-in execution timing and bottleneck identification

## LLM Integration Strategy

### Phase 2 Enhancement Opportunities

**Sentiment Agent LLM Augmentation:**
- **Implementation**: OpenAI API for nuanced financial text analysis beyond VADER
- **Benefits**: Better handling of sarcasm, complex financial terminology, multi-document synthesis
- **Use Case**: "Apple's iPhone sales beat expectations but guidance disappointing" → nuanced mixed sentiment
- **Integration**: LLM enhances VADER baseline while maintaining fallback capability

**Fundamental Agent Dynamic Enhancement:**
- **Implementation**: LLM-powered earnings call transcript analysis for real-time quality updates
- **Benefits**: Dynamic fundamental scores vs static manual curation
- **Use Case**: Quarterly earnings calls → extract management sentiment, guidance changes, competitive positioning
- **Integration**: LLM supplements manual factsheets with quarterly updates

**News Synthesis & Validation:**
- **Implementation**: Multi-document summarization for comprehensive ticker analysis
- **Benefits**: Process 100+ articles per ticker vs manual 5-15 curation
- **Use Case**: Synthesize week's news into coherent narrative: "Tesla production ramp + regulatory approval + competition analysis"
- **Integration**: LLM creates rich context while human validation ensures accuracy

**Signal Validation & Meta-Analysis:**
- **Implementation**: Cross-reference agent decisions with market commentary and analyst reports
- **Benefits**: Confidence scoring based on expert consensus alignment
- **Use Case**: "Our BUY rating aligns with 70% of sell-side analysts and recent institutional buying"
- **Integration**: LLM provides decision support without overriding systematic signals

### MVP vs LLM Trade-off Analysis

**Current MVP Advantages:**
- **Deterministic Logic**: Fully auditable and explainable for regulatory compliance
- **Cost Efficiency**: No API costs or latency concerns
- **Reliability**: No dependency on external AI services for core functionality
- **Baseline Performance**: Establishes measurable performance benchmark for LLM comparison

**LLM Integration Timeline:**
- **Phase 1**: Current rule-based system (completed)
- **Phase 2**: LLM enhancement of existing agents (6-month timeline)
- **Phase 3**: New LLM-native agents (earnings revision, macro sentiment)
- **Phase 4**: Full agentic trading with dynamic strategy adaptation

## RAG & Vector Database Enhancement Vision

### Financial Knowledge Retrieval Architecture

**Proposed Implementation:**
- **Vector Database**: Pinecone/Weaviate with financial document embeddings
- **Embedding Model**: FinBERT or domain-specific financial language models
- **Document Corpus**: 10-K filings, earnings transcripts, analyst reports, regulatory filings
- **Real-time Ingestion**: Automated processing of new filings and market commentary

**Business Intelligence Transformation:**
- **Current State**: Static fundamental factsheets with manual updates
- **Enhanced State**: Dynamic knowledge retrieval with comprehensive business context
- **Example Query**: "Tesla Q3 2024 production challenges and competitive response to BYD expansion"
- **RAG Response**: Synthesized analysis from earnings calls, 10-K risks, industry reports

**Specialized Financial RAG Features:**
- **Temporal Grounding**: Results filtered by as_of_date to prevent leakage
- **Source Attribution**: Complete audit trail showing which documents influenced decisions  
- **Sector Expertise**: Industry-specific knowledge graphs for contextual understanding
- **Quantitative Integration**: Extract numerical data alongside qualitative insights

**Implementation Benefits:**
- **Scalability**: Analyze thousands of companies vs manual 4-ticker curation
- **Depth**: Comprehensive business understanding vs simplified metrics
- **Timeliness**: Real-time knowledge updates vs quarterly manual reviews
- **Consistency**: Systematic analysis methodology across entire investment universe

### Advanced Agent Roadmap

**Earnings Revision Agent (LLM + RAG Powered):**
- **Data Sources**: Earnings transcripts, guidance updates, analyst revisions
- **Logic**: Track estimate changes and sentiment shifts quarter-over-quarter
- **Benefits**: Capture fundamental inflection points before price adjustments
- **Implementation**: 3-month development timeline with backtesting validation

**Macro Economic Agent:**
- **Data Sources**: Fed minutes, economic releases, central bank communications
- **Logic**: Assess macro regime impact on growth vs value vs momentum factors
- **Benefits**: Dynamic factor weighting based on economic conditions
- **Implementation**: Requires macro economic knowledge base development

**Technical Pattern Recognition Agent:**
- **Data Sources**: High-frequency price/volume data, options flow
- **Logic**: ML pattern recognition for support/resistance, breakouts, regime changes
- **Benefits**: Enhance valuation agent with sophisticated technical analysis
- **Implementation**: Computer vision techniques applied to financial charts

**Risk Management Agent:**
- **Data Sources**: Portfolio positions, market volatility, correlation matrices
- **Logic**: Position sizing, hedge recommendations, stress testing
- **Benefits**: Dynamic risk adjustment vs static equal-weight allocation
- **Implementation**: Requires portfolio optimization and risk modeling frameworks

## Enterprise Production Scaling

### Infrastructure Requirements
- **Kubernetes Deployment**: Container orchestration for agent scalability
- **Redis State Management**: Distributed caching for multi-instance coordination
- **PostgreSQL**: Time-series database for historical decision storage
- **Monitoring Stack**: Prometheus/Grafana for system performance tracking

### Regulatory & Compliance
- **Audit Trails**: Complete decision genealogy for regulatory examination
- **Model Risk Management**: A/B testing framework for agent performance validation
- **Documentation Standards**: Automated model card generation for each agent
- **Backtesting Governance**: Statistical significance testing and walk-forward validation

---

# PART III: TECHNICAL DETAILS

## Setup & Usage

### Environment Setup
```bash
# Clone and setup
git clone <repository-url>
cd antipodes
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional environment variables
export FINANCIAL_DATASETS_API_KEY=your_key_here  # For live price data
export OPENAI_API_KEY=your_key_here              # For LLM report/optimizer in the UI
export LANGCHAIN_API_KEY=your_key_here           # For workflow monitoring (optional)
```

Alternatively, create a `.env` at the repo root:
```
FINANCIAL_DATASETS_API_KEY=...
OPENAI_API_KEY=...
```

### System Execution
```bash
# Main system execution with custom date
python main.py --as-of-date 2025-04-01 --verbose

# Component testing
python main.py test-config                # Validate configuration
python main.py test-all-agents           # Test individual agents  
python main.py run-langgraph-workflow    # Full LangGraph execution

# Bonus feature validation
python main.py test-rolling-decisions    # Stability across multiple dates
python main.py test-robustness          # Weight sensitivity analysis

# Test suite execution
python -m pytest tests/ -v              # Run all tests
python tests/test_basic.py               # Individual test files
```

### Streamlit UI (Recommended)
```bash
streamlit run streamlit_app.py
```

Sidebar controls:
- Date, tickers, agent weights, forward window
- Toggle LLM performance report (needs `OPENAI_API_KEY`)
- Run and view tables, KPIs, chart, and download CSVs/PNG/MD
- Optimizer: request suggestions (JSON) and Apply to runtime config
- Rolling A/B: Baseline vs Variant across past months; export CSV; Promote Variant on uplift
- Config Versions: load previously promoted configs and apply (rollback)

### Output Files Generated
```bash
outputs/
├── picks.csv         # Agent ratings and final coordinator decisions
├── performance.csv   # Portfolio vs benchmark performance metrics
├── chart.png         # Visual performance comparison chart
├── attribution.csv   # Per-ticker returns and contributions
└── performance_report.md  # LLM-generated markdown attribution (if enabled)
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