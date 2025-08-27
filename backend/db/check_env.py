# check_env.py
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Test 1: Check current working directory ---
cwd = os.getcwd()
logging.info(f"Current Working Directory is: {cwd}")

# --- Test 2: Check for a .env file in the CWD ---
env_file_in_cwd_path = os.path.join(cwd, '.env')
if os.path.exists(env_file_in_cwd_path):
    logging.info(f"Found '.env' file at: {env_file_in_cwd_path}")
else:
    logging.warning(f"'.env' file NOT FOUND in current directory.")

# --- Test 3: Attempt to load the .env file from the CWD ---
logging.info("Attempting to load .env from the current directory...")
load_dotenv()
postgres_uri = os.getenv("POSTGRES_URI")

# --- Test 4: Report the result ---
if postgres_uri:
    logging.info("SUCCESS: The 'POSTGRES_URI' variable was loaded.")
    # For security, we only print a portion of the URI
    print(f"   - Loaded value starts with: {postgres_uri[:20]}...")
else:
    logging.error("FAILURE: The 'POSTGRES_URI' variable was NOT loaded.")