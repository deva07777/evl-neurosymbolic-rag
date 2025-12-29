# 🚀 HOW TO RUN FINCHAT GLOBAL — Complete Setup Guide

## ⚡ QUICK START (5 Minutes)

### Step 1: Install Dependencies

```bash
cd d:\Rag
pip install -r requirements.txt
```

**What it installs:**

- sentence-transformers (for embeddings)
- faiss-cpu (for vector search)
- streamlit (for dashboard)
- beautifulsoup4 + lxml (for web scraping)
- pdfplumber + PyPDF2 (for PDF parsing)
- networkx (for knowledge graphs)
- All other dependencies

**Time:** 2-5 minutes (depending on internet speed)

---

### Step 2: Create Your `.env` File

```bash
copy .env.example .env
```

**This creates `.env` with Groq pre-configured:**

```
LLM_PROVIDER=groq
LLM_MODEL=mixtral-8x7b-32768
LLM_TEMPERATURE=0.0
```

---

### Step 3: Add Your Groq API Key

**Option A: If you have a Groq API Key**

1. Open `d:\Rag\.env` in a text editor
2. Find this line:
   ```
   GROQ_API_KEY=
   ```
3. Add your API key (from https://console.groq.com):
   ```
   GROQ_API_KEY=gsk_YOUR_ACTUAL_KEY_HERE
   ```
4. Save the file

**Option B: Without API Key (Limited Testing)**

- The system will work but may be slow
- Good for testing the architecture only

---

### Step 4: Verify Installation

```bash
python -c "from financial_agent import UnifiedFinancialAgent; print('✅ System Ready!')"
```

You should see: `✅ System Ready!`

---

## 🎯 RUNNING THE SYSTEM

### Option 1: Run Integration Examples (Recommended First)

```bash
python integration_example.py
```

**What it does:**

1. Creates a financial agent
2. Loads Apple (AAPL) data
3. Runs queries with E-V-L verification
4. Shows knowledge graph
5. Compares companies
6. Demonstrates batch processing

**Expected Output:**

```
[1] Loading AAPL ticker and building knowledge graph...
    Status: loaded
    Documents: 45

[2] Asking question about Apple...
    Question: What was Apple's total revenue?

[3] Running query with E-V-L verification...
    Answer: Apple's revenue was...
    Confidence: 0.92

    Agent E (Earnings): PASS
    Agent V (Validity): PASS
    Agent L (Longevity): PASS
```

---

### Option 2: Launch Interactive Dashboard

```bash
streamlit run app.py
```

**Then:**

1. Opens automatically at: http://localhost:8501
2. Choose page from sidebar:
   - **Single Company**: Ask questions about one ticker
   - **Comparative Analysis**: Compare two companies
   - **Analytics**: View query history
   - **Admin**: Manage caches

**Features:**

- Real-time answer generation
- Source visualization
- Confidence scoring
- Knowledge graph display

---

### Option 3: Run Unit Tests

```bash
python tests.py
```

**Tests the RAG core:**

- Document processing ✓
- Chunking ✓
- Embeddings ✓
- Basic functionality ✓

Expected: 14+ tests passing

---

### Option 4: Run Neuro-Symbolic Tests

```bash
python neuro_symbolic_tests.py
```

**Tests the verification framework:**

- Knowledge graph ✓
- Agent E (Earnings) ✓
- Agent V (Validity) ✓
- Agent L (Longevity) ✓
- End-to-end verification ✓

Expected: 14+ tests passing

---

## 💻 PYTHON SCRIPT EXAMPLES

### Example 1: Simple Query

```python
from financial_agent import UnifiedFinancialAgent

# Create agent
agent = UnifiedFinancialAgent()

# Load a company
print("Loading AAPL...")
agent.load_ticker("AAPL", market="US")

# Ask a question
result = agent.query("AAPL", "What is the revenue?")

# Display results
print("\n" + "="*70)
print("ANSWER:")
print(result['answer'])
print("\nCONFIDENCE:", result['confidence_score'])
print("\nVERIFICATION:")
print(result['verification_details'])
print("="*70)
```

### Example 2: Compare Companies

```python
from financial_agent import UnifiedFinancialAgent

agent = UnifiedFinancialAgent()
result = agent.compare_companies("AAPL", "MSFT", "revenue")
print(result)
```

### Example 3: Batch Processing

```python
from financial_agent import UnifiedFinancialAgent

agent = UnifiedFinancialAgent()

queries = [
    {"ticker": "AAPL", "question": "What is revenue?", "market": "US"},
    {"ticker": "MSFT", "question": "What is net income?", "market": "US"},
]

results = agent.batch_query(queries)
for r in results:
    print(f"Answer: {r['answer']}")
```

Save these as `.py` files and run:

```bash
python my_script.py
```

---

## 🔍 COMMON ISSUES & FIXES

### Issue 1: "Module not found" Error

```
ModuleNotFoundError: No module named 'sentence_transformers'
```

**Fix:**

```bash
pip install sentence-transformers
pip install faiss-cpu
pip install streamlit
```

---

### Issue 2: "GROQ_API_KEY not found"

```
Error: GROQ_API_KEY not provided
```

**Fix:**

1. Get key from https://console.groq.com
2. Open `.env` file
3. Add: `GROQ_API_KEY=gsk_YOUR_KEY`
4. Save file

---

### Issue 3: Port 8501 Already in Use (Streamlit)

```
StreamlitAppException: Port 8501 is already in use
```

**Fix:**

```bash
streamlit run app.py --server.port 8502
```

---

### Issue 4: "pdfplumber not installed"

```
Warning: pdfplumber not available
```

**Fix:**

```bash
pip install pdfplumber PyPDF2
```

---

## 📊 COMPLETE EXECUTION FLOW

```
START
  ↓
[1] Install Dependencies
    pip install -r requirements.txt
  ↓
[2] Create .env File
    copy .env.example .env
    (Edit to add GROQ_API_KEY)
  ↓
[3] Verify Installation
    python -c "from financial_agent import UnifiedFinancialAgent; print('OK')"
  ↓
[4] Choose How to Run:
    ├─ python integration_example.py     (see demos)
    ├─ streamlit run app.py              (interactive dashboard)
    ├─ python tests.py                   (run tests)
    └─ python my_script.py               (custom script)
  ↓
END - View Results!
```

---

## 🎯 RECOMMENDED SEQUENCE FOR FIRST TIME

### Day 1: Verify Everything Works

```bash
# Step 1: Install
pip install -r requirements.txt

# Step 2: Configure
copy .env.example .env
# Edit .env and add your Groq API key

# Step 3: Verify
python -c "from financial_agent import UnifiedFinancialAgent; print('✅ Ready!')"

# Step 4: Run tests
python tests.py
```

### Day 2: See It In Action

```bash
# Run integration examples
python integration_example.py

# Or launch dashboard
streamlit run app.py
```

### Day 3: Build Custom Solutions

```python
# Use in your own Python scripts
from financial_agent import UnifiedFinancialAgent

agent = UnifiedFinancialAgent()
agent.load_ticker("YOUR_TICKER", market="US")
result = agent.query("YOUR_TICKER", "Your question")
```

---

## 📚 FILE LOCATIONS

| File                      | Purpose               | Run Command                      |
| ------------------------- | --------------------- | -------------------------------- |
| `integration_example.py`  | See all features      | `python integration_example.py`  |
| `app.py`                  | Interactive dashboard | `streamlit run app.py`           |
| `tests.py`                | Core tests            | `python tests.py`                |
| `neuro_symbolic_tests.py` | Verification tests    | `python neuro_symbolic_tests.py` |
| `financial_agent.py`      | Main API              | Import in your script            |

---

## ✅ SUCCESS CHECKLIST

- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file created: `copy .env.example .env`
- [ ] Groq API key added to `.env`
- [ ] System verified: `python -c "from financial_agent import ..."`
- [ ] Tests passing: `python tests.py`
- [ ] Examples run: `python integration_example.py`
- [ ] Dashboard works: `streamlit run app.py`

---

## 🚀 YOU'RE READY!

Just run one of these commands:

```bash
# Option 1: See live examples
python integration_example.py

# Option 2: Use interactive dashboard
streamlit run app.py

# Option 3: Run all tests
python tests.py && python neuro_symbolic_tests.py
```

---

## 💬 WHAT TO DO NEXT

1. **Read Documentation**: Open `QUICKSTART.md`
2. **Understand Architecture**: Read `NEURO_SYMBOLIC_ARCHITECTURE.md`
3. **Explore Code**: Check `integration_example.py` for usage patterns
4. **Build Your Own**: Use the API in your scripts

---

**Questions?** Check the inline docstrings in the `.py` files or read the documentation files! 🎉
