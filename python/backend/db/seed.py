import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Loading env variables
load_dotenv()

# SQLAlchemy Init
db_url = os.getenv("POSTGRES_URI")
engine = create_engine(db_url)

# Load the CSV
df = pd.read_csv("cleaned_emissions.csv")

# Write to Postgres using engine
df.to_sql(
    name="company_emission",
    con=engine,
    if_exists="replace",
    index=False
)
