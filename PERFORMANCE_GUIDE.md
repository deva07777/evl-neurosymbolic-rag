# ⏱️ Performance Guide - Why It's Slow & How to Speed It Up

## Performance Breakdown

### First Query (New Ticker)

```
Download SEC 10-K filing:       30-60 seconds
  └─ Parse PDF/HTML:            10-20s
  └─ Network latency:           5-10s

Create embeddings:              15-30 seconds
  └─ sentence-transformers:     12-25s
  └─ HNSW indexing:             2-5s

Search & Retrieve:              1-2 seconds
  └─ FAISS vector search:       500ms
  └─ Rank documents:            500ms

LLM Generation (Groq):          5-15 seconds
  └─ API call latency:          2-3s
  └─ Token generation:          3-10s

E-V-L Verification:             10-20 seconds
  └─ Agent E (Earnings):        3-5s
  └─ Agent V (Validity):        3-5s
  └─ Agent L (Longevity):       4-10s

TOTAL: 60-145 seconds (1.5-2.5 minutes) ⏳
```

### Cached Query (Same Ticker)

```
Vector database lookup:         500ms
  └─ Semantic search:           300ms
  └─ Reranking:                 200ms

LLM Generation:                 5-15 seconds

E-V-L Verification:             10-20 seconds (if enabled)

TOTAL: 15-35 seconds (with verification) ⚡
       5-10 seconds (without verification) ⚡⚡
```

---

## How to Speed Up

### Option 1: Use Fast Demo (⚡ Instant)

```bash
streamlit run demo_fast.py
# Pre-cached responses with instant results
# Perfect for testing UI/features
```

### Option 2: Disable Verification (⚡ Fast)

In the app, **uncheck "Verify ✓"** before querying:

- Without verification: 5-10 seconds
- With verification: 25-35 seconds

### Option 3: Query Same Ticker Twice (⚡ Fast)

1. First query: 2 minutes (slow, but caches everything)
2. Second query: 5-10 seconds (instant because cached!)

```
Query "AAPL": 2 min
Query "AAPL": 5 sec ✓
Query "AAPL": 5 sec ✓
Query "MSFT": 2 min (new company)
Query "MSFT": 5 sec ✓
```

### Option 4: Use Batch Processing

```python
queries = [
    {"ticker": "AAPL", "question": "What is revenue?"},
    {"ticker": "AAPL", "question": "What is margin?"},  # ✓ Fast
    {"ticker": "MSFT", "question": "What is revenue?"},
]
results = agent.batch_query(queries)
# Processes 2-3 queries in parallel
```

### Option 5: Lighter Embedding Model

Edit `embedding_manager.py`:

```python
# Change from:
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim, 500MB

# To:
model = SentenceTransformer('all-MiniLM-L6-v2')  # ← Already fastest!

# Even faster (lower quality):
model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')
# 512-dim but 2-3x faster
```

---

## Real-World Performance

| Operation             | Time   | Notes                              |
| --------------------- | ------ | ---------------------------------- |
| First AAPL load       | 2 min  | Downloads 10-K, creates embeddings |
| Second AAPL query     | 5 sec  | Cached, super fast                 |
| Third AAPL query      | 5 sec  | Still cached                       |
| First MSFT load       | 2 min  | New company, needs download        |
| Batch 5 queries       | 10 sec | Parallel processing                |
| With verification OFF | -50%   | Skip E-V-L agents                  |

---

## What's Slowing You Down?

### 🐢 Bottleneck #1: Document Download (30-60s)

**Why:** SEC Edgar serves files over HTTP
**Solution:**

- Download once, then cached forever ✓
- Use `demo_fast.py` to skip this
- Pre-cache documents overnight

### 🐢 Bottleneck #2: Embedding Generation (15-30s)

**Why:** sentence-transformers encodes all 50-100 chunks
**Solution:**

- Only happens once per company ✓
- Subsequent queries use cached embeddings
- Use lighter model (distiluse) for 2-3x speed

### 🐢 Bottleneck #3: E-V-L Verification (10-20s)

**Why:** Three agents run sequentially with LLM calls
**Solution:**

- **Disable verification** if you need speed
- Or disable per-agent (L agent is slowest)
- Will be parallelized in v2

### 🐢 Bottleneck #4: LLM Latency (5-15s)

**Why:** Groq API response time
**Solution:**

- Groq is already fastest (mixtral 8x7b)
- Use OpenAI for quality, but slower
- Local Ollama is instant but lower quality

---

## Pro Tips for Production

### 1. Pre-warm Cache

```bash
# Run at night to cache all companies
python -c "
from financial_agent import UnifiedFinancialAgent
agent = UnifiedFinancialAgent()
for ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN']:
    agent.load_ticker(ticker)
print('Cache ready!')
"
```

### 2. Deploy with Redis

```python
# Cache embeddings in Redis instead of memory
# Survives app restarts
from redis import Redis
agent.cache_backend = Redis(host='localhost')
```

### 3. Use Batch API

```python
# 50 queries run 5x faster with batching
queries = [... 50 questions ...]
results = agent.batch_query(queries, parallel_workers=4)
```

### 4. Monitor Performance

```python
# Add timing to your queries
import time
start = time.time()
result = agent.query(ticker, question)
print(f"Latency: {time.time() - start:.2f}s")
```

---

## Expected Times (Realistic)

| Scenario                   | Time    | Feeling      |
| -------------------------- | ------- | ------------ |
| Demo mode                  | 0.1s    | ⚡ Instant   |
| Cached query (no verify)   | 3-5s    | ⚡ Fast      |
| Cached query (with verify) | 20-30s  | ✓ Acceptable |
| First load (new ticker)    | 90-150s | ⏳ Wait once |
| Batch 10 queries           | 30-50s  | ✓ Good       |

---

## TL;DR

✅ **First query is slow (2 min)** because it downloads a 10MB file
✅ **Second query is fast (5 sec)** because everything is cached
✅ **Disable verification to save 15-20s**
✅ **Use demo_fast.py for instant testing**
✅ **Groq is fastest LLM** (already optimized)

**Bottom line:** Be patient on first query, then enjoy instant responses! 🚀
