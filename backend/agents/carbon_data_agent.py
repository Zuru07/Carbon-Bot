import os
import re
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CarbonDataAgent:
    """
    An agent responsible for the entire data ingestion and vectorization pipeline.
    It loads data from a CSV, stores it in a relational database (PostgreSQL),
    creates semantic vector embeddings, and upserts them into a vector database (Pinecone).
    """

    def __init__(self):
        """
        Initializes the agent by loading configuration and setting up necessary clients.
        """
        logging.info("Initializing CarbonDataAgent...")
        self._load_config()
        
        # Initialize the embedding model once
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()

        # Initialize Pinecone client
        self.pinecone = Pinecone(api_key=self.pinecone_api_key)

    def _load_config(self):
        """Loads required configuration from environment variables."""
        self.postgres_uri = os.getenv("POSTGRES_URI")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.csv_path = os.getenv("CSV_PATH", "cleaned_emissions.csv")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "company-emissions-index")
        self.postgres_table_name = os.getenv("POSTGRES_TABLE_NAME", "company_emissions")
        self.batch_size = int(os.getenv("PINECONE_BATCH_SIZE", "32"))

        if not all([self.postgres_uri, self.pinecone_api_key, self.csv_path]):
            raise ValueError("One or more critical environment variables are not set: POSTGRES_URI, PINECONE_API_KEY, CSV_PATH")
        logging.info("Configuration loaded successfully.")

    def _safe_id(self, name: str) -> str:
        """Normalizes a company name into a safe, file-system friendly ID."""
        safe = str(name).encode("ascii", "ignore").decode().lower()
        safe = re.sub(r'\s+', '_', safe)
        safe = re.sub(r'[^a-z0-9_]', '', safe)
        return safe

    def _create_description(self, row: pd.Series) -> str:
        """Creates a rich text description of a company for vector embedding."""
        return (
            f"Company: {row.get('company_name', 'N/A')}\n"
            f"Sector: {row.get('sector', 'N/A')}\n"
            f"Headquarters: {row.get('headquarters_country', 'N/A')}\n"
            f"Reporting Year: {row.get('reporting_year', 'N/A')}\n"
            f"Scope 1 Emissions: {row.get('scope1_total', 0):.2f} metric tons CO2e\n"
            f"Scope 2 Emissions: {row.get('scope2_total', 0):.2f} metric tons CO2e\n"
            f"Scope 3 Emissions: {row.get('scope3_total', 0):.2f} metric tons CO2e"
        )

    def load_csv(self) -> pd.DataFrame | None:
        """Loads the source CSV into a pandas DataFrame."""
        if not os.path.exists(self.csv_path):
            logging.error(f"Data file not found at: {self.csv_path}")
            return None
        logging.info(f"Loading data from {self.csv_path}...")
        try:
            df = pd.read_csv(self.csv_path)
            logging.info(f"Successfully loaded {len(df)} records from CSV.")
            return df
        except Exception as e:
            logging.error(f"Failed to read CSV file: {e}")
            return None

    def store_postgres(self, df: pd.DataFrame):
        """Saves the DataFrame to a PostgreSQL table."""
        logging.info(f"Attempting to store {len(df)} records in PostgreSQL table '{self.postgres_table_name}'...")
        try:
            engine = create_engine(self.postgres_uri)
            with engine.connect() as connection:
                df.to_sql(
                    name=self.postgres_table_name,
                    con=connection,
                    if_exists="replace", # Use "replace" for idempotency in seeding
                    index=False
                )
                logging.info("Data successfully stored in PostgreSQL.")
        except OperationalError as e:
            logging.error(f"PostgreSQL connection failed: {e}")
            raise
        except Exception as e:
            logging.error(f"An error occurred during PostgreSQL storage: {e}")
            raise

    def store_pinecone(self, df: pd.DataFrame):
        """Generates embeddings and upserts data into a Pinecone index."""
        logging.info("Preparing to store data in Pinecone...")
        
        # 1. Create index if it doesn't exist
        if self.pinecone_index_name not in self.pinecone.list_indexes().names():
            logging.info(f"Pinecone index '{self.pinecone_index_name}' not found. Creating new index...")
            self.pinecone.create_index(
                name=self.pinecone_index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        index = self.pinecone.Index(self.pinecone_index_name)
        
        # 2. Process and upsert in batches for efficiency
        logging.info(f"Upserting {len(df)} records to Pinecone in batches of {self.batch_size}...")
        for i in tqdm(range(0, len(df), self.batch_size), desc="Upserting to Pinecone"):
            batch_df = df.iloc[i:i + self.batch_size]
            
            descriptions = batch_df.apply(self._create_description, axis=1).tolist()
            embeddings = self.embedding_model.encode(descriptions).tolist()
            
            vectors_to_upsert = []
            for idx, (row_index, row) in enumerate(batch_df.iterrows()):
                vectors_to_upsert.append({
                    "id": self._safe_id(row['company_name']),
                    "values": embeddings[idx],
                    "metadata": {
                        "company_name": row.get('company_name', 'N/A'),
                        "sector": row.get('sector', 'N/A'),
                        "reporting_year": int(row.get('reporting_year', 0)),
                        "scope1_total": float(row.get('scope1_total', 0)),
                        "scope2_total": float(row.get('scope2_total', 0)),
                        "scope3_total": float(row.get('scope3_total', 0))
                    }
                })
            
            if vectors_to_upsert:
                index.upsert(vectors=vectors_to_upsert)
        
        logging.info("Data successfully stored in Pinecone.")

    def run(self):
        """
        Orchestrates the entire data ingestion pipeline.
        This ensures Postgres and Pinecone are always synced from the same source data.
        """
        logging.info("--- Starting Data Ingestion Pipeline ---")
        # Step 1: Load data from the source file
        data_df = self.load_csv()
        if data_df is None:
            logging.error("Pipeline halted: Could not load source data.")
            return

        # Step 2: Store factual data in the relational database
        try:
            self.store_postgres(data_df)
        except Exception:
            logging.error("Pipeline halted: Failed to store data in PostgreSQL.")
            return
            
        # Step 3: Store vector embeddings for semantic search
        try:
            self.store_pinecone(data_df)
        except Exception as e:
            logging.error(f"Pipeline failed during Pinecone storage: {e}")
            return
            
        logging.info("--- Data Ingestion Pipeline Finished Successfully ---")

def main():
    """Entry point function to initialize and run the agent."""
    # --- Load Environment Variables ---
    # This searches for .env in the current dir or parent dirs, which is robust
    if not load_dotenv():
        # A fallback if .env is not found automatically
        project_root = Path(__file__).resolve().parents[3] # Assumes /python/server/agents
        dotenv_path = project_root / ".env"
        if dotenv_path.exists():
            logging.info(f"Loading .env from calculated path: {dotenv_path}")
            load_dotenv(dotenv_path=dotenv_path)
        else:
            logging.warning("Could not find .env file. Agent may fail if env vars are not set.")

    try:
        agent = CarbonDataAgent()
        agent.run()
    except Exception as e:
        logging.critical(f"A critical error occurred in the agent: {e}")

if __name__ == '__main__':
    main()