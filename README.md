# Carbon-bot: Multi-Agent ESG Reporting System

An intelligent ESG (Environmental, Social, Governance) reporting system powered by LangChain agents and local LLaMA 3. Carbon-bot provides natural language queries, emissions analysis, deviation detection, and regulatory report generation for corporate sustainability data.

## Architecture

```
carbon-bot/
├── backend/
│   ├── agents/           # LangChain-powered AI agents
│   │   ├── carbon_data_agent.py    # Data ingestion & vectorization
│   │   ├── sustainability_agent.py # Analysis & alerts
│   │   ├── genai_reporter.py       # LLM-powered report generation
│   │   ├── submission_agent.py      # Report submission & audit
│   │   └── agent_tools.py          # LangChain tool definitions
│   ├── router/            # FastAPI endpoints
│   │   ├── main.py                # API routes
│   │   └── schema.py              # Request/response schemas
│   ├── utils/             # Utility functions
│   │   ├── data_enrichment.py     # Data simulation pipeline
│   │   ├── emission_calculator.py # Emissions calculations
│   │   ├── emission_factors.py    # Grid emission factors
│   │   └── report_schema.py       # ESG report schemas
│   └── orchestrator.py     # MasterAgent orchestration
├── frontend/
│   └── app.py             # Streamlit UI
├── config/
│   └── emission_factors.json
└── tests/
```

## Features

- **Natural Language Queries**: Ask questions like "Compare Scope 1 emissions between Amazon and Microsoft"
- **Data Ingestion**: Load CSV data, enrich with simulations, store in PostgreSQL + Pinecone
- **Emissions Analysis**: Scope 1, 2, 3 breakdowns with quarterly data
- **Deviation Alerts**: Automatic detection of year-over-year emission changes
- **Historical Trends**: Track emissions over multiple years
- **Structured Reports**: Generate JSON reports for regulatory submissions
- **Submission Management**: Versioned reports with audit trail

## Tech Stack

- **Backend**: FastAPI + LangChain
- **Frontend**: Streamlit
- **Database**: PostgreSQL (relational) + Pinecone (vector store)
- **LLM**: Ollama with LLaMA 3
- **Data Processing**: Pandas, NumPy
- **Embeddings**: Sentence Transformers (all-mpnet-base-v2)

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Pinecone account
- Ollama running with llama3 model

### Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```env
POSTGRES_URI=postgresql://user:password@localhost:5432/carbon_bot
PINECONE_API_KEY=your-pinecone-api-key
CSV_PATH=cleaned_emissions.csv
PINECONE_INDEX_NAME=company-emissions-index
POSTGRES_TABLE_NAME=company_emissions
PINECONE_BATCH_SIZE=32
ENRICHMENT_METHOD=distribution
```

### Running the Application

```bash
# Start FastAPI backend
python -m uvicorn backend.router.main:app --reload --port 8000

# In another terminal, start Streamlit frontend
streamlit run frontend/app.py
```

### Data Ingestion

Run the CarbonDataAgent to load and process data:

```bash
python -m backend.agents.carbon_data_agent
```

Or use the migration script:

```bash
python run_migrations.py
```

## API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /report/generate` - Natural language report
- `POST /report/generate/structured` - JSON report
- `POST /report/submit` - Generate and submit report

### Company Data
- `GET /company/{name}` - Company snapshot
- `GET /company/{name}/summary` - Emissions summary
- `GET /company/{name}/energy` - Electricity estimation
- `GET /company/{name}/alerts` - Deviation alerts
- `GET /company/{name}/trends` - Historical trends

### Submissions
- `GET /submissions` - Submission history
- `GET /submissions/{confirmation_id}` - Specific submission

## Agents

### CarbonDataAgent
Loads emissions data from CSV, enriches with:
- Quarterly breakdowns (Q1-Q4)
- Supplier emissions (5 simulated suppliers)
- Electricity consumption estimates
- Employee counts and energy mix

Stores enriched data in PostgreSQL and creates vector embeddings in Pinecone.

### SustainabilityAgent
Performs analytical queries:
- Company snapshots
- Energy consumption calculations
- Deviation alert detection
- Historical trend analysis

### GenAI_Reporter
Uses LLaMA 3 (via Ollama) to:
- Answer natural language queries
- Generate structured ESG reports
- Create comparative analyses

### SubmissionAgent
Handles report submission:
- Validates reports against schema
- Saves JSON files to submissions/
- Maintains audit trail in PostgreSQL

### MasterAgent
Orchestrates all agents using LangChain ReAct agent with custom prompt for concise, factual responses.

## Data Simulation

### Quarterly Breakdowns
- Normal distribution with controlled variation (std: 0.10)
- Each quarter gets 15-35% of annual total
- Sum equals annual total

### Electricity Estimation
- Back-calculated from Scope 2 emissions
- Formula: `electricity_kWh = Scope2_tCO2e * 1000 / grid_factor`

### Supplier Breakdown
- Dirichlet distribution for proportional contributions
- 5 simulated suppliers

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_sustainability_agent.py

# Run with coverage
pytest --cov=backend --cov-report=html
```

## Linting

```bash
# Format code
black backend/ frontend/

# Lint
ruff check backend/

# Type check
mypy backend/
```

## License

MIT
