from abc import ABC, abstractmethod
from datetime import date
from typing import List

from ..models import AgentRating, AgentType

class BaseAgent(ABC):
    """Base class for all trading agents"""
    
    def __init__(self, agent_type: AgentType, name: str):
        self.agent_type = agent_type
        self.name = name
    
    @abstractmethod
    def analyze(self, market_data, news_data, fundamental_data, as_of_date: date) -> List[AgentRating]:
        """
        Analyze data and return ratings for all tickers
        
        Args:
            market_data: Price data
            news_data: News articles
            fundamental_data: Fundamental metrics
            as_of_date: Decision date
            
        Returns:
            List of AgentRating objects
        """
        pass
    
    def __str__(self):
        return f"{self.name} ({self.agent_type.value})"