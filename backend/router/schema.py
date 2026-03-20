from pydantic import BaseModel
from typing import Optional

# --- Request Schemas ---

class ReportQuery(BaseModel):
    """The input model for a user's natural language query."""
    query: str


# --- Response Schemas ---

class SubmissionReceipt(BaseModel):
    """The output model for a successful submission."""
    status: str
    confirmation_id: str
    submitted_at: str
    company_name: str
    file_location: str

class ErrorResponse(BaseModel):
    """A generic error response model."""
    detail: str
