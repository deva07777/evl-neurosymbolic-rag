# FinChat Global — QUICK REFERENCE CARD

## 🚀 SETUP (Do This Once)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create config file
copy .env.example .env

# 3. Edit .env and add your Groq API key
#    GROQ_API_KEY=gsk_YOUR_KEY_HERE
#    (Get key from: https://console.groq.com)

# 4. Verify everything works
python verify_setup.py
```

---

## 💻 RUNNING (Pick One Option)

### Option A: See Examples (Best First Time)

```bash
python integration_example.py
```

Shows:

- Loading company data
- Making queries
- E-V-L verification in action
- Knowledge graph exploration
- Company comparison
- Batch processing

### Option B: Interactive Dashboard (Best for Exploration)

```bash
streamlit run app.py
```

Then open: http://localhost:8501

Features:

- Single company analysis
- Comparative analysis
- Query history
- Admin panel

### Option C: Run Tests (Best for Validation)

```bash
# Core RAG tests
python tests.py

# Neuro-symbolic verification tests
python neuro_symbolic_tests.py
```

### Option D: Use in Your Code (Best for Production)

```python
from financial_agent import UnifiedFinancialAgent

agent = UnifiedFinancialAgent()
agent.load_ticker("AAPL", market="US")
result = agent.query("AAPL", "What is revenue?")
print(result['answer'])
print(f"Confidence: {result['confidence_score']}")
```

---

## 🔧 CONFIGURATION

### Using Groq (Free, Fast) ← RECOMMENDED

```bash
LLM_PROVIDER=groq
LLM_MODEL=mixtral-8x7b-32768
GROQ_API_KEY=gsk_YOUR_KEY
```

### Using OpenAI (Paid, Higher Quality)

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk_YOUR_KEY
```

### Using Ollama (Local, Private)

```bash
LLM_PROVIDER=ollama
LLM_MODEL=mistral
# No API key needed (runs locally)
```

---

## 📊 WHAT EACH COMMAND DOES

| Command                          | What It Does                       | Time      |
| -------------------------------- | ---------------------------------- | --------- |
| `python verify_setup.py`         | Checks if everything is configured | <1 sec    |
| `python integration_example.py`  | Runs all demo workflows            | 30-60 sec |
| `streamlit run app.py`           | Launches interactive dashboard     | Instant   |
| `python tests.py`                | Runs core RAG tests                | 10-20 sec |
| `python neuro_symbolic_tests.py` | Tests verification framework       | 10-20 sec |

---

## 🎯 COMMON TASKS

### Task: Ask About a Company

```python
from financial_agent import UnifiedFinancialAgent

agent = UnifiedFinancialAgent()
agent.load_ticker("AAPL", market="US")
result = agent.query("AAPL", "What is the net income?")
print(result['answer'])
```

### Task: Compare Two Companies

```python
agent.compare_companies("AAPL", "MSFT", "revenue")
```

### Task: Get Financial Summary

```python
summary = agent.get_financial_summary("AAPL", market="US")
print(summary)
```

### Task: Batch Query Multiple Questions

```python
queries = [
    {"ticker": "AAPL", "question": "What is revenue?", "market": "US"},
    {"ticker": "MSFT", "question": "What is margin?", "market": "US"},
]
results = agent.batch_query(queries)
```

---

## 🐛 TROUBLESHOOTING

### Problem: Module not found

```bash
# Solution:
pip install -r requirements.txt
```

### Problem: "GROQ_API_KEY not found"

```bash
# Solution:
# 1. Open .env file
# 2. Find: GROQ_API_KEY=your_groq_key_here
# 3. Replace with: GROQ_API_KEY=gsk_YOUR_ACTUAL_KEY
# 4. Save file
```

### Problem: Port 8501 already in use

```bash
# Solution:
streamlit run app.py --server.port 8502
```

### Problem: Slow performance

```bash
# Use Groq instead (faster):
LLM_PROVIDER=groq
LLM_MODEL=mixtral-8x7b-32768
```

---

## 📚 FILES GUIDE

| File                             | Purpose                          |
| -------------------------------- | -------------------------------- |
| `HOW_TO_RUN.md`                  | Complete setup guide (READ THIS) |
| `verify_setup.py`                | Check if system is configured    |
| `integration_example.py`         | See all features in action       |
| `app.py`                         | Interactive dashboard            |
| `tests.py`                       | Unit tests                       |
| `financial_agent.py`             | Main API                         |
| `NEURO_SYMBOLIC_ARCHITECTURE.md` | Architecture details             |
| `QUICKSTART.md`                  | 5-minute start guide             |

---

## ✅ SUCCESS INDICATORS

- ✓ `verify_setup.py` shows all green checks
- ✓ `python integration_example.py` runs without errors
- ✓ `streamlit run app.py` opens dashboard
- ✓ Tests pass: `python tests.py`

---

## 🎉 YOU'RE READY!

**Start here:**

```bash
# 1. Verify setup
python verify_setup.py

# 2. See examples
python integration_example.py

# 3. Try dashboard
streamlit run app.py
```

**Questions?** Check `HOW_TO_RUN.md` for detailed guide!
