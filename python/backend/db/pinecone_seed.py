import re
from pinecone import Pinecone, ServerlessSpec
import pandas as pd
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
import getpass
import urllib.parse

# Load env variables
load_dotenv()

# Removing special characters and non-ascii symbols
def safe_id(name):
    safe = name.encode("ascii", "ignore").decode().lower()
    safe = re.sub(r'\s+', '_', safe)
    safe = re.sub(r'[^a-z0-9_]', '', safe)
    return safe

# Pinecone init
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "company-emissions-index"

embedding_model = SentenceTransformer("all-mpnet-base-v2")
dimension = embedding_model.get_sentence_embedding_dimension() 

# Create index if it doesn't exist
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(index_name)

# Load data from Postgres
db_url = os.getenv("POSTGRES_URI")
engine = create_engine(db_url)
df = pd.read_sql("SELECT * FROM company_emission", engine)

# Build vectors
vectors = []
for _, row in df.iterrows():
    description = (
        f"Company: {row['company_name']}\n"
        f"Sector: {row['sector']}\n"
        f"Headquarters: {row['headquarters_country']}\n"
        f"Employees: {row['employee_count']}\n"
        f"Energy Mix: {row['energy_mix_renewable']}% renewable, "
        f"{row['energy_mix_fossil']}% fossil, {row['energy_mix_nuclear']}% nuclear\n"
        f"Scope 1 Emissions: {row['scope1_total']} metric tons CO2e\n"
        f"Scope 2 Emissions: {row['scope2_total']} metric tons CO2e\n"
        f"Scope 3 Emissions: {row['scope3_total']} metric tons CO2e"
    )
    embedding = embedding_model.encode(description).tolist()
    vectors.append({
        "id": safe_id(row['company_name']),
        "values": embedding,
        "metadata": {
            "company_name": row['company_name'],
            "sector": row['sector'],
            "country": row['headquarters_country'],
            "reporting_year": row['reporting_year'],
            "employee_count": row['employee_count'],
            "scope1_total": row['scope1_total'],
            "scope2_total": row['scope2_total'],
            "scope3_total": row['scope3_total']
        }
    })

# Upsert to Pinecone
index.upsert(vectors)
