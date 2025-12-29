"""Lightweight version - disables verification for speed."""
import streamlit as st
from financial_agent import UnifiedFinancialAgent
from datetime import datetime

st.set_page_config(page_title="FinChat Global - Speed Mode", layout="wide", page_icon="⚡")

# Custom CSS
st.markdown("""
<style>
    .fast-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
if 'agent' not in st.session_state:
    st.session_state.agent = UnifiedFinancialAgent()

agent = st.session_state.agent

# Header
st.title("⚡ FinChat Global - Speed Mode")
st.markdown("Fast queries without E-V-L verification (3-5 seconds per query)")
st.markdown('<span class="fast-badge">⚡ Verification: OFF (for speed)</span>', unsafe_allow_html=True)

# Input
col1, col2 = st.columns(2)
with col1:
    ticker = st.text_input("📌 Ticker", value="AAPL")
with col2:
    market = st.selectbox("🌍 Market", ["US", "IN"])

question = st.text_area("❓ Question", value="What is the revenue trend?", height=80)

# Query
if st.button("⚡ Quick Query (No Verification)", use_container_width=True):
    if not ticker or not question:
        st.error("Enter ticker and question!")
    else:
        with st.spinner("Searching... (should be 3-10 seconds)"):
            try:
                # Load (cached if already loaded)
                agent.load_ticker(ticker, market)
                
                # Query WITHOUT verification (fast!)
                result = agent.query(ticker, question, market)
                
                if result:
                    st.success("✓ Done!")
                    
                    # Show metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        conf = result.get('confidence_score', 0)
                        st.metric("Confidence", f"{conf:.2f}" if isinstance(conf, (int, float)) else "N/A")
                    with col2:
                        latency = result.get('latency_ms', 0)
                        st.metric("Speed", f"{latency}ms")
                    
                    # Answer
                    st.markdown("### 💡 Answer")
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px;'>
                        {result.get('answer', 'No answer')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Sources
                    st.markdown("### 📚 Sources")
                    for i, src in enumerate(result.get('source_documents', [])[:2], 1):
                        st.write(f"**{i}.** {str(src)[:100]}...")
                else:
                    st.error("No result returned")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.info("""
**Speed Tips:**
- First AAPL query: ~90s (downloads + embeds)
- All other AAPL queries: ~5s (cached!)
- Missing verification? Use main app.py for full features
- Want demo data? Try demo_fast.py
""")
