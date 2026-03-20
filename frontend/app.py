# frontend/app.py
import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / ".env")


# --- Custom CSS: Antigravity-Inspired Dark Theme ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #00f5d4;
        --secondary: #9b5de5;
        --accent: #f15bb5;
        --background: #0a0a0f;
        --surface: #12121a;
        --surface-light: #1a1a2e;
        --text: #e0e0e0;
        --text-muted: #8888aa;
        --glow-primary: 0 0 20px rgba(0, 245, 212, 0.5);
        --glow-secondary: 0 0 30px rgba(155, 93, 229, 0.5);
        --glow-accent: 0 0 25px rgba(241, 91, 181, 0.5);
    }
    
    * {
        font-family: 'Rajdhani', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
        background-attachment: fixed;
    }
    
    /* Stars effect */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20px 30px, #fff, transparent),
            radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
            radial-gradient(1px 1px at 90px 40px, #fff, transparent),
            radial-gradient(2px 2px at 130px 80px, rgba(255,255,255,0.6), transparent),
            radial-gradient(1px 1px at 160px 120px, #fff, transparent),
            radial-gradient(2px 2px at 200px 50px, rgba(255,255,255,0.7), transparent),
            radial-gradient(1px 1px at 250px 160px, #fff, transparent),
            radial-gradient(2px 2px at 300px 100px, rgba(255,255,255,0.5), transparent),
            radial-gradient(1px 1px at 350px 200px, #fff, transparent),
            radial-gradient(2px 2px at 400px 60px, rgba(255,255,255,0.8), transparent);
        background-repeat: repeat;
        background-size: 400px 300px;
        pointer-events: none;
        z-index: 0;
        opacity: 0.6;
        animation: twinkle 8s ease-in-out infinite;
    }
    
    @keyframes twinkle {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 0.9; }
    }
    
    /* Main title styling */
    .main-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 40px rgba(0, 245, 212, 0.3);
        letter-spacing: 3px;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: var(--text-muted);
        letter-spacing: 2px;
        text-transform: uppercase;
        position: relative;
        z-index: 1;
    }
    
    /* Card styling */
    .css-1r6slb0, .css-ocqtc7, [data-testid="stCard"] {
        background: rgba(18, 18, 26, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(155, 93, 229, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: var(--glow-secondary);
        transition: all 0.3s ease;
    }
    
    .css-1r6slb0:hover, .css-ocqtc7:hover {
        border-color: var(--primary);
        box-shadow: var(--glow-primary);
        transform: translateY(-2px);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(145deg, rgba(18, 18, 26, 0.9), rgba(26, 26, 46, 0.9));
        border: 1px solid rgba(0, 245, 212, 0.4);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: var(--glow-primary);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: scale(1.02);
        box-shadow: 0 0 40px rgba(0, 245, 212, 0.6);
    }
    
    .metric-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
        text-shadow: 0 0 10px rgba(0, 245, 212, 0.5);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }
    
    /* Section headers */
    .section-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--secondary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--secondary);
        text-shadow: 0 0 15px rgba(155, 93, 229, 0.4);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--secondary) 0%, var(--accent) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 2rem;
        font-family: 'Orbitron', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        box-shadow: var(--glow-secondary);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        box-shadow: var(--glow-primary), var(--glow-secondary);
        transform: translateY(-2px);
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(18, 18, 26, 0.9);
        border: 1px solid rgba(155, 93, 229, 0.5);
        border-radius: 8px;
        color: var(--text);
        font-size: 1.1rem;
        padding: 0.8rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary);
        box-shadow: var(--glow-primary);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 10, 15, 0.95), rgba(26, 26, 46, 0.95));
        border-right: 1px solid rgba(155, 93, 229, 0.3);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: var(--primary);
        font-family: 'Orbitron', sans-serif;
    }
    
    /* Success/Error/Info boxes */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Charts */
    [data-testid="stVegaLiteChart"], [data-testid="stDeckGlChart"] {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--primary) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(18, 18, 26, 0.8);
        border: 1px solid rgba(155, 93, 229, 0.3);
        border-radius: 8px 8px 0 0;
        padding: 0.8rem 1.5rem;
        color: var(--text-muted);
        font-family: 'Orbitron', sans-serif;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(155, 93, 229, 0.2);
        color: var(--primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(0, 245, 212, 0.1) !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(18, 18, 26, 0.8);
        border: 1px solid rgba(155, 93, 229, 0.3);
        border-radius: 8px;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--secondary), transparent);
        margin: 2rem 0;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--background);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--secondary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Floating animation */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .floating {
        animation: float 4s ease-in-out infinite;
    }
