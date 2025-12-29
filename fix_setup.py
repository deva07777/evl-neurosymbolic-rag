"""Quick workaround - bypass embedding requirement temporarily."""
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="FinChat - Quick Workaround", layout="wide")

st.title("⚠️ Setup Issue - Temporary Workaround")

st.warning("""
**Problem:** sentence-transformers installation failed
**Impact:** Can't create embeddings (hangs indefinitely)
**Solution:** Install manually or use cached data

Choose one of the following:
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Option 1: Install Properly ✓")
    st.code("""
# Stop the app (Ctrl+C)

# Install sentence-transformers manually
pip install sentence-transformers --upgrade

# Then restart
streamlit run app.py
    """, language="bash")
    
    if st.button("Try again after installing ↻"):
        st.success("Restart the app after installing!")

with col2:
    st.subheader("Option 2: Use Demo (No Wait) ⚡")
    st.code("""
# In a new terminal:
streamlit run demo_fast.py

# Instant results, no dependencies needed!
    """, language="bash")
    
    if st.button("Go to demo →"):
        st.markdown("[Click here to open demo_fast.py](http://localhost:8501?page=demo_fast)")

st.markdown("---")

st.info("""
**What went wrong?**
- Python environment has multiple versions installed
- Streamlit running in Python 3.11, but package installed in different version
- Or: Installation didn't complete properly

**Fix:**
```bash
# Option A: Force reinstall with specific Python
python -m pip install --upgrade --force-reinstall sentence-transformers

# Option B: Use faster demo (no embedding needed)
streamlit run demo_fast.py

# Option C: Skip embedding and use mock data
python integration_example.py
```
""")

st.error("""
**DO NOT WAIT** - The app will hang indefinitely if sentence-transformers is missing.

**Kill the app:** Press Ctrl+C in terminal
**Then choose one solution above**
""")
