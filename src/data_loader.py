import requests
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Optional
import os
import json
from pathlib import Path

from .config import config
from .models import StockPrice, MarketData, NewsItem, NewsData, FundamentalData

class FinancialDataLoader:
    """Handles loading stock price data with fallback mechanism"""
    
    def __init__(self):
        self.api_key = config.api.financial_datasets_api_key
        self.base_url = config.api.financial_datasets_base_url
        self.fallback_path = config.get_data_fallback_path()
        
    def fetch_stock_prices(
        self, 
        tickers: List[str], 
        start_date: date, 
        end_date: date,
        as_of_date: date
    ) -> MarketData:
        """
        Fetch stock prices with strict date filtering to prevent leakage
        
        Args:
            tickers: List of stock symbols
            start_date: Start of data window
            end_date: End of data window  
            as_of_date: Decision date - no data after this date allowed
        """
        # Critical: Ensure we never use data after as_of_date
        if end_date > as_of_date:
            print(f"⚠️  Adjusting end_date from {end_date} to {as_of_date} to prevent leakage")
            end_date = as_of_date
            
        if start_date > as_of_date:
            raise ValueError(f"Start date {start_date} is after as_of_date {as_of_date}")
        
        prices = []
        
        # Try API first
        if self.api_key:
            try:
                prices = self._fetch_from_api(tickers, start_date, end_date)
                print(f"✅ Successfully fetched data from API for {len(tickers)} tickers")
            except Exception as e:
                print(f"❌ API fetch failed: {e}")
                print("📁 Falling back to cached data...")
                prices = self._fetch_from_fallback(tickers, start_date, end_date)
        else:
            print("🔑 No API key found, using fallback data")
            prices = self._fetch_from_fallback(tickers, start_date, end_date)
            
        # Final leakage check
        prices = [p for p in prices if p.date <= as_of_date]
        
        return MarketData(prices=prices, as_of_date=as_of_date)
    
    def _fetch_from_api(self, tickers: List[str], start_date: date, end_date: date) -> List[StockPrice]:
        """Fetch from financialdatasets.ai API using correct format"""
        prices = []
        
        for ticker in tickers:
            # Correct URL format from the API documentation
            url = (
                f"https://api.financialdatasets.ai/prices/"
                f"?ticker={ticker}"
                f"&interval=day"
                f"&interval_multiplier=1"
                f"&start_date={start_date.isoformat()}"
                f"&end_date={end_date.isoformat()}"
            )
            
            # Correct headers format
            headers = {
                "X-API-KEY": self.api_key
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse the 'prices' array from response
                    prices_data = data.get('prices', [])
                    
                    for price_data in prices_data:
                        try:
                            # API returns 'time' field instead of 'date'
                            date_str = price_data.get('time', price_data.get('date', ''))
                            if not date_str:
                                print(f"  ❌ No date/time field in price data: {price_data}")
                                continue
                                
                            price = StockPrice(
                                ticker=ticker,
                                date=datetime.fromisoformat(date_str.replace('Z', '+00:00')).date(),
                                open_price=float(price_data['open']),
                                high_price=float(price_data['high']),
                                low_price=float(price_data['low']),
                                close_price=float(price_data['close']),
                                volume=int(price_data['volume'])
                            )
                            prices.append(price)
                        except (KeyError, ValueError) as e:
                            print(f"  ❌ Error parsing price data: {e} - {price_data}")
                            continue
                        
                    print(f"  ✅ Fetched {len(prices_data)} records for {ticker}")
                    
                else:
                    print(f"  ❌ API error for {ticker}: {response.status_code}")
                    raise requests.RequestException(f"API returned {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"  ❌ Failed to fetch {ticker}: {e}")
                raise e
                
        return prices
    
    def _fetch_from_fallback(self, tickers: List[str], start_date: date, end_date: date) -> List[StockPrice]:
        """Load from fallback CSV file"""
        if not os.path.exists(self.fallback_path):
            # Create sample fallback data
            self._create_sample_fallback_data(tickers, start_date, end_date)
        
        df = pd.read_csv(self.fallback_path)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Filter data
        mask = (
            (df['ticker'].isin(tickers)) & 
            (df['date'] >= start_date) & 
            (df['date'] <= end_date)
        )
        df = df[mask]
        
        prices = []
        for _, row in df.iterrows():
            price = StockPrice(
                ticker=row['ticker'],
                date=row['date'],
                open_price=row['open'],
                high_price=row['high'],
                low_price=row['low'],
                close_price=row['close'],
                volume=row['volume']
            )
            prices.append(price)
            
        return prices
    
    def _create_sample_fallback_data(self, tickers: List[str], start_date: date, end_date: date):
        """Create realistic sample data for fallback"""
        print("📊 Creating enhanced fallback data...")
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        extended_end = end_date + timedelta(days=120) 
        
        # Base prices for each ticker (approximate recent values)
        base_prices = {
            'AAPL': 180.0,
            'MSFT': 350.0, 
            'NVDA': 800.0,
            'TSLA': 250.0
        }
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                for ticker in tickers:
                    # Simple random walk with slight upward bias
                    if data:
                        last_close = [d for d in data if d['ticker'] == ticker]
                        if last_close:
                            base_price = last_close[-1]['close']
                        else:
                            base_price = base_prices.get(ticker, 100.0)
                    else:
                        base_price = base_prices.get(ticker, 100.0)
                    
                    # Random daily change ±3%
                    import random
                    change = random.uniform(-0.03, 0.03)
                    close = base_price * (1 + change)
                    
                    # Realistic OHLV
                    daily_range = close * random.uniform(0.01, 0.04)
                    open_price = close * random.uniform(0.99, 1.01)
                    high = max(open_price, close) + random.uniform(0, daily_range)
                    low = min(open_price, close) - random.uniform(0, daily_range)
                    volume = random.randint(10000000, 100000000)
                    
                    data.append({
                        'ticker': ticker,
                        'date': current_date.isoformat(),
                        'open': round(open_price, 2),
                        'high': round(high, 2),
                        'low': round(low, 2),
                        'close': round(close, 2),
                        'volume': volume
                    })
            
            current_date += timedelta(days=1)
        
        df = pd.DataFrame(data)
        df.to_csv(self.fallback_path, index=False)
        print(f"✅ Created fallback data with {len(df)} records")

class NewsLoader:
    """Handles loading news data from JSON files"""
    
    def load_news_data(self, as_of_date: date) -> NewsData:
        """Load news from data/news/ directory"""
        news_dir = Path("data/news")
        articles = []
        
        if not news_dir.exists():
            print("📰 No news directory found, creating sample data...")
            self._create_sample_news()
        
        # Load from JSON files
        for json_file in news_dir.glob("*.json"):
            ticker = json_file.stem.upper()
            
            try:
                with open(json_file) as f:
                    content = f.read().strip()
                    if not content:
                        print(f"  ⚠️  Empty news file: {json_file}")
                        continue
                    data = json.loads(content)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"  ⚠️  Invalid JSON in {json_file}: {e}")
                continue
                
            for item in data:
                article_date = datetime.fromisoformat(item['date']).date()
                
                # Prevent leakage - only use news before as_of_date
                if article_date <= as_of_date:
                    article = NewsItem(
                        ticker=ticker,
                        title=item['title'],
                        snippet=item['snippet'],
                        date=article_date,
                        source=item.get('source', 'unknown'),
                        url=item.get('url')
                    )
                    articles.append(article)
        
        return NewsData(articles=articles, as_of_date=as_of_date)
    
    def _create_sample_news(self):
        """Create sample news data"""
        Path("data/news").mkdir(parents=True, exist_ok=True)
        
        sample_news = {
            "AAPL": [
                {
                    "title": "Apple Reports Strong iPhone Sales Beat Expectations",
                    "snippet": "Apple Inc. reported better-than-expected iPhone sales for Q2 2025, with revenue up 12% year-over-year, boosting investor confidence in the tech giant.",
                    "date": "2025-06-05",
                    "source": "Reuters"
                },
                {
                    "title": "Apple Intelligence AI Features Drive Services Growth",
                    "snippet": "Apple's AI suite 'Apple Intelligence' has driven 18% growth in services revenue, with premium AI subscriptions exceeding projections.",
                    "date": "2025-06-12", 
                    "source": "Bloomberg"
                },
                {
                    "title": "Supply Chain Optimization Boosts Apple Margins",
                    "snippet": "Apple's new supply chain partnerships in Southeast Asia have improved gross margins by 200 basis points, analysts report.",
                    "date": "2025-06-18",
                    "source": "Financial Times"
                },
                {
                    "title": "Apple Vision Pro Sales Disappoint in Q2",
                    "snippet": "Apple Vision Pro sales of 180,000 units fell short of the 400,000 unit expectation, raising questions about VR market readiness.",
                    "date": "2025-06-28",
                    "source": "CNBC"
                }
            ],
            "MSFT": [
                {
                    "title": "Microsoft Azure AI Revenue Surges 45% Year-Over-Year",
                    "snippet": "Microsoft reported exceptional growth in Azure AI services, with $8.2 billion in quarterly revenue from AI workloads and Copilot enterprise.",
                    "date": "2025-06-08",
                    "source": "Reuters"
                },
                {
                    "title": "Microsoft 365 Copilot Reaches 10 Million Subscribers",
                    "snippet": "Enterprise adoption of Microsoft's AI-powered Copilot has reached 10 million paid subscribers, generating $2 billion in annual recurring revenue.",
                    "date": "2025-06-15",
                    "source": "Wall Street Journal"
                },
                {
                    "title": "Gaming Division Faces Headwinds as Cloud Gaming Grows",
                    "snippet": "While traditional Xbox sales declined 8%, Microsoft's cloud gaming service Game Pass Ultimate grew 25% with 35 million subscribers.",
                    "date": "2025-06-22",
                    "source": "GamesBeat"
                },
                {
                    "title": "Microsoft Announces $20B Green Data Center Initiative",
                    "snippet": "Microsoft commits to building carbon-negative data centers powered by renewable energy, investing $20 billion over five years.",
                    "date": "2025-06-26",
                    "source": "TechCrunch"
                }
            ],
            "NVDA": [
                {
                    "title": "NVIDIA Data Center Revenue Hits $35B in Q2 2025",
                    "snippet": "NVIDIA's data center revenue reached $35.1 billion, up 89% year-over-year, driven by insatiable demand for AI training infrastructure.",
                    "date": "2025-06-06",
                    "source": "Reuters"
                },
                {
                    "title": "NVIDIA Blackwell Architecture Sees Record Pre-Orders",
                    "snippet": "NVIDIA's next-generation Blackwell AI chips have garnered over $80 billion in committed orders from hyperscale customers.",
                    "date": "2025-06-13",
                    "source": "Bloomberg"
                },
                {
                    "title": "Competition Heats Up as AMD Launches MI400 AI Chips",
                    "snippet": "AMD's new MI400 AI accelerators pose increasing competition to NVIDIA, though analysts expect minimal near-term market share impact.",
                    "date": "2025-06-20",
                    "source": "AnandTech"
                },
                {
                    "title": "NVIDIA Automotive AI Revenue Doubles to $1.5B",
                    "snippet": "NVIDIA's automotive division hit $1.5 billion in quarterly revenue as autonomous vehicle deployments accelerate globally.",
                    "date": "2025-06-25",
                    "source": "Automotive News"
                }
            ],
            "TSLA": [
                {
                    "title": "Tesla Q2 2025 Deliveries Beat Expectations at 520K Units",
                    "snippet": "Tesla delivered 520,000 vehicles in Q2 2025, beating analyst estimates of 485,000, driven by strong Model 3 refresh demand.",
                    "date": "2025-06-07",
                    "source": "Reuters"
                },
                {
                    "title": "Tesla FSD Version 13 Achieves Major Safety Milestone",
                    "snippet": "Tesla's Full Self-Driving v13 achieved 4.2 million miles between disengagements, marking significant progress toward Level 4 autonomy.",
                    "date": "2025-06-14",
                    "source": "Electrek"
                },
                {
                    "title": "Tesla Energy Storage Deployments Surge 180% YoY",
                    "snippet": "Tesla deployed 9.4 GWh of energy storage in Q2, with Megapack installations driving 35% gross margins in the energy business.",
                    "date": "2025-06-21",
                    "source": "CleanTechnica"
                },
                {
                    "title": "Tesla Cybertruck Production Reaches 50K Monthly Run Rate",
                    "snippet": "Tesla's Austin Gigafactory achieved Cybertruck production of 50,000 units per month, with backlog extending into 2027.",
                    "date": "2025-06-27",
                    "source": "InsideEVs"
                }
            ]
        }
        
        for ticker, news_items in sample_news.items():
            with open(f"data/news/{ticker}.json", "w") as f:
                json.dump(news_items, f, indent=2)
        
        print(f"✅ Created sample news for {len(sample_news)} tickers with 2025 dates")

class FundamentalLoader:
    """Handles fundamental data loading"""
    
    def load_fundamental_data(self) -> List[FundamentalData]:
        """Load hand-curated fundamental data"""
        # 
        
        return [
    FundamentalData(
        ticker="AAPL",
        revenue_growth=0.08,        # 8% revenue growth
        operating_margin=0.30,      # 30% operating margin
        debt_to_equity=0.20,        # Low leverage
        capex_intensity=0.04,       # 4% of revenue
        quality_score=0.85          # High quality
    ),
    FundamentalData(
        ticker="MSFT", 
        revenue_growth=0.12,        # 12% revenue growth
        operating_margin=0.35,      # 35% operating margin
        debt_to_equity=0.15,        # Very low leverage
        capex_intensity=0.06,       # 6% of revenue
        quality_score=0.90          # Highest quality
    ),
    FundamentalData(
        ticker="NVDA",
        revenue_growth=0.45,        # 45% revenue growth (AI boom)
        operating_margin=0.28,      # 28% operating margin
        debt_to_equity=0.10,        # Minimal leverage
        capex_intensity=0.08,       # 8% of revenue (R&D heavy)
        quality_score=0.82          # High quality, but growth-dependent
    ),
    FundamentalData(
        ticker="TSLA",
        revenue_growth=0.22,        # 22% revenue growth
        operating_margin=0.18,      # 18% operating margin (improving)
        debt_to_equity=0.25,        # Moderate leverage
        capex_intensity=0.12,       # 12% of revenue (factory expansion)
        quality_score=0.75          # Good quality, but more volatile
    )
]