</style>
""", unsafe_allow_html=True)


# --- Page Configuration ---
st.set_page_config(
    page_title="ESG Reporting AI",
    page_icon=":leaf:",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- Helper Functions ---
def create_metric_card(value, label, delta=None):
    """Creates a styled metric card."""
    delta_html = f'<span style="color: var(--primary); font-size: 0.9rem;">{delta}</span>' if delta else ''
    html = f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def create_section_header(title):
    """Creates a styled section header."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


# --- Agent Initialization ---
@st.cache_resource
def init_agents():
    """Initialize all agents with caching."""
    try:
        from backend.orchestrator import MasterAgent
        from backend.agents.submission_agent import SubmissionAgent
        from backend.agents.sustainability_agent import SustainabilityAgent
        from backend.agents.genai_reporter import GenAI_Reporter
        
        return {
            'master_agent': MasterAgent(),
            'submission_agent': SubmissionAgent(),
            'sustainability_agent': SustainabilityAgent(),
            'genai_reporter': GenAI_Reporter()
        }
    except Exception as e:
        return {'error': str(e)}


agents = init_agents()

if 'error' in agents:
    st.error(f"Failed to initialize agents: {agents['error']}")
    st.info("Please ensure Ollama is running and environment variables are configured.")
    st.stop()


