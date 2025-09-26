# frontend/app.py
import streamlit as st
import sys
from pathlib import Path
import json

# --- Path Correction & Imports ---
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
from backend.orchestrator import MasterAgent
from backend.agents.submission_agent import SubmissionAgent
from backend.agents.sustainability_agent import SustainabilityAgent
from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / ".env")


# --- Page Configuration ---
st.set_page_config(page_title="ESG Reporting AI", page_icon="🌿", layout="wide")

# --- Agent Initialization ---
if "agents_initialized" not in st.session_state:
    with st.spinner("Initializing AI Orchestrator and Agents..."):
        try:
            st.session_state.master_agent = MasterAgent()
            st.session_state.submission_agent = SubmissionAgent()
            st.session_state.sustainability_agent = SustainabilityAgent()
            st.session_state.agents_initialized = True
        except Exception as e:
            st.error(f"Failed to initialize agents: {e}")
            st.stop()

# --- UI Layout ---
st.title("🌿 ESG & Carbon Intensity Reporting AI")
st.markdown("An orchestrated multi-agent system for ESG analysis and submission.")

# --- Main Agent Interface ---
st.header("Unified Agent Interface")
query = st.text_input("Enter your query:", placeholder="e.g., Get a full report for BP for submission")

with st.form("report_form"):
    submitted = st.form_submit_button("Generate & Submit Report")
    if submitted:
        if query:
            report_content = ""
            with st.spinner("Orchestrator is generating the report..."):
                result = st.session_state.master_agent.run(query)
                report_content = result.get('output', str(result))

            # --- THE FIX: Search for the company name in the report text ---
            st.info("Parsing generated report to identify the subject company...")
            company_list = st.session_state.sustainability_agent.get_all_company_names()
            
            # Find which company name from your database is mentioned in the report
            company_name_in_report = next((name for name in company_list if name in report_content), "UnknownCompany")
            
            st.success(f"Company Identified: {company_name_in_report}")

            simulated_report_data = {
                "query": query,
                "generated_report": report_content,
                "company_name": company_name_in_report, # Use the name found in the report
                "reporting_year": 2024
            }

            with st.spinner("Submission Agent is filing the report..."):
                receipt = st.session_state.submission_agent.submit_report(simulated_report_data)
            
            st.markdown("### Agent Response:")
            st.text(report_content)
            st.markdown("---")
            if receipt['status'] == 'SUCCESS':
                st.success("Report Submitted Successfully!")
                st.json(receipt)
            else:
                st.error("Report Submission Failed.")
                st.json(receipt)
        else:
            st.warning("Please enter a query.")