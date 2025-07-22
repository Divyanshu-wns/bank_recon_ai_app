# app.py
import streamlit as st
from agents.orchestrator import AgentOrchestrator
from utils.pdf_parser import extract_text_from_pdf
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="Bank Reconciliation AI (Agents)", layout="centered")

# Initialize the consent state in session state if it doesn't exist
if 'consent_given' not in st.session_state:
    st.session_state.consent_given = False

# --- Title ---
st.title("🤖 AI-Powered Bank Reconciliation (Multi-Agent)")

# --- Consent Section ---
if not st.session_state.consent_given:
    st.warning("⚠️ Important: Data Privacy Notice")
    st.markdown("""
    Please be aware that:
    - This application processes Excel files and SOP documents
    - We use external services including OpenAI's LLM for data processing
    - DO NOT upload files containing sensitive, confidential, or real customer data
    - All data processing is done in-memory and not stored permanently
    """)
    
    consent = st.checkbox("I understand and confirm that I will not upload any sensitive or real customer data")
    
    if consent:
        if st.button("Proceed to Application"):
            st.session_state.consent_given = True
            st.rerun()
            
else:
    # --- Instructions Section ---
    with st.expander("📋 Input File Requirements", expanded=True):
        st.markdown("""
        ### Excel File Format
        Please upload a single Excel file (.xlsx) containing:

        1. A sheet named **'EDW'**
        2. A sheet named **'Journal'**

        ⚠️ Sheet names must match exactly as shown above (case-sensitive).

        ### Basic Format Example:
        ```
        EDW sheet:
        Account Number | Transaction Date | Amount

        Journal sheet:
        Account Number | Journal Date | Debit Amount | Credit Amount
        ```
        """)

    # --- Upload Section ---
    st.markdown("""
    Upload your Excel file with `EDW` and `Journal` sheets, and optionally an SOP PDF for contextual intelligence.
    """)

    uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

    # Check if PDF parsing is available
    try:
        from utils.pdf_parser import extract_text_from_pdf
        sop_file = st.file_uploader("📘 Upload SOP / Policy PDF (optional)", type=["pdf"])
    except ImportError:
        st.warning("📘 PDF parsing is not available. SOP upload is disabled.")
        sop_file = None

    # --- Process Button ---
    if uploaded_file and st.button("🚀 Run Reconciliation"):
        logs = []

        # 1. Get Azure OpenAI credentials
        def get_azure_openai_config():
            # Try environment variables first
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("OPENAI_API_VERSION")
            model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
            
            # Fall back to Streamlit secrets
            if not azure_endpoint and "azure_openai" in st.secrets and "azure_endpoint" in st.secrets["azure_openai"]:
                azure_endpoint = st.secrets["azure_openai"]["azure_endpoint"]
            if not api_key and "azure_openai" in st.secrets and "api_key" in st.secrets["azure_openai"]:
                api_key = st.secrets["azure_openai"]["api_key"]
            if not api_version and "azure_openai" in st.secrets and "api_version" in st.secrets["azure_openai"]:
                api_version = st.secrets["azure_openai"]["api_version"]
            if not model_name and "azure_openai" in st.secrets and "model_name" in st.secrets["azure_openai"]:
                model_name = st.secrets["azure_openai"]["model_name"]

            if not (azure_endpoint and api_key and api_version and model_name):
                st.error("❌ Azure OpenAI credentials not found. Please set them in environment variables or Streamlit secrets.")
                st.stop()
            return {
                "azure_endpoint": azure_endpoint,
                "api_key": api_key,
                "api_version": api_version,
                "model_name": model_name
            }

        azure_config = get_azure_openai_config()

        # 2. Extract SOP text
        sop_text = ""
        if sop_file:
            with st.spinner("📖 Reading SOP PDF..."):
                try:
                    sop_text = extract_text_from_pdf(sop_file)
                    if sop_text:
                        st.success("✅ SOP loaded successfully.")
                    else:
                        st.warning("⚠️ Could not read SOP. Proceeding without SOP context.")
                except Exception as e:
                    st.warning(f"⚠️ Could not read SOP: {e}")

        # 3. Run Orchestration
        st.info("⏳ Running all agents...")
        with st.spinner("🧠 Reconciliation in progress..."):
            try:
                orchestrator = AgentOrchestrator(azure_config)
                output_file, logs = orchestrator.run_all(uploaded_file, sop_text)
                st.success("✅ Reconciliation completed.")
            except Exception as e:
                st.error("❌ Failed during agent execution.")
                st.exception(e)
                st.stop()

        # 4. Show Logs
        with st.expander("📝 Agent Logs", expanded=True):
            for log in logs:
                st.write(log)

        # 5. Download Output
        st.download_button(
            label="📥 Download Final Reconciliation Report",
            data=output_file,
            file_name="Final_Reconciliation_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
