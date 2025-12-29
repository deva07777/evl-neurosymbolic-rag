"""FinChat Global — Beautiful Modern Financial RAG Dashboard."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from financial_agent import UnifiedFinancialAgent
from config import config
from utils import logger
from datetime import datetime

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="FinChat Global",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "FinChat Global — Neuro-Symbolic Financial RAG Agent"
    }
)

# ============================================================================
# CUSTOM STYLING - MODERN & BEAUTIFUL
# ============================================================================
st.markdown("""
<style>
    /* Global Styles */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
    }
    
    /* Main Container */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
        color: white;
    }
    
    /* Headers */
    h1 {
        color: #2d3748;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #2d3748;
        font-weight: 700;
        border-bottom: 3px solid #667eea;
        padding-bottom: 10px;
    }
    
    h3 {
        color: #4a5568;
        font-weight: 600;
    }
    
    /* Cards & Containers */
    .answer-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        font-size: 1.1rem;
        line-height: 1.8;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        border: none;
    }
    
    .source-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
        border-left: 5px solid #667eea;
        padding: 15px;
        margin: 12px 0;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        color: #667eea;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #718096;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.05rem;
        font-weight: 600;
        padding: 12px 24px;
        color: #4a5568;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #667eea;
        border-bottom: 3px solid #667eea;
    }
    
    /* Confidence Badges */
    .confidence-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 700;
        margin: 5px 5px 5px 0;
    }
    
    .confidence-high {
        background: #d1fae5;
        color: #065f46;
    }
    
    .confidence-medium {
        background: #fef3c7;
        color: #92400e;
    }
    
    .confidence-low {
        background: #fee2e2;
        color: #7f1d1d;
    }
    
    /* Verification Badges */
    .verification-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 5px 5px 5px 0;
    }
    
    .verification-pass {
        background: #d1fae5;
        color: #065f46;
    }
    
    .verification-fail {
        background: #fee2e2;
        color: #7f1d1d;
    }
    
    /* Sidebar Text */
    .sidebar-text {
        color: white;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR HEADER & NAVIGATION
# ============================================================================
st.sidebar.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='color: white; margin: 0; font-size: 1.8rem;'>📊 FinChat Global</h1>
    <p style='color: #cbd5e0; margin: 10px 0 0 0; font-size: 0.9rem;'>Neuro-Symbolic Financial Intelligence</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation",
    ["📈 Single Company Analysis", "🔄 Comparative Analysis", "📉 Analytics & Insights", "⚙️ Admin Panel"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class='sidebar-text'>
    <b>How it Works:</b>
    <ul>
        <li>Fetches SEC filings & financial reports</li>
        <li>Processes with AI embeddings</li>
        <li>Verifies with E-V-L agents</li>
        <li>Returns verified insights</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.info("💡 Tip: Use specific questions for better results!")

# ============================================================================
# INITIALIZE SESSION STATE & AGENT
# ============================================================================
if 'agent' not in st.session_state:
    st.session_state.agent = UnifiedFinancialAgent()

if 'query_history' not in st.session_state:
    st.session_state.query_history = []

agent = st.session_state.agent

# ============================================================================
# PAGE 1: SINGLE COMPANY ANALYSIS
# ============================================================================
if menu == "📈 Single Company Analysis":
    st.title("� Single Company Analysis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input("📌 Ticker Symbol", value="AAPL", placeholder="e.g., AAPL, MSFT")
    with col2:
        market = st.selectbox("🌍 Market", ["US", "IN"])
    with col3:
        st.write("")  # spacing
        st.write("")
    
    question = st.text_area(
        "❓ Your Question",
        value="Summarize revenue and margin trends.",
        placeholder="Ask about financial metrics, trends, risks...",
        height=100
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        run_query = st.button("🚀 Analyze", use_container_width=True)
    with col2:
        enable_verification = st.checkbox("Verify ✓", value=True)
    
    if run_query and ticker and question:
        with st.spinner("🔄 Loading financial data and analyzing..."):
            try:
                # Load ticker (with timeout notice)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📥 Downloading SEC filing (30-60s on first run)...")
                progress_bar.progress(10)
                
                load_status = agent.load_ticker(ticker, market)
                
                status_text.text("🧠 Creating embeddings (15-30s)...")
                progress_bar.progress(50)
                
                # Query with verification
                status_text.text("🔍 Searching documents...")
                progress_bar.progress(70)
                
                result = agent.query(ticker, question, market)
                
                status_text.text("✓ Complete!")
                progress_bar.progress(100)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Store in history
                st.session_state.query_history.append({
                    "ticker": ticker,
                    "question": question,
                    "timestamp": datetime.now()
                })
                
                # Display Results
                st.markdown("---")
                
                # Confidence & Verification
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    conf = result.get('confidence_score', 0)
                    if isinstance(conf, (int, float)):
                        st.metric("Confidence Score", f"{conf:.2f}", delta=f"{(conf-0.5)*100:.0f}%" if conf > 0.5 else None)
                        if conf >= 0.85:
                            st.markdown('<span class="confidence-badge confidence-high">✓ High Confidence</span>', unsafe_allow_html=True)
                        elif conf >= 0.65:
                            st.markdown('<span class="confidence-badge confidence-medium">⚠ Medium Confidence</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="confidence-badge confidence-low">✗ Low Confidence</span>', unsafe_allow_html=True)
                
                with col2:
                    verif = result.get('verification_details', {})
                    all_pass = verif.get('all_agents_pass', False)
                    st.metric("Verification", "✓ PASS" if all_pass else "⚠ CHECK", delta=None)
                
                with col3:
                    latency = result.get('latency_ms', 0)
                    st.metric("Response Time", f"{latency}ms", delta=None)
                
                # Answer
                st.markdown("### 💡 Answer")
                st.markdown(f"""
                <div class='answer-box'>
                    {result.get('answer', 'No answer generated')}
                </div>
                """, unsafe_allow_html=True)
                
                # Verification Details
                if enable_verification and result.get('verification_details'):
                    st.markdown("### ✓ Verification Details")
                    vd = result['verification_details']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**Agent E** (Earnings): {'✓ PASS' if 'EARNINGS_VALID' in vd.get('verification_summary', '') else '⚠ CHECK'}")
                    with col2:
                        st.markdown(f"**Agent V** (Validity): {'✓ PASS' if 'VALIDITY_PASS' in vd.get('verification_summary', '') else '⚠ CHECK'}")
                    with col3:
                        st.markdown(f"**Agent L** (Longevity): {'✓ PASS' if 'LONGEVITY_PASS' in vd.get('verification_summary', '') else '⚠ CHECK'}")
                    
                    st.info(vd.get('verification_summary', 'Verification completed'))
                
                # Sources
                st.markdown("### 📚 Sources")
                sources = result.get('source_documents', [])
                if sources:
                    for i, source in enumerate(sources[:3], 1):
                        st.markdown(f"""
                        <div class='source-box'>
                            <b>Source {i}:</b> {source[:150]}...
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No sources found")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.warning("""
                ⏱️ **Slow First Load?** This is normal!
                - First query: 2-3 minutes (downloading + embedding)
                - Subsequent queries: 3-5 seconds (cached)
                
                **Quick Demo:** Try `demo_fast.py` for instant results!
                """)
                logger.exception("Query failed")

# ============================================================================
# PAGE 2: COMPARATIVE ANALYSIS
# ============================================================================
elif menu == "🔄 Comparative Analysis":
    st.title("🔄 Comparative Analysis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker1 = st.text_input("First Company", value="AAPL")
    with col2:
        ticker2 = st.text_input("Second Company", value="MSFT")
    with col3:
        metric = st.text_input("Metric to Compare", value="revenue")
    
    if st.button("📊 Compare", use_container_width=True):
        with st.spinner("Comparing companies..."):
            try:
                result = agent.compare_companies(ticker1, ticker2, metric)
                st.success("✓ Comparison Complete")
                st.info(result)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 3: ANALYTICS & INSIGHTS
# ============================================================================
elif menu == "📉 Analytics & Insights":
    st.title("📉 Analytics & Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Query History")
        if st.session_state.query_history:
            for i, q in enumerate(st.session_state.query_history[-10:], 1):
                st.write(f"{i}. **{q['ticker']}**: {q['question'][:50]}...")
        else:
            st.info("No queries yet. Start by analyzing a company!")
    
    with col2:
        st.markdown("### ⚡ Quick Stats")
        st.metric("Queries Run", len(st.session_state.query_history))
        st.metric("Companies Loaded", len(agent.vectorstores))

# ============================================================================
# PAGE 4: ADMIN PANEL
# ============================================================================
elif menu == "⚙️ Admin Panel":
    st.title("⚙️ Admin Panel")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 Loaded Companies")
        companies = list(agent.vectorstores.keys())
        if companies:
            for company in companies:
                st.write(f"✓ {company}")
        else:
            st.info("No companies loaded yet")
    
    with col2:
        st.markdown("### 🗑️ Cache Management")
        if st.button("Clear All Cache", use_container_width=True):
            agent.cache.clear()
            agent.vectorstores.clear()
            agent.documents.clear()
            st.success("✓ Cache cleared!")
    
    st.markdown("---")
    st.markdown("### 📊 System Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cached Companies", len(agent.vectorstores))
    with col2:
        st.metric("Cache Items", len(agent.cache))
    with col3:
        st.metric("Documents Loaded", len(agent.documents))

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #718096; font-size: 0.9rem;'>
    <p>FinChat Global © 2025 | Powered by Groq + Neuro-Symbolic Intelligence</p>
    <p>Dual-Market Financial Analysis for US (SEC) & India (MCA)</p>
</div>
""", unsafe_allow_html=True)