# --- Sidebar ---
with st.sidebar:
    st.markdown('<h1 style="font-size: 1.8rem; margin-bottom: 1rem;">Control Center</h1>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    create_section_header("Quick Actions")
    
    if st.button("Dashboard", use_container_width=True):
        st.session_state['current_view'] = 'dashboard'
    
    if st.button("Query Data", use_container_width=True):
        st.session_state['current_view'] = 'query'
    
    if st.button("Generate Report", use_container_width=True):
        st.session_state['current_view'] = 'report'
    
    if st.button("Submission History", use_container_width=True):
        st.session_state['current_view'] = 'submissions'
    
    st.markdown("---")
    
    create_section_header("Settings")
    
    report_type = st.selectbox(
        "Report Type",
        ["annual", "quarterly", "spot"],
        index=0
    )
    
    output_format = st.selectbox(
        "Output Format",
        ["text", "json", "both"],
        index=0
    )
    
    st.markdown("---")
    st.markdown('<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">Carbon-bot v2.0</p>', unsafe_allow_html=True)


# --- Main Content ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<h1 class="main-title">ESG REPORTING AI</h1>', unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="text-align: right; padding-top: 1rem;">
        <span style="color: var(--primary); font-size: 0.9rem;">[LIVE]</span>
        <br>
        <span style="color: var(--text-muted); font-size: 0.8rem;">System Online</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<p class="subtitle">Multi-Agent Carbon Intensity Analysis & Reporting</p>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# --- Tabs for Different Views ---
tab1, tab2, tab3, tab4 = st.tabs(["Query Interface", "Dashboard", "Report Generation", "Submissions"])


# --- Tab 1: Query Interface ---
with tab1:
    create_section_header("Natural Language Query")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "",
            placeholder="Ask anything about ESG data...",
            label_visibility="collapsed"
        )
    with col2:
        search_btn = st.button("Analyze", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if query and search_btn:
        with st.spinner("AI is analyzing your query..."):
            try:
                result = agents['master_agent'].run(query)
                response = result.get('output', str(result))
                
                create_section_header("Analysis Result")
                st.success("Analysis Complete!")
                
                st.markdown(f"""
                <div style="background: rgba(18, 18, 26, 0.9); border: 1px solid var(--primary); 
                            border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                    <p style="color: var(--text); line-height: 1.8; font-size: 1.1rem;">
                        {response}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Check for company mentions
                company_list = agents['sustainability_agent'].get_all_company_names()
                detected_company = next((name for name in company_list if name.lower() in query.lower()), None)
                
                if detected_company:
                    st.info(f"Company Detected: **{detected_company}**")
                    
                    # Show quick metrics
                    snapshot = agents['sustainability_agent'].get_company_snapshot(detected_company)
                    if snapshot:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            create_metric_card(f"{snapshot.get('scope1_total', 0):,.0f}", "Scope 1 (tCO2e)")
                        with col2:
                            create_metric_card(f"{snapshot.get('scope2_total', 0):,.0f}", "Scope 2 (tCO2e)")
                        with col3:
                            create_metric_card(f"{snapshot.get('scope3_total', 0):,.0f}", "Scope 3 (tCO2e)")
                        with col4:
                            total = (snapshot.get('scope1_total', 0) or 0) + (snapshot.get('scope2_total', 0) or 0) + (snapshot.get('scope3_total', 0) or 0)
                            create_metric_card(f"{total:,.0f}", "Total (tCO2e)")
                            
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
    
    if not query:
        st.info("Tip: 'Compare emissions between Amazon and Microsoft' or 'What are the Scope 1 emissions for BP?'")


# --- Tab 2: Dashboard ---
with tab2:
    create_section_header("Company Data Overview")
    
    company_list = agents['sustainability_agent'].get_all_company_names()
    
    if company_list:
        selected_company = st.selectbox("Select a company:", company_list)
        
        if selected_company:
            snapshot = agents['sustainability_agent'].get_company_snapshot(selected_company)
            
            if snapshot:
                col1, col2, col3 = st.columns(3)
                
                scope1 = snapshot.get('scope1_total', 0) or 0
                scope2 = snapshot.get('scope2_total', 0) or 0
                scope3 = snapshot.get('scope3_total', 0) or 0
                total = scope1 + scope2 + scope3
                
                with col1:
                    st.markdown("""
                    <div class="metric-card" style="border-color: #00f5d4;">
                        <div style="color: var(--primary); font-size: 0.8rem; text-transform: uppercase;">Scope 1</div>
                        <div class="metric-value">{:,.0f}</div>
                        <div class="metric-label">metric tons CO2e</div>
                    </div>
                    """.format(scope1), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div class="metric-card" style="border-color: #9b5de5;">
                        <div style="color: var(--secondary); font-size: 0.8rem; text-transform: uppercase;">Scope 2</div>
                        <div class="metric-value">{:,.0f}</div>
                        <div class="metric-label">metric tons CO2e</div>
                    </div>
                    """.format(scope2), unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                    <div class="metric-card" style="border-color: #f15bb5;">
                        <div style="color: var(--accent); font-size: 0.8rem; text-transform: uppercase;">Scope 3</div>
                        <div class="metric-value">{:,.0f}</div>
                        <div class="metric-label">metric tons CO2e</div>
                    </div>
                    """.format(scope3), unsafe_allow_html=True)
                
                st.markdown("<hr>", unsafe_allow_html=True)
                
                # Additional metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    create_metric_card(f"{total:,.0f}", "Total Emissions")
                
                with col2:
                    elec = snapshot.get('electricity_kwh', 0) or 0
                    create_metric_card(f"{elec/1e6:.1f}M", "Electricity (kWh)")
                
                with col3:
                    employees = snapshot.get('employee_count', 0) or 0
                    create_metric_card(f"{employees:,}", "Employees")
                
                with col4:
                    intensity = total / employees if employees > 0 else 0
                    create_metric_card(f"{intensity:,.0f}", "tCO2e/Employee")
                
                # Energy Mix
                st.markdown("<br>", unsafe_allow_html=True)
                create_section_header("Energy Mix")
                
                col1, col2, col3 = st.columns(3)
                
                renewable = snapshot.get('energy_mix_renewable_pct', 0) or 0
                fossil = snapshot.get('energy_mix_fossil_pct', 0) or 0
                nuclear = snapshot.get('energy_mix_nuclear_pct', 0) or 0
                
                with col1:
                    st.progress(renewable/100, text=f"Renewable: {renewable:.1f}%")
                with col2:
                    st.progress(fossil/100, text=f"Fossil: {fossil:.1f}%")
                with col3:
                    st.progress(nuclear/100, text=f"Nuclear: {nuclear:.1f}%")
                
                # Alerts
                st.markdown("<br>", unsafe_allow_html=True)
                alerts = agents['sustainability_agent'].check_deviation_alerts(selected_company)
                
                if alerts:
                    st.warning(f"{len(alerts)} deviation(s) detected")
                    for alert in alerts:
                        st.markdown(f"""
                        <div style="background: rgba(241, 91, 181, 0.1); border-left: 3px solid var(--accent); 
                                    padding: 0.8rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0;">
                            <strong style="color: var(--accent);">[{alert.get('severity', 'info').upper()}]</strong>
                            {alert.get('message', '')}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("No significant deviations detected")
    else:
        st.warning("No companies found in the database.")


# --- Tab 3: Report Generation ---
with tab3:
    create_section_header("Generate ESG Report")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        report_company = st.selectbox("Select company for report:", company_list if company_list else ["No companies available"])
    
    with col2:
        report_type = st.selectbox("Report Type:", ["annual", "quarterly", "spot"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        generate_btn = st.button("Generate Report", use_container_width=True)
    
    with col2:
        submit_btn = st.button("Generate & Submit", use_container_width=True)
    
    if generate_btn and report_company != "No companies available":
        with st.spinner("Generating report..."):
            try:
                snapshot = agents['sustainability_agent'].get_company_snapshot(report_company)
                alerts = agents['sustainability_agent'].check_deviation_alerts(report_company)
                
                report = agents['genai_reporter'].generate_structured_esg_report(
                    company_name=report_company,
                    snapshot=snapshot,
                    alerts=alerts,
                    report_type=report_type
                )
                
                create_section_header("Generated Report")
                
                st.json(report.model_dump())
                
                st.download_button(
                    "Download Report (JSON)",
                    data=report.model_dump_json(indent=2),
                    file_name=f"ESG_Report_{report_company}_{report_type}.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"Report generation failed: {str(e)}")
    
    if submit_btn and report_company != "No companies available":
        with st.spinner("Generating and submitting report..."):
            try:
                snapshot = agents['sustainability_agent'].get_company_snapshot(report_company)
                alerts = agents['sustainability_agent'].check_deviation_alerts(report_company)
                
                report = agents['genai_reporter'].generate_structured_esg_report(
                    company_name=report_company,
                    snapshot=snapshot,
                    alerts=alerts,
                    report_type=report_type
                )
                
                receipt = agents['submission_agent'].submit_structured_report(report)
                
                if receipt.get('status') == 'SUCCESS':
                    st.success("Report Submitted Successfully!")
                    st.json(receipt)
                else:
                    st.error("Submission Failed")
                    
            except Exception as e:
                st.error(f"Submission failed: {str(e)}")


# --- Tab 4: Submissions ---
with tab4:
    create_section_header("Submission History")
    
    history = agents['submission_agent'].get_submission_history(limit=20)
    
    if history:
        for sub in history:
            st.markdown(f"""
            <div style="background: rgba(18, 18, 26, 0.9); border: 1px solid rgba(155, 93, 229, 0.3); 
                        border-radius: 12px; padding: 1.2rem; margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: var(--primary); font-size: 1.1rem;">{sub.get('company_name', 'Unknown')}</strong>
                        <div style="color: var(--text-muted); font-size: 0.9rem;">
                            Year: {sub.get('reporting_year', 'N/A')} | Version: {sub.get('report_version', 1)}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {'rgba(0, 245, 212, 0.2)' if sub.get('submission_status') == 'SUCCESS' else 'rgba(241, 91, 181, 0.2)'}; 
                                     color: {'var(--primary)' if sub.get('submission_status') == 'SUCCESS' else 'var(--accent)'}; 
                                     padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem;">
                            {sub.get('submission_status', 'UNKNOWN')}
                        </span>
                        <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.5rem;">
                            ID: {str(sub.get('confirmation_id', ''))[:8]}...
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No submissions found. Generate and submit a report to see history here.")


# --- Footer ---
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: var(--text-muted); padding: 1rem 0;">
    <p style="font-size: 0.9rem;">
        Carbon-bot | Multi-Agent ESG Reporting System
    </p>
    <p style="font-size: 0.8rem; opacity: 0.7;">
        Powered by LangChain + LLaMA 3 | Data storage: PostgreSQL + Pinecone
    </p>
</div>
""", unsafe_allow_html=True)
