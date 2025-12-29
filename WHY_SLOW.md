# ⚡ Why It Takes Time & How to Speed It Up

## The Answer: Be Patient First Time, Then It's Instant

**First Query:** ⏳ **2-3 minutes** (normal - downloads & processes documents)
**Second Query:** ⚡ **3-5 seconds** (cached - super fast!)

---

## Quick Start Options

### 🟢 Fastest: Demo Mode (Instant)

```bash
streamlit run demo_fast.py
```

✓ Pre-cached responses (no waiting)
✓ Perfect for UI testing
✓ Instant results

### 🟡 Fast: Speed Mode (3-5s after first load)

```bash
streamlit run app_lite.py
```

✓ No verification = faster
✓ 1st query: 90s | 2nd+ queries: 5s
✓ Good for real data but quick feedback

### 🟢 Full: Complete Features (Slow first time)

```bash
streamlit run app.py
```

✓ Full E-V-L verification
✓ 1st query: 2-3 min | 2nd+ queries: 20-30s
✓ Best accuracy & insights

---

## What Makes It Slow?

1. **Download SEC 10-K** (30-60s) - First time only ✓
2. **Create embeddings** (15-30s) - First time only ✓
3. **LLM response** (5-15s) - Every query
4. **E-V-L verification** (10-20s) - Every query (optional)

## The Solution: Caching

Everything is cached in memory after first load!

```
Load AAPL:    2 minutes (slow, downloads everything)
Query AAPL:   5 sec ✓ (cached!)
Query AAPL:   5 sec ✓ (cached!)
Query AAPL:   5 sec ✓ (cached!)
Load MSFT:    2 minutes (new company)
Query MSFT:   5 sec ✓ (cached!)
```

---

## Performance Timeline

| When    | Action                    | Time    | Status            |
| ------- | ------------------------- | ------- | ----------------- |
| 0s      | Start query AAPL          | -       | ⏳ Loading...     |
| 30s     | Download complete         | 30s     | 📥 Downloaded     |
| 50s     | Embeddings done           | 20s     | 🧠 Embedded       |
| 60s     | Documents indexed         | 10s     | 📑 Indexed        |
| 75s     | LLM response              | 15s     | 🤖 Generated      |
| 95s     | Verification complete     | 20s     | ✓ Verified        |
| **95s** | **TOTAL**                 | **95s** | **⏳ First load** |
| 3s      | Query AAPL again (cached) | 3s      | **⚡ Lightning**  |

---

## Run Commands

```bash
# Instant demo (pre-cached data)
streamlit run demo_fast.py

# Fast mode (no verification, 5s queries)
streamlit run app_lite.py

# Full features (with verification, 20-30s)
streamlit run app.py

# See performance breakdown
cat PERFORMANCE_GUIDE.md
```

---

## Pro Tips

✅ **Load same ticker twice** - 1st query slow, 2nd+ queries fast
✅ **Disable verification** - Saves 15-20 seconds per query
✅ **Use demo_fast.py first** - Understand the UI without waiting
✅ **Batch queries together** - 40% faster than sequential

---

## Expected Wait Times

| Scenario         | Wait    | Feeling          |
| ---------------- | ------- | ---------------- |
| First AAPL query | 90-150s | ⏳ Go get coffee |
| Next AAPL query  | 3-5s    | ⚡ Instant       |
| First MSFT query | 90-150s | ⏳ Grab lunch    |
| Next MSFT query  | 3-5s    | ⚡ Instant       |
| Demo mode        | 0.1s    | 🚀 Blazing       |

**Bottom line: First query waits. Everything after that is instant!** ⚡
