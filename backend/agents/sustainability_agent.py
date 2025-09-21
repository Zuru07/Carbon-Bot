# import os
# import logging
# import pandas as pd
# from sqlalchemy import create_engine
# from dotenv import load_dotenv
# from pathlib import Path

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# class SustainabilityAgent:
#     """
#     An agent for performing structured analytical queries against the
#     PostgreSQL database.
#     """
#     def __init__(self):
#         self.db_uri = os.getenv("POSTGRES_URI")
#         self.table_name = os.getenv("POSTGRES_TABLE_NAME", "enriched_company_emissions")
#         if not self.db_uri:
#             raise ValueError("POSTGRES_URI environment variable is not set.")
#         try:
#             self.engine = create_engine(self.db_uri)
#             logging.info("SustainabilityAgent connected to PostgreSQL successfully.")
#         except Exception as e:
#             logging.error(f"Failed to connect to PostgreSQL: {e}")
#             raise

#     def get_company_snapshot(self, company_name: str) -> dict | None:
#         """Retrieves all data for a single company."""
#         logging.info(f"Fetching snapshot for company: {company_name}")
#         try:
#             with self.engine.connect() as connection:
#                 query = f"SELECT * FROM {self.table_name} WHERE company_name = '{company_name}';"
#                 df = pd.read_sql(query, connection)
#             if df.empty:
#                 return None
#             return df.to_dict('records')[0]
#         except Exception as e:
#             logging.error(f"Error fetching company snapshot: {e}")
#             return None

#     def get_all_company_names(self) -> list:
#         """Retrieves a list of all unique company names."""
#         logging.info("Fetching all company names.")
#         try:
#             with self.engine.connect() as connection:
#                 query = f"SELECT DISTINCT company_name FROM {self.table_name} ORDER BY company_name;"
#                 df = pd.read_sql(query, connection)
#             return df['company_name'].tolist()
#         except Exception as e:
#             logging.error(f"Error fetching company names: {e}")
#             return []

# if __name__ == '__main__':
#     project_root = Path(__file__).resolve().parents[3]
#     load_dotenv(dotenv_path=project_root / ".env")
    
#     agent = SustainabilityAgent()
#     names = agent.get_all_company_names()
#     print(f"Found {len(names)} companies.")
    
#     if names:
#         snapshot = agent.get_company_snapshot(names[0])
#         print(f"\nSnapshot for {names[0]}:")
#         import json
#         print(json.dumps(snapshot, indent=2, default=str))

import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SustainabilityAgent:
    """
    An agent for performing structured analytical queries against the
    PostgreSQL database with robust, production-grade connection management.
    """
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        load_dotenv(dotenv_path=self.project_root / ".env")
        
        self.db_uri = os.getenv("POSTGRES_URI")
        self.table_name = os.getenv("POSTGRES_TABLE_NAME", "company_emissions")
        if not self.db_uri:
            raise ValueError("POSTGRES_URI environment variable is not set.")
        try:
            logging.info("Creating new SQLAlchemy engine...")
            # --- THE FIX: Add connection pooling and timeout settings ---
            self.engine = create_engine(
                self.db_uri,
                pool_recycle=1800,  # Recycle connections every 30 minutes (1800 seconds)
                connect_args={'connect_timeout': 10} # Set a 10-second timeout for new connections
            )
            # Test the connection immediately
            with self.engine.connect() as connection:
                logging.info("SustainabilityAgent connected to PostgreSQL successfully.")
        except Exception as e:
            logging.error(f"Failed to connect to PostgreSQL on initialization: {e}", exc_info=True)
            raise

    def get_company_snapshot(self, company_name: str) -> dict | None:
        """Retrieves all data for a single company using a safe, parameterized query."""
        logging.info(f"Fetching snapshot for company: '{company_name}'")
        try:
            with self.engine.connect() as connection:
                query = text(f"SELECT * FROM {self.table_name} WHERE company_name = :c_name")
                df = pd.read_sql(query, connection, params={"c_name": company_name})
            
            if df.empty:
                logging.warning(f"No data found for company: '{company_name}'")
                return None
            
            result_dict = df.to_dict('records')[0]
            for key, value in result_dict.items():
                if pd.isna(value): result_dict[key] = None
                elif hasattr(value, 'item'): result_dict[key] = value.item()
            return result_dict

        except Exception as e:
            logging.error(f"Error fetching company snapshot for '{company_name}': {e}", exc_info=True)
            return None

    def get_all_company_names(self) -> list:
        """Retrieves a list of all unique company names."""
        logging.info("Fetching all company names.")
        try:
            with self.engine.connect() as connection:
                query = f"SELECT DISTINCT company_name FROM {self.table_name} ORDER BY company_name;"
                df = pd.read_sql(query, connection)
            return df['company_name'].tolist()
        except Exception as e:
            logging.error(f"Error fetching company names: {e}", exc_info=True)
            return []

if __name__ == '__main__':
    # This test block now also uses the robust project_root logic
    try:
        agent = SustainabilityAgent()
        names = agent.get_all_company_names()
        print(f"Found {len(names)} companies.")
        
        if names:
            # Test with a specific company name from your dataset
            test_company = "Amazon.Com" 
            print(f"\n--- Testing Snapshot for: {test_company} ---")
            snapshot = agent.get_company_snapshot(test_company)
            if snapshot:
                import json
                print(json.dumps(snapshot, indent=2, default=str))
            else:
                print(f"Could not retrieve snapshot for {test_company}")
    except Exception as e:
        print(f"An error occurred during agent test: {e}")