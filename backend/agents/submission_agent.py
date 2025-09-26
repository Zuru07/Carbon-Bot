import json
import logging
import uuid
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SubmissionAgent:
    """
    An agent that simulates the filing of an ESG report with a regulatory body.
    """
    def __init__(self, submission_dir: str = "submissions"):
        # Create a directory to store the simulated submissions
        self.project_root = Path(__file__).resolve().parents[2]
        self.submission_path = self.project_root / submission_dir
        self.submission_path.mkdir(exist_ok=True)
        logging.info(f"SubmissionAgent initialized. Reports will be saved to: {self.submission_path}")

    def submit_report(self, report_data: dict) -> dict:
        """
        Simulates submitting a report by saving it to a file and returning
        a confirmation receipt.

        Args:
            report_data (dict): The report content to be submitted.

        Returns:
            dict: A submission receipt with status and a confirmation ID.
        """
        company_name = report_data.get("company_name", "UNKNOWN_COMPANY")
        reporting_year = report_data.get("reporting_year", "YYYY")
        
        logging.info(f"Preparing to file report for {company_name} for year {reporting_year}.")
        
        try:
            # Generate a unique filename and confirmation ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            confirmation_id = str(uuid.uuid4())
            filename = f"submission_{company_name.replace(' ', '_')}_{reporting_year}_{timestamp}.json"
            filepath = self.submission_path / filename

            # Save the report data to the file
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=4)
            
            logging.info(f"Submission successful. Confirmation ID: {confirmation_id}")
            
            receipt = {
                "status": "SUCCESS",
                "confirmation_id": confirmation_id,
                "submitted_at": datetime.now().isoformat(),
                "company_name": company_name,
                "file_location": str(filepath)
            }
            return receipt

        except Exception as e:
            logging.error(f"Submission failed: {e}", exc_info=True)
            return {
                "status": "FAILED",
                "error": str(e)
            }