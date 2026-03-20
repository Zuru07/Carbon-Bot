import json
import logging

from langchain.tools import tool

from .sustainability_agent import SustainabilityAgent
from .genai_reporter import GenAI_Reporter
from .submission_agent import SubmissionAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sustainability_agent = SustainabilityAgent()
genai_reporter = GenAI_Reporter()
submission_agent = SubmissionAgent()


@tool
def get_company_data_snapshot(company_name: str) -> str:
    """
    Retrieves a detailed, structured data snapshot for a SINGLE company.
    
    Args:
        company_name (str): The exact, single name of the company.
                            DO NOT provide a list of names.
                            
    Returns:
        A JSON string of the company's data or an error message.
    """
    data = sustainability_agent.get_company_snapshot(company_name)
    if data:
        return json.dumps(data, indent=2, default=str)
    return f"Error: No data found for company '{company_name}'."


@tool
def get_emissions_summary(company_name: str) -> str:
    """
    Gets a formatted emissions summary for a company including totals,
    quarterly breakdowns, energy data, and metadata.
    
    Args:
        company_name (str): The exact name of the company.
        
    Returns:
        A formatted summary of the company's emissions data.
    """
    summary = sustainability_agent.get_emissions_summary(company_name)
    if summary:
        return json.dumps(summary, indent=2, default=str)
    return f"Error: No data found for company '{company_name}'."


@tool
def get_energy_consumption(company_name: str) -> str:
    """
    Calculates and returns estimated electricity consumption from Scope 2 emissions.
    
    Args:
        company_name (str): The exact name of the company.
        
    Returns:
        JSON string with electricity estimation details.
    """
    energy_data = sustainability_agent.get_energy_consumption(company_name)
    if energy_data:
        return json.dumps(energy_data, indent=2, default=str)
    return f"Error: Could not calculate energy consumption for '{company_name}'."


@tool
def check_deviation_alerts(company_name: str, threshold_pct: float = 10.0) -> str:
    """
    Checks for significant year-over-year changes in emissions data.
    
    Args:
        company_name (str): The exact name of the company.
        threshold_pct (float): Percentage change to trigger an alert (default: 10%).
        
    Returns:
        JSON string with any detected deviation alerts.
    """
    alerts = sustainability_agent.check_deviation_alerts(company_name, threshold_pct)
    if alerts:
        return json.dumps({
            "company_name": company_name,
            "alerts_count": len(alerts),
            "alerts": alerts
        }, indent=2, default=str)
    return f"No significant deviations found for '{company_name}'."


@tool
def get_historical_trends(company_name: str, years: int = 5) -> str:
    """
    Retrieves historical emissions data for trend analysis.
    
    Args:
        company_name (str): The exact name of the company.
        years (int): Number of years of history to retrieve (default: 5).
        
    Returns:
        JSON string with historical emissions data.
    """
    trends = sustainability_agent.get_historical_trends(company_name, years)
    if trends:
        return json.dumps({
            "company_name": company_name,
            "records_count": len(trends),
            "trends": trends
        }, indent=2, default=str)
    return f"No historical data found for '{company_name}'."


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


@tool
def generate_structured_report(company_name: str, report_type: str = "annual") -> str:
    """
    Generates a fully structured ESG report in JSON format suitable for
    regulatory submissions.
    
    Args:
        company_name (str): The exact name of the company.
        report_type (str): Type of report - 'annual', 'quarterly', or 'spot'.
        
    Returns:
        A structured ESG report in JSON format.
    """
    snapshot = sustainability_agent.get_company_snapshot(company_name)
    if not snapshot:
        return f"Error: No data found for company '{company_name}'."
    
    alerts = sustainability_agent.check_deviation_alerts(company_name)
    
    report = genai_reporter.generate_structured_esg_report(
        company_name=company_name,
        snapshot=snapshot,
        alerts=alerts,
        report_type=report_type
    )
    
    return report.model_dump_json(indent=2)


@tool
def submit_esg_report(company_name: str, report_type: str = "annual") -> str:
    """
    Generates and submits an ESG report for a company.
    This combines report generation and submission in one step.
    
    Args:
        company_name (str): The exact name of the company.
        report_type (str): Type of report - 'annual', 'quarterly', or 'spot'.
        
    Returns:
        A submission receipt with confirmation ID and file location.
    """
    snapshot = sustainability_agent.get_company_snapshot(company_name)
    if not snapshot:
        return f"Error: No data found for company '{company_name}'."
    
    alerts = sustainability_agent.check_deviation_alerts(company_name)
    
    report = genai_reporter.generate_structured_esg_report(
        company_name=company_name,
        snapshot=snapshot,
        alerts=alerts,
        report_type=report_type
    )
    
    receipt = submission_agent.submit_structured_report(report)
    
    return json.dumps(receipt, indent=2, default=str)


@tool
def get_submission_history(company_name: str | None = None, limit: int = 10) -> str:
    """
    Retrieves submission history from the audit trail.
    
    Args:
        company_name (str, optional): Filter by company name.
        limit (int): Maximum number of records to return (default: 10).
        
    Returns:
        JSON string with submission history.
    """
    history = submission_agent.get_submission_history(company_name, limit)
    if history:
        return json.dumps({
            "records_count": len(history),
            "submissions": history
        }, indent=2, default=str)
    return "No submission history found."
