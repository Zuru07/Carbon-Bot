import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from backend.orchestrator import MasterAgent
from backend.agents.submission_agent import SubmissionAgent
from backend.agents.sustainability_agent import SustainabilityAgent
from backend.agents.genai_reporter import GenAI_Reporter
from backend.router.schema import ReportQuery, SubmissionReceipt

load_dotenv(dotenv_path=project_root / ".env")

app = FastAPI(
    title="ESG Reporting AI API",
    description="An API for interacting with a multi-agent ESG reporting system.",
    version="2.0.0"
)

try:
    master_agent = MasterAgent()
    submission_agent = SubmissionAgent()
    sustainability_agent = SustainabilityAgent()
    genai_reporter = GenAI_Reporter()
except Exception as e:
    raise RuntimeError(f"Fatal Error: Could not initialize agents. Reason: {e}") from e


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "ESG Reporting AI API is running",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "agents": {
            "master_agent": "initialized",
            "submission_agent": "initialized",
            "sustainability_agent": "initialized",
            "genai_reporter": "initialized"
        }
    }


@app.post("/report/generate", response_model=dict)
def generate_report(request: ReportQuery):
    """
    Uses the MasterAgent orchestrator to generate a response to a natural language query.
    """
    try:
        result = master_agent.run(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")


@app.post("/report/generate/structured")
def generate_structured_report(request: ReportQuery):
    """
    Generates a structured JSON report for regulatory submissions.
    """
    try:
        company_name = request.query.strip()
        
        snapshot = sustainability_agent.get_company_snapshot(company_name)
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
        
        alerts = sustainability_agent.check_deviation_alerts(company_name)
        
        report = genai_reporter.generate_structured_esg_report(
            company_name=company_name,
            snapshot=snapshot,
            alerts=alerts,
            report_type="annual"
        )
        
        return report.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")


@app.post("/report/submit", response_model=dict)
def submit_report(request: ReportQuery):
    """
    Generates and submits a report for a company.
    """
    try:
        company_name = request.query.strip()
        
        snapshot = sustainability_agent.get_company_snapshot(company_name)
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
        
        alerts = sustainability_agent.check_deviation_alerts(company_name)
        
        report = genai_reporter.generate_structured_esg_report(
            company_name=company_name,
            snapshot=snapshot,
            alerts=alerts,
            report_type="annual"
        )
        
        receipt = submission_agent.submit_structured_report(report)
        
        if receipt.get("status") == "FAILED":
            raise HTTPException(status_code=500, detail=f"Submission failed: {receipt.get('error')}")

        return receipt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Submission process failed: {e}")


@app.get("/company/{company_name}")
def get_company_data(company_name: str):
    """Gets detailed data for a specific company."""
    try:
        snapshot = sustainability_agent.get_company_snapshot(company_name)
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
        return snapshot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve company data: {e}")


@app.get("/company/{company_name}/summary")
def get_company_summary(company_name: str):
    """Gets formatted emissions summary for a company."""
    try:
        summary = sustainability_agent.get_emissions_summary(company_name)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {e}")


@app.get("/company/{company_name}/energy")
def get_company_energy(company_name: str):
    """Gets electricity consumption estimation for a company."""
    try:
        energy = sustainability_agent.get_energy_consumption(company_name)
        if not energy:
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
        return energy
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate energy consumption: {e}")


@app.get("/company/{company_name}/alerts")
def get_company_alerts(company_name: str, threshold: float = 10.0):
    """Gets deviation alerts for a company."""
    try:
        alerts = sustainability_agent.check_deviation_alerts(company_name, threshold)
        return {
            "company_name": company_name,
            "threshold_pct": threshold,
            "alerts_count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check alerts: {e}")


@app.get("/company/{company_name}/trends")
def get_company_trends(company_name: str, years: int = 5):
    """Gets historical emissions trends for a company."""
    try:
        trends = sustainability_agent.get_historical_trends(company_name, years)
        return {
            "company_name": company_name,
            "years_requested": years,
            "records_count": len(trends),
            "trends": trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {e}")


@app.get("/submissions")
def get_submission_history(company_name: str | None = None, limit: int = 10):
    """Gets submission history from the audit trail."""
    try:
        history = submission_agent.get_submission_history(company_name, limit)
        return {
            "records_count": len(history),
            "submissions": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {e}")


@app.get("/submissions/{confirmation_id}")
def get_submission(confirmation_id: str):
    """Gets a specific submission by confirmation ID."""
    try:
        submission = submission_agent.get_submission_by_id(confirmation_id)
        if not submission:
            raise HTTPException(status_code=404, detail=f"Submission '{confirmation_id}' not found")
        return submission
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve submission: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
