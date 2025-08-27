# seed_prod.py
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv
import logging

# --- Configuration ---
# Loading Env Variables
load_dotenv()

# Use logging for clear, standardized output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# All configurable variables should be in one place.
CONFIG = {
    "db_uri": os.getenv("POSTGRES_URI"),
    "csv_path": os.getenv("CSV_PATH"),
    "table_name": "company_emissions", # Corrected from your code
    "if_exists": "replace" # Acknowledge this is for dev; for prod, this would be 'append' or a custom upsert
}

# --- Main Logic ---
def main():
    """Main function to load data from CSV to PostgreSQL."""
    if not CONFIG["db_uri"]:
        logging.error("Database URI is not set. Please check your .env file.")
        return

    try:
        engine = create_engine(CONFIG["db_uri"])
        # Use a context manager to ensure the connection is closed.
        with engine.connect() as connection:
            logging.info(f"Successfully connected to the database.")
            
            # Check if the CSV file exists before trying to read it.
            if not os.path.exists(CONFIG["csv_path"]):
                logging.error(f"Data file not found at: {CONFIG['csv_path']}")
                return

            logging.info(f"Reading data from {CONFIG['csv_path']}...")
            df = pd.read_csv(CONFIG["csv_path"])

            logging.info(f"Writing {len(df)} records to table '{CONFIG['table_name']}'...")
            df.to_sql(
                name=CONFIG["table_name"],
                con=connection,
                if_exists=CONFIG["if_exists"],
                index=False
            )
            logging.info("Data loading complete.")

    except OperationalError as e:
        logging.error(f"Database connection failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()