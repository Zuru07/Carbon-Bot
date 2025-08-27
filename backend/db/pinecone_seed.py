# pipeline_seed_prod.py
import re
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
import logging
from tqdm import tqdm

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG = {
    "pinecone_api_key": os.getenv("PINECONE_API_KEY"),
    "pinecone_index_name": "company-emissions-index",
    "db_uri": os.getenv("POSTGRES_URI"), # Keep for a single source of config
    "csv_path": "cleaned_emissions.csv",
    "table_name": "company_emissions",
    "batch_size": 32 # Control how many vectors are processed/upserted at once
}

# --- Helper Functions ---
def safe_id(name):
    safe = str(name).encode("ascii", "ignore").decode().lower()
    safe = re.sub(r'\s+', '_', safe)
    safe = re.sub(r'[^a-z0-9_]', '', safe)
    return safe

def create_description(row):
    # This function is now separate for clarity and testability.
    return (
        f"Company: {row['company_name']}\n"
        f"Sector: {row['sector']}\n"
        f"Headquarters: {row['headquarters_country']}\n"
        f"Scope 1 Emissions: {row['scope1_total']} metric tons CO2e\n"
        f"Scope 2 Emissions: {row['scope2_total']} metric tons CO2e\n"
        f"Scope 3 Emissions: {row['scope3_total']} metric tons CO2e"
    )

# --- Main Logic ---
def main():
    """Main function to load data and create vector embeddings in batches."""
    # --- Initialization ---
    pc = Pinecone(api_key=CONFIG["pinecone_api_key"])
    embedding_model = SentenceTransformer("all-mpnet-base-v2")
    dimension = embedding_model.get_sentence_embedding_dimension()
    
    # --- Create Pinecone Index if Needed ---
    if CONFIG["pinecone_index_name"] not in pc.list_indexes().names():
        logging.info(f"Creating new Pinecone index: {CONFIG['pinecone_index_name']}")
        pc.create_index(
            name=CONFIG["pinecone_index_name"],
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    index = pc.Index(CONFIG["pinecone_index_name"])
    
    # --- Load Data ---
    if not os.path.exists(CONFIG["csv_path"]):
        logging.error(f"Data file not found at: {CONFIG['csv_path']}")
        return
    df = pd.read_csv(CONFIG["csv_path"])

    # --- Process and Upsert in Batches ---
    logging.info(f"Processing and upserting {len(df)} records in batches of {CONFIG['batch_size']}...")
    for i in tqdm(range(0, len(df), CONFIG["batch_size"])):
        batch_df = df.iloc[i:i + CONFIG["batch_size"]]
        
        # 1. Create descriptions and embeddings for the batch
        descriptions = batch_df.apply(create_description, axis=1).tolist()
        embeddings = embedding_model.encode(descriptions).tolist()
        
        # 2. Prepare vector objects for upsert
        vectors_to_upsert = []
        for idx, (row_index, row) in enumerate(batch_df.iterrows()):
            vectors_to_upsert.append({
                "id": safe_id(row['company_name']),
                "values": embeddings[idx],
                "metadata": {
                    "company_name": row['company_name'],
                    "sector": row['sector'],
                    "reporting_year": int(row['reporting_year']),
                    "scope1_total": float(row['scope1_total']),
                    "scope2_total": float(row['scope2_total']),
                    "scope3_total": float(row['scope3_total'])
                }
            })
        
        # 3. Upsert the batch to Pinecone
        if vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)
            
    logging.info("Pinecone upsert complete.")

if __name__ == "__main__":
    load_dotenv()
    main()