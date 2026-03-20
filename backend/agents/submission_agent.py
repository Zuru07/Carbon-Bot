import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SubmissionAgent:
    """
    An agent that handles the filing of ESG reports with regulatory bodies.
    
    Supports structured JSON reports, submission versioning, and audit trail
    through database storage.
    """
    
    def __init__(self, submission_dir: str = "submissions"):
        self.project_root = Path(__file__).resolve().parents[2]
        load_dotenv(dotenv_path=self.project_root / ".env")
        
        self.submission_path = self.project_root / submission_dir
        self.submission_path.mkdir(exist_ok=True)
        
        self.db_uri = os.getenv("POSTGRES_URI")
        if self.db_uri:
            self.engine = create_engine(
                self.db_uri,
                pool_recycle=1800,
                connect_args={'connect_timeout': 10}
            )
        else:
            self.engine = None
            logging.warning("POSTGRES_URI not set - submission history will not be stored in database")
        
        logging.info(f"SubmissionAgent initialized. Reports will be saved to: {self.submission_path}")

    def submit_report(
        self,
        report_data: dict,
        validate: bool = True
    ) -> dict:
        """
        Submits a report by saving it to a file and recording the submission.
        
        Args:
            report_data: The report content to be submitted
            validate: Whether to validate against ESG report schema
            
        Returns:
            Submission receipt with status and confirmation ID
        """
        company_name = report_data.get("company_name", "UNKNOWN_COMPANY")
        reporting_year = report_data.get("reporting_period", {}).get("year") or \
                        report_data.get("reporting_year", "YYYY")
        
        logging.info(f"Preparing to file report for {company_name} for year {reporting_year}")
        
        if validate:
            is_valid, errors = self._validate_report(report_data)
            if not is_valid:
                logging.warning(f"Report validation warnings: {errors}")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            confirmation_id = str(uuid.uuid4())
            version = self._get_next_version(company_name, reporting_year)
            
            filename = f"submission_{self._safe_filename(company_name)}_{reporting_year}_v{version}_{timestamp}.json"
            filepath = self.submission_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=4, default=str)
            
            receipt = {
                "status": "SUCCESS",
                "confirmation_id": confirmation_id,
                "submitted_at": datetime.now().isoformat(),
                "company_name": company_name,
                "reporting_year": reporting_year,
                "report_version": version,
                "file_location": str(filepath)
            }
            
            self._store_submission_history(receipt)
            
            logging.info(f"Submission successful. Confirmation ID: {confirmation_id}")
            return receipt

        except Exception as e:
            logging.error(f"Submission failed: {e}", exc_info=True)
            return {
                "status": "FAILED",
                "error": str(e)
            }

    def submit_structured_report(
        self,
        report_schema,  # ESGReportSchema instance
        validate: bool = True
    ) -> dict:
        """
        Submits a structured ESG report.
        
        Args:
            report_schema: ESGReportSchema instance
            validate: Whether to validate the report
            
        Returns:
            Submission receipt
        """
        report_data = report_schema.model_dump()
        return self.submit_report(report_data, validate=validate)

    def _validate_report(self, report_data: dict) -> tuple[bool, list[str]]:
        """Validates report data against expected schema."""
        errors = []
        
        required_fields = ['company_name', 'emissions_summary']
        for field in required_fields:
            if field not in report_data:
                errors.append(f"Missing required field: {field}")
        
        if 'emissions_summary' in report_data:
            summary = report_data['emissions_summary']
            for scope in ['scope1_tCO2e', 'scope2_tCO2e', 'scope3_tCO2e']:
                if scope in summary and summary[scope] < 0:
                    errors.append(f"{scope} cannot be negative")
        
        return len(errors) == 0, errors

    def _safe_filename(self, name: str) -> str:
        """Creates a safe filename from a company name."""
        safe = str(name).replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe = ''.join(c for c in safe if c.isalnum() or c in '_-')
        return safe[:50]

    def _get_next_version(
        self,
        company_name: str,
        reporting_year: int | str
    ) -> int:
        """Gets the next version number for a company's submission."""
        if not self.engine:
            return 1
        
        try:
            with self.engine.connect() as connection:
                query = text("""
                    SELECT MAX(report_version) as max_version
                    FROM submission_history
                    WHERE company_name = :company_name AND reporting_year = :year
                """)
                result = connection.execute(query, {
                    "company_name": company_name,
                    "year": int(reporting_year) if str(reporting_year).isdigit() else 0
                })
                row = result.fetchone()
                if row and row[0]:
                    return int(row[0]) + 1
                return 1
        except SQLAlchemyError as e:
            logging.warning(f"Could not get version number: {e}")
            return 1

    def _store_submission_history(self, receipt: dict) -> bool:
        """Stores submission record in database for audit trail."""
        if not self.engine:
            return False
        
        try:
            with self.engine.connect() as connection:
                query = text("""
                    INSERT INTO submission_history (
                        confirmation_id, company_name, reporting_year,
                        report_version, file_location, submitted_at,
                        submission_status, validated_successfully
                    ) VALUES (
                        :confirmation_id, :company_name, :reporting_year,
                        :report_version, :file_location, :submitted_at,
                        :status, :validated
                    )
                """)
                connection.execute(query, {
                    "confirmation_id": receipt["confirmation_id"],
                    "company_name": receipt["company_name"],
                    "reporting_year": receipt.get("reporting_year"),
                    "report_version": receipt.get("report_version", 1),
                    "file_location": receipt["file_location"],
                    "submitted_at": receipt["submitted_at"],
                    "status": receipt["status"],
                    "validated": receipt.get("validation_passed", True)
                })
                connection.commit()
            logging.info(f"Submission history recorded in database")
            return True
        except SQLAlchemyError as e:
            logging.warning(f"Could not store submission history (table may not exist): {e}")
            return False

    def get_submission_history(
        self,
        company_name: str | None = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Retrieves submission history from database.
        
        Args:
            company_name: Filter by company name
            limit: Maximum number of records to return
            
        Returns:
            List of submission records
        """
        if not self.engine:
            logging.warning("Database not configured - cannot retrieve history")
            return []
        
        try:
            with self.engine.connect() as connection:
                conditions = []
                params = {"limit": limit}
                
                if company_name:
                    conditions.append("company_name = :company_name")
                    params["company_name"] = company_name
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                query = text(f"""
                    SELECT * FROM submission_history
                    WHERE {where_clause}
                    ORDER BY submitted_at DESC
                    LIMIT :limit
                """)
                df = __import__('pandas').read_sql(query, connection, params=params)
            
            return df.to_dict('records') if not df.empty else []
        except SQLAlchemyError as e:
            logging.warning(f"Could not retrieve submission history: {e}")
            return []

    def get_submission_by_id(self, confirmation_id: str) -> dict | None:
        """Retrieves a specific submission by confirmation ID."""
        if not self.engine:
            return None
        
        try:
            with self.engine.connect() as connection:
                query = text("""
                    SELECT * FROM submission_history
                    WHERE confirmation_id = :confirmation_id
                """)
                df = __import__('pandas').read_sql(query, connection, params={"confirmation_id": confirmation_id})
            
            if df.empty:
                return None
            return df.iloc[0].to_dict()
        except SQLAlchemyError as e:
            logging.warning(f"Could not retrieve submission: {e}")
            return None

    def get_latest_submission(self, company_name: str, reporting_year: int) -> dict | None:
        """Gets the most recent submission for a company and year."""
        if not self.engine:
            return None
        
        try:
            with self.engine.connect() as connection:
                query = text("""
                    SELECT * FROM submission_history
                    WHERE company_name = :company_name AND reporting_year = :year
                    ORDER BY submitted_at DESC
                    LIMIT 1
                """)
                df = __import__('pandas').read_sql(query, connection, params={
                    "company_name": company_name,
                    "year": reporting_year
                })
            
            if df.empty:
                return None
            return df.iloc[0].to_dict()
        except SQLAlchemyError as e:
            logging.warning(f"Could not retrieve latest submission: {e}")
            return None


if __name__ == '__main__':
    print("=== Testing Submission Agent ===\n")
    
    agent = SubmissionAgent()
    
    sample_report = {
        "report_id": "ESG-2024-TEST-001",
        "report_type": "annual",
        "company_name": "Test Corporation",
        "reporting_period": {"year": 2024},
        "emissions_summary": {
            "scope1_tCO2e": 100000,
            "scope2_tCO2e": 50000,
            "scope3_tCO2e": 500000,
            "total_tCO2e": 650000
        },
        "compliance_status": {
            "reporting_framework": "GHG Protocol",
            "reporting_standard": "ISO 14064-1"
        },
        "data_sources": ["Company records"],
        "generated_at": datetime.now().isoformat()
    }
    
    receipt = agent.submit_report(sample_report)
    print(f"Submission Receipt:")
    print(json.dumps(receipt, indent=2))
