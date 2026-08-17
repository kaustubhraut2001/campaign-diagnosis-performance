import os
import sys
import json
import streamlit as st
import pandas as pd

# Add code directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.graph import CampaignDiagnosticGraph
from src.data_cleaner import DataCleaner

# Page Configuration
st.set_page_config(
    page_title="Campaign Performance Diagnostic Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Theme & Glassmorphism Aesthetics)
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stApp {
        background-color: #0f172a;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
    }
    .badge-answerable {
        background-color: #065f46;
        color: #34d399;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-ambiguous {
        background-color: #92400e;
        color: #fbbf24;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-unanswerable {
        background-color: #991b1b;
        color: #f87171;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Sample Questions List
SAMPLE_QUESTIONS = [
    "1. What was total spend and total conversions last month?",
    "2. Why did CPA go up in June?",
    "3. Which creative has the best ROAS on mobile in Tier 1 cities?",
    "4. Is CMP-1006 pacing correctly against its daily budget?",
    "5. Which city has the worst cost per conversion, and by how much?",
    "6. Compare Meta and Google Search on CPA over the full period.",
    "7. What happened to CMP-1006 in the middle of June?",
    "8. Show me the CTR trend for CRE-2002 week by week.",
    "9. Which age group converts best on Connected TV?",
    "10. What is our average order value by channel?",
    "11. How did last week compare to the week before?",
    "12. Why is Tier 3 mobile traffic on CMP-1004 performing so badly?",
    "13. What is the customer lifetime value of people acquired through YouTube?",
    "14. Should we increase budget on CMP-1003?",
    "15. Which campaign is closest to hitting a 4x ROAS target?"
]

# Title Header
st.title("📊 Campaign Performance Diagnostic Engine")
st.markdown("*Multi-Agent Graph System for Calculated Performance Analysis & Auditability*")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Data & Engine Controls")
    
    # Load dataset hygiene summary
    @st.cache_data
    def load_dataset_info():
        cleaner = DataCleaner()
        df, report = cleaner.load_and_clean()
        return df, report

    try:
        cleaned_df, report = load_dataset_info()
        st.success("✅ Dataset Loaded & Cleaned")
        st.markdown(f"**Rows:** {report['final_rows']:,} (from {report['initial_rows']:,})")
        st.markdown(f"**Date Range:** {report['date_range']}")
        st.markdown(f"**Duplicates Removed:** {report['duplicates_removed']}")
        st.markdown(f"**Channels Cleaned:** {len(report['channels_unified'])}")
    except Exception as e:
        st.error(f"Failed to load dataset: {str(e)}")

    st.markdown("---")
    st.header("❓ Sample Questions")
    selected_sample = st.selectbox(
        "Choose an Account Manager Question Preset:",
        ["-- Select Question --"] + SAMPLE_QUESTIONS
    )

    # Architecture Overview Expander
    arch_img_path = os.path.join(os.path.dirname(__file__), "assets", "agent_architecture.jpg")
    if os.path.exists(arch_img_path):
        with st.expander("🧩 View Multi-Agent Architecture", expanded=False):
            st.image(arch_img_path, caption="Multi-Agent State Graph Architecture", use_container_width=True)

# Main Input Form
col1, col2 = st.columns([4, 1])

with col1:
    default_q = "" if selected_sample == "-- Select Question --" else selected_sample
    user_question = st.text_input(
        "Enter your campaign diagnostic question in plain English:",
        value=default_q,
        placeholder="e.g. Why did CPA go up in June?"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Run Diagnostic", type="primary", use_container_width=True)

if run_btn or (selected_sample != "-- Select Question --" and user_question):
    if not user_question.strip():
        st.warning("Please enter a question or select a preset.")
    else:
        with st.spinner("Running Multi-Node Graph Diagnostic..."):
            graph = CampaignDiagnosticGraph()
            state = graph.run(user_question)

        # Status & Classification Badge
        q_type = state.get("question_type", "answerable")
        st.markdown("### 📋 Diagnostic Status")
        
        if q_type == "answerable":
            st.markdown('<span class="badge-answerable">✅ ANSWERABLE FROM DATA</span>', unsafe_allow_html=True)
        elif q_type == "ambiguous":
            st.markdown('<span class="badge-ambiguous">⚠️ AMBIGUOUS QUESTION - CLARIFICATION REQUIRED</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-unanswerable">⛔ UNANSWERABLE - MISSING DATA SCHEMA</span>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Diagnostic Answer & Output
        st.markdown(state["final_answer"])

        # Display Generated Chart if present
        chart_path = state.get("chart_path")
        if chart_path and os.path.exists(chart_path):
            st.markdown("### 📈 Visual Comparison / Trend Chart")
            st.image(chart_path, caption=state.get("chart_title", "Diagnostic Visualization"), use_container_width=True)

        # Code Audit Expander
        audit_trail = state.get("audit_trail", [])
        if audit_trail:
            with st.expander("🔍 Calculation Code Audit (User Verification)", expanded=False):
                st.markdown("The following Python Pandas code was generated by the **Planner** and executed safely by the **Query Executor Worker** over the cleaned dataset:")
                st.code(audit_trail[-1]["code"], language="python")
                st.markdown("**Execution Output:**")
                st.text(audit_trail[-1].get("output", "No console output recorded."))

        # Graph Execution Trace Log Expander
        trace = state.get("execution_trace", [])
        if trace:
            with st.expander("🌐 Graph Execution Trace Log", expanded=False):
                st.markdown("Step-by-step state trajectory across Graph Nodes:")
                trace_df = pd.DataFrame(trace)
                st.dataframe(trace_df, use_container_width=True)
