from dotenv import load_dotenv
load_dotenv()

# Expose a LangGraph graph for LangGraph Platform deployments
from src.workflow import AgentWorkflow

# Compiled graph; expects input with key: as_of_date (YYYY-MM-DD)
graph = AgentWorkflow().workflow


