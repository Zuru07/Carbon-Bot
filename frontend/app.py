# frontend/app.py
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# --- Path Correction & Imports ---
# This block robustly finds the project root and adds it to the system path.
try:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.append(str(project_root))
    from backend.agents.sustainability_agent import SustainabilityAgent
    from backend.agents.genai_reporter import GenAI_Reporter
except ImportError:
    st.error("Fatal Error: Could not import agent modules. Please ensure your project structure is correct and that 'backend' and 'backend/agents' directories contain an '__init__.py' file.")
    st.stop()

from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / ".env")


# --- Page Configuration ---
st.set_page_config(page_title="ESG Reporting AI", page_icon="🌿", layout="wide")

# --- Agent Initialization using Session State ---
if "agents_initialized" not in st.session_state:
    with st.spinner("Initializing AI agents... This may take a moment."):
        try:
            st.session_state.sustainability_agent = SustainabilityAgent()
            st.session_state.genai_reporter = GenAI_Reporter()
            st.session_state.agents_initialized = True
        except Exception as e:
            st.error(f"Failed to initialize agents: {e}")
            st.stop()

# --- UI Layout ---
st.title("🌿 ESG & Carbon Intensity Reporting AI")
st.markdown("An AI-powered system to analyze and report on corporate emissions data.")

# --- Main AI Reporter Section ---
st.header("Ask the AI Analyst")
query = st.text_input("Enter your question:", placeholder="e.g., Compare the total emissions of BP and Shell")

if st.button("Generate Report"):
    if query:
        with st.spinner("The AI is writing your report..."):
            report = st.session_state.genai_reporter.generate_report(query)
            st.markdown(report)
    else:
        st.warning("Please enter a question.")

# --- Data Snapshot Section ---
st.header("Company Data Snapshot")
st.markdown("Select a company to view its detailed data from our database.")

@st.cache_data
def get_company_names():
    return st.session_state.sustainability_agent.get_all_company_names()

company_names = get_company_names()
selected_company = st.selectbox("Choose a company:", options=company_names)

if selected_company:
    snapshot = st.session_state.sustainability_agent.get_company_snapshot(selected_company)
    if snapshot:
        st.dataframe(pd.DataFrame([snapshot]))
    else:
        st.error(f"Could not retrieve data for {selected_company}.")