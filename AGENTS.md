# Agent Coding Guidelines

## Project Overview

Carbon-bot is an ESG (Environmental, Social, Governance) reporting system with:
- **Backend**: FastAPI + LangChain agents for orchestration
- **Frontend**: Streamlit UI for interactive queries
- **Database**: PostgreSQL (relational data) + Pinecone (vector embeddings)
- **LLM**: Ollama with LLaMA 3 for natural language processing
- **Data Simulation**: NumPy-based realistic emissions modeling

## Build/Lint/Test Commands

### Python Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI backend
python -m uvicorn backend.router.main:app --reload --port 8000

# Run the Streamlit frontend
streamlit run frontend/app.py
```

### Testing (pytest)
```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest

# Run tests in a specific file
pytest tests/test_sustainability_agent.py

# Run a specific test function
pytest tests/test_sustainability_agent.py::test_sustainability_agent_snapshot -v

# Run tests matching a pattern
pytest -k "test_"

# Run with coverage
pytest --cov=backend --cov-report=html
```

### Linting & Type Checking
```bash
# Install development tools
pip install ruff black mypy

# Format code with Black
black backend/ frontend/

# Lint with Ruff
ruff check backend/

# Type check with MyPy
mypy backend/
```

### Database Migrations
```bash
# Run migrations manually (requires psql)
psql -U postgres -d carbon_bot -f backend/db/migrations/001_add_enriched_columns.sql
psql -U postgres -d carbon_bot -f backend/db/migrations/002_add_alerts_and_history.sql
psql -U postgres -d carbon_bot -f backend/db/migrations/003_add_submissions.sql
```

## Code Style Guidelines

### Python Version
- Target Python 3.10+

### Import Conventions
- Standard library imports first, then third-party, then local
- Use absolute imports within the package: `from backend.agents import ...`
- Group imports with blank lines between groups:
```python
import os
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from backend.agents.agent_tools import get_company_data_snapshot
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `CarbonDataAgent`, `SustainabilityAgent`)
- **Functions/Methods**: `snake_case` (e.g., `get_company_snapshot`, `store_postgres`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_BATCH_SIZE`)
- **Variables**: `snake_case` (e.g., `pinecone_index_name`)
- **Private methods**: Prefix with `_` (e.g., `_load_config`, `_safe_id`)

### Type Annotations
- Use type hints for function parameters and return types
- Use union syntax for multiple types: `dict | None`
```python
def get_company_snapshot(self, company_name: str) -> dict | None:
    ...
```

### Docstrings
- Use Google-style docstrings for all public classes and functions
```python
class CarbonDataAgent:
    """
    An agent responsible for the entire data ingestion and vectorization pipeline.
    It loads data from a CSV, enriches it with simulated quarterly breakdowns,
    supplier emissions, and electricity estimates, stores it in a relational 
    database (PostgreSQL), and creates semantic vector embeddings for Pinecone.
    """

    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enriches the emissions data with simulated data."""
```

### Error Handling
- Use specific exception types when possible
- Always log errors with context using `logging` module
- Include `exc_info=True` for exceptions to show stack traces
```python
try:
    with self.engine.connect() as connection:
        ...
except OperationalError as e:
    logging.error(f"PostgreSQL connection failed: {e}", exc_info=True)
    raise
except Exception as e:
    logging.error(f"An error occurred: {e}")
    return None
```

### Logging
- Use module-level logging configuration
```python
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```
- Log levels: DEBUG for development, INFO for general operations, WARNING/ERROR for problems

### Pydantic Schemas (FastAPI)
- Use Pydantic v2 `BaseModel` for request/response schemas
```python
from pydantic import BaseModel

class ReportQuery(BaseModel):
    """The input model for a user's natural language query."""
    query: str
```

### Database Queries
- Use SQLAlchemy's `text()` for raw SQL with parameterized queries
- NEVER interpolate user input directly into SQL strings
```python
from sqlalchemy import text

query = text(f"SELECT * FROM {self.table_name} WHERE company_name = :c_name")
df = pd.read_sql(query, connection, params={"c_name": company_name})
```

## Project Structure
```
carbon-bot/
├── config/
│   └── emission_factors.json    # Emission factors for calculations
├── backend/
│   ├── agents/                  # Agent implementations
│   │   ├── agent_tools.py       # LangChain tools
│   │   ├── carbon_data_agent.py # Data ingestion & enrichment
│   │   ├── genai_reporter.py    # Report generation with LLM
│   │   ├── submission_agent.py  # Report submission & audit
│   │   └── sustainability_agent.py # Analysis & alerts
│   ├── db/
│   │   └── migrations/          # Database migration scripts
│   │       ├── 001_add_enriched_columns.sql
│   │       ├── 002_add_alerts_and_history.sql
│   │       └── 003_add_submissions.sql
│   ├── router/                  # FastAPI routes and schemas
│   │   ├── main.py
│   │   └── schema.py
│   ├── utils/                   # Utility functions
│   │   ├── data_enrichment.py
│   │   ├── emission_calculator.py
│   │   ├── emission_factors.py
│   │   ├── report_schema.py     # ESG report schemas
│   │   └── schema_validator.py
│   └── orchestrator.py          # Main orchestration logic
├── frontend/
│   └── app.py                   # Streamlit UI
├── submissions/                  # Generated submission files
├── tests/
│   └── test_sustainability_agent.py
├── requirements.txt
└── .env                        # Environment variables (gitignored)
```

## Environment Variables
- Required in `.env`:
  - `POSTGRES_URI`: PostgreSQL connection string
  - `PINECONE_API_KEY`: Pinecone API key
- Optional:
  - `CSV_PATH`: Path to emissions data CSV (default: `cleaned_emissions.csv`)
  - `PINECONE_INDEX_NAME`: Vector index name
  - `POSTGRES_TABLE_NAME`: Database table name
  - `PINECONE_BATCH_SIZE`: Batch size for vector upserts
  - `ENRICHMENT_METHOD`: `distribution` (normal/Dirichlet) or `equal_split` (default: `distribution`)
  - `GRID_EMISSION_FACTOR`: Override default grid emission factor (kg CO2/kWh)
  - `REGION_CODE`: Default region for emission factor lookup

## Data Simulation

### Quarterly Emissions Breakdown
- Uses normal distribution with controlled variation (std: 0.10)
- Each quarter gets 15-35% of annual total
- Sum of quarters equals annual total

### Electricity Consumption Estimation
- Back-calculated from Scope 2 emissions using grid emission factors
- Formula: `electricity_kWh = Scope2_tCO2e * 1000 / grid_factor`
- Configurable via `config/emission_factors.json`

### Supplier Emissions Breakdown
- Uses Dirichlet distribution for proportional contributions
- 5 simulated suppliers by default
- Sum of supplier emissions equals Scope 3 total

### Metadata Generation
- Employee count estimated from company emissions size
- Energy mix percentages based on sector classification

## API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /report/generate` - Generate natural language report
- `POST /report/generate/structured` - Generate JSON report
- `POST /report/submit` - Generate and submit report

### Company Data Endpoints
- `GET /company/{name}` - Get company snapshot
- `GET /company/{name}/summary` - Get emissions summary
- `GET /company/{name}/energy` - Get electricity estimation
- `GET /company/{name}/alerts` - Get deviation alerts
- `GET /company/{name}/trends` - Get historical trends

### Submission Endpoints
- `GET /submissions` - Get submission history
- `GET /submissions/{confirmation_id}` - Get specific submission

## Testing Guidelines
- Place tests in `tests/` directory at project root
- Test file naming: `test_<module_name>.py`
- Test function naming: `test_<function_name>_<scenario>`
```python
def test_emission_calculator_quarterly():
    """Test quarterly breakdown generation."""
    ...
```
- Mock external services (Ollama, Pinecone, PostgreSQL) in unit tests

## Git Workflow
- Commit messages: Use conventional commits (e.g., `feat:`, `fix:`, `refactor:`)
- Never commit `.env` files or API keys
- Use `git diff --cached` before committing to review staged changes
