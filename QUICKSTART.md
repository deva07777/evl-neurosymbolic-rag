# Quick Start Guide — FinChat Global Neuro-Symbolic RAG

## 🚀 Get Running in 5 Minutes

### Step 1: Install Dependencies

```bash
cd d:\Rag
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy template
copy .env.example .env

# Edit .env with your API keys
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_key_here
```

### Step 3: Run Interactive Example

```bash
python integration_example.py
```

This will demonstrate:

- ✅ Loading a company (AAPL)
- ✅ Building knowledge graph
- ✅ Querying with E-V-L verification
- ✅ Comparing companies
- ✅ Batch processing

### Step 4: Launch Dashboard

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

### Step 5: Run Tests

```bash
python tests.py                    # Core RAG tests
python neuro_symbolic_tests.py     # Neuro-symbolic tests
```

---

## 💡 Code Examples

### Example 1: Simple Query

```python
from financial_agent import UnifiedFinancialAgent

agent = UnifiedFinancialAgent()
agent.load_ticker("AAPL", market="US")

result = agent.query("AAPL", "What is Apple's revenue?")
print(result['answer'])
print(f"Confidence: {result['confidence_score']}")
print(result['verification_details'])
```

### Example 2: Company Comparison

```python
result = agent.compare_companies("AAPL", "MSFT", "revenue")
print(result)
```

### Example 3: Knowledge Graph Exploration

```python
# Access the knowledge graph
kg = agent.knowledge_graphs.get("US::AAPL")
if kg:
    peers = kg.get_peers("AAPL")
    print(f"Competitors: {peers}")

    metrics = kg.get_metrics("AAPL")
    print(f"Historical revenue: {metrics.get('revenue', {})}")
```

### Example 4: Batch Processing

```python
queries = [
    {"ticker": "AAPL", "question": "What is the revenue?", "market": "US"},
    {"ticker": "MSFT", "question": "What is net income?", "market": "US"},
    {"ticker": "TCS", "question": "What is the market cap?", "market": "IN"},
]
results = agent.batch_query(queries)
for r in results:
    print(f"Q: {r.get('question')}\nA: {r.get('answer')}\n")
```

---

## 🔍 Understanding Verification

### Confidence Score Breakdown

**0.95+** = All agents pass ✅

- Earnings verified
- Claims supported
- Trends consistent

**0.75-0.94** = One agent flags concern ⚠️

- Possible anomaly detected
- Trend break found
- Minor unsupported claims

**<0.75** = Multiple failures 🚨

- Numerical mismatch
- Trend anomaly + unsupported claims
- High hallucination risk

### Example Output

```json
{
  "answer": "Apple's revenue was $383.29 billion...",
  "confidence_score": 0.92,
  "verification_details": {
    "agent_e": {
      "status": "PASS",
      "details": "Earnings claim verified: $383.29B confirmed"
    },
    "agent_v": {
      "status": "PASS",
      "details": "All factual claims supported by 2 sources"
    },
    "agent_l": {
      "status": "FAIL",
      "details": "ANOMALY: $383B is 2.5% growth, but historical avg is 5%",
      "confidence_penalty": 0.03
    }
  }
}
```

---

## 📊 Project Structure

```
d:\Rag\
├── Core RAG (document_fetcher.py, embedding_manager.py, rag_engine.py)
├── Neuro-Symbolic (knowledge_graph.py, verification_agents.py)
├── Agent (financial_agent.py)
├── UI (app.py)
├── Tests (tests.py, neuro_symbolic_tests.py)
├── Config (config.py, .env.example)
└── Docs (README.md, NEURO_SYMBOLIC_ARCHITECTURE.md, COMPLETION_SUMMARY.md)
```

---

## ⚙️ Configuration Options

Edit `config.py` or `.env`:

```bash
# LLM Settings
LLM_PROVIDER=openai                 # or groq, ollama
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.0                 # Deterministic for finance
LLM_MAX_TOKENS=1024

# Chunking
CHUNK_SIZE=1200                     # Characters per chunk
CHUNK_OVERLAP=250                   # Overlap for context

# Search
SIMILARITY_THRESHOLD=0.6            # Min relevance score

# Paths
DATA_DIR=./data                     # Cache directory
VECTOR_DB_DIR=./vector_db           # Index directory

# Optional
REDIS_URL=redis://localhost:6379    # For production caching
RATE_LIMIT_PER_MIN=60              # API rate limit
```

---

## 🐛 Troubleshooting

### Issue: "sentence-transformers not available"

```bash
pip install sentence-transformers
```

### Issue: "secedgar not available"

```bash
pip install sec-edgar-downloader
```

### Issue: OpenAI API errors

- Check `OPENAI_API_KEY` in `.env`
- Verify API key has correct permissions
- Check rate limits

### Issue: PDF parsing fails

```bash
pip install pdfplumber PyPDF2
```

---

## 📈 Performance Tips

1. **Cache First Query**: First load takes 5-10 seconds. Subsequent queries use cache (<100ms).
2. **Batch Processing**: Process 10+ queries in parallel with `batch_query()`.
3. **Switch to Groq**: For faster responses, use `LLM_PROVIDER=groq` (free, fast).
4. **Use Local Ollama**: For privacy, run `ollama run mistral` and use `LLM_PROVIDER=ollama`.

---

## 📚 Documentation

- **README.md** — Setup & overview
- **NEURO_SYMBOLIC_ARCHITECTURE.md** — Full architecture specification
- **COMPLETION_SUMMARY.md** — Feature checklist
- **integration_example.py** — Code examples
- **config.py** — All configuration options

---

## ✅ What You Get

- ✅ Production-grade RAG system
- ✅ Neuro-symbolic verification
- ✅ Hallucination detection
- ✅ Multi-market support (US + India)
- ✅ Streamlit dashboard
- ✅ Full test coverage
- ✅ Comprehensive documentation

---

Ready? Run: `python integration_example.py` 🚀
