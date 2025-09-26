# from langchain.tools import tool
# from .sustainability_agent import SustainabilityAgent
# from .genai_reporter import GenAI_Reporter

# # Initialize the agents that the tools will use
# sustainability_agent = SustainabilityAgent()
# genai_reporter = GenAI_Reporter()

# @tool
# def get_company_data_snapshot(company_name: str) -> dict:
#     """
#     Retrieves a detailed data snapshot for a single, specified company.
#     Use this tool when the user asks for the specific data of one company.
#     """
#     return sustainability_agent.get_company_snapshot(company_name)

# @tool
# def generate_esg_report(query: str) -> str:
#     """
#     Generates a comparative ESG report or answers a natural language question
#     by analyzing data from multiple companies. Use this for any query that
#     involves comparison, analysis, or open-ended questions.
#     """
#     return genai_reporter.generate_report(query)

# backend/agents/agent_tools.py
from langchain.tools import tool
from .sustainability_agent import SustainabilityAgent
from .genai_reporter import GenAI_Reporter
import json # Import json for better output formatting

# Initialize the agents that the tools will use
sustainability_agent = SustainabilityAgent()
genai_reporter = GenAI_Reporter()

@tool
def get_company_data_snapshot(company_name: str) -> str:
    """
    Retrieves a detailed, structured data snapshot for a SINGLE company.
    
    Args:
        company_name (str): The exact, single name of the company. 
                            DO NOT provide a list of names.
                            
    Returns a JSON string of the company's data or an error message.
    """
    # The tool now returns a JSON string, which is easier for the LLM to parse.
    data = sustainability_agent.get_company_snapshot(company_name)
    if data:
        return json.dumps(data, indent=2, default=str)
    return f"Error: No data found for company '{company_name}'."

@tool
def generate_esg_report(query: str) -> str:
    """
    Answers a natural language query by comparing multiple companies or analyzing trends.
    Use this for any open-ended question that requires reasoning or retrieving
    information from several sources.
    
    Args:
        query (str): The user's full, original question.
    """
    return genai_reporter.generate_report(query)