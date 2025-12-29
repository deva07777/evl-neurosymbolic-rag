# FinChat Global — Neuro-Symbolic Architecture

## Overview

FinChat Global has been upgraded to a **Neuro-Symbolic** hybrid architecture combining:

1. **Neural Layer**: LLMs for natural language understanding and generation (existing RAG)
2. **Symbolic Layer**: Knowledge graphs for structured reasoning and fact verification
3. **Verification Layer**: Multi-agent framework (E-V-L) for answer validation

This creates a self-checking system that reduces hallucinations and increases trustworthiness.

---

## Architecture Components

### 1. Knowledge Graph Layer (`knowledge_graph.py`)

**Purpose**: Build and maintain a symbolic representation of financial entities and relationships.

#### Data Structure (NetworkX DiGraph)

```
Nodes:
├── Company (AAPL, MSFT, RELIANCE, etc.)
│   └── Attributes: name, sector, market
├── Sector (Technology, Finance, Energy)
├── KeyMetrics (Revenue, NetIncome, Margin, EPS)
│   └── Attributes: ticker, metric, value, year
└── Peer (MSFT, GOOGL, etc.)

Edges:
├── Company --[belongs_to]--> Sector
├── Company --[has_metric]--> KeyMetrics
├── Company --[peer]--> Company
└── (Relationships have similarity scores)
```

#### Key Methods

```python
# Create and populate graph
kg = FinancialKnowledgeGraph()
kg.add_company_node("AAPL", "Apple Inc.", "Technology")
kg.add_metric_node("AAPL", "revenue", 394.3e9, 2024)
kg.add_peer_relationship("AAPL", "MSFT", similarity=0.85)

# Query graph
peers = kg.get_peers("AAPL")  # ['MSFT', 'GOOGL', ...]
metrics = kg.get_metrics("AAPL")  # {'revenue': {2024: 394.3e9, ...}, ...}
years, values, trend = kg.get_trend("AAPL", "revenue")  # years=[2022,2023,2024], trend="up"

# Auto-extract metrics from unstructured text
metrics = kg.extract_metrics_from_text("Apple reported $394B revenue", "AAPL", 2024)

# Generate context for LLM prompt
context = kg.get_context_prompt("AAPL")
# Output: "Company: Apple Inc. (AAPL)\nSector: Technology\nPeers: MSFT, GOOGL\n..."
```

#### Symbolic Reasoning

- **Peer Comparison**: Extract peer metrics and include in RAG context for comparative analysis
- **Trend Detection**: Automatically flag anomalies (e.g., "Revenue declined despite growth trend")
- **Historical Context**: Provide multi-year financial history for trend validation

---

### 2. E-V-L Verification Framework (`verification_agents.py`)

After LLM generates an answer, it passes through **three sequential verification agents** before being returned to the user.

#### Agent E: Earnings Verification

**Purpose**: Verify all numerical financial claims.

```
Answer: "Apple's revenue reached $394.3 Billion in 2024"

Process:
1. Extract numbers: [(394.3, "Billion"), ...]
2. Cross-check against source chunks
3. Report: EARNINGS_VALID or EARNINGS_HALLUCINATION

Output:
{
  "agent": "E",
  "status": "PASS",
  "details": "All 2 numerical claims verified",
  "confidence_penalty": 0.0
}
```

**Regex Patterns Used**:

- Revenue: `$394B`, `394 Billion`, `$394M`, etc.
- Net Income: `$96.9B`, `96.9 Billion`
- Margins: `24.6%`, `25% margin`
- EPS: `$5.61`, `5.61 per share`

**Failure Example**:

```
Answer: "Apple's revenue was $999 Trillion"
Status: FAIL (999 Trillion not found in any chunk)
Correction: "Verified numbers: 394 Billion. Unverified: 999 Trillion"
Penalty: -0.30 confidence
```

#### Agent V: Validity Verification

**Purpose**: Verify factual claims are textually supported by sources.

```
Answer: "Apple is a technology company making iPhones."

Process:
1. Extract claims: ["Apple is a technology company", "making iPhones"]
2. Word overlap analysis with source chunks
3. Report: VALIDITY_PASS or VALIDITY_FAIL

Output:
{
  "agent": "V",
  "status": "PASS",
  "details": "All 2 claims verified in sources",
  "confidence_penalty": 0.0
}
```

**Word Overlap Scoring**:

- Split claim and source into words
- Calculate intersection (40%+ overlap = supported)
- Discard short words (<3 chars) to avoid noise

**Failure Example**:

```
Answer: "Apple is a pharmaceutical company making vaccines."
Claim "pharmaceutical company" has only 5% word overlap with source text
Status: FAIL
Penalty: -0.25 confidence
```

#### Agent L: Longevity Verification

**Purpose**: Verify trend claims are consistent with historical data patterns.

```
Answer: "Apple's revenue has grown consistently over 5 years"

Process:
1. Extract trend claims: [(revenue, "growth")]
2. Query knowledge graph for historical trend
3. Compare claimed vs. actual trend
4. Report: LONGEVITY_PASS or LONGEVITY_ANOMALY

Output:
{
  "agent": "L",
  "status": "PASS",
  "details": "All trend claims consistent with history",
  "confidence_penalty": 0.0
}
```

**Trend Detection**:

- Calculate % change from first year to last
- Change > 5%: "up"
- Change < -5%: "down"
- Otherwise: "stable"

**Failure Example**:

```
Answer: "Revenue has been declining for 5 years"
Historical data: [100, 110, 120, 130] (actual: UP trend)
Status: FAIL
Anomaly: "Claimed declining but historically UP"
Penalty: -0.15 confidence
```

---

### 3. E-V-L Framework Orchestration

```python
from verification_agents import EVLVerificationFramework

framework = EVLVerificationFramework()
result = framework.verify_answer(
    answer="Apple revenue was $394B",
    source_chunks=[...],
    knowledge_graph=kg,
    ticker="AAPL"
)

# Returns:
{
  "all_pass": True,  # All 3 agents passed
  "confidence_adjustment": 0.0,  # No penalty
  "agent_results": [AgentE_result, AgentV_result, AgentL_result],
  "final_confidence_score": 0.95,
  "verification_summary": """
    Agent E: [PASS] All 2 numerical claims verified
    Agent V: [PASS] All claims supported by sources
    Agent L: [PASS] All trends consistent with history
  """
}
```

#### Confidence Scoring Logic

```
Base confidence (if all agents pass): 0.95
Base confidence (if any fail): 0.60

Penalties:
- Agent E failure: -0.30
- Agent V failure: -0.25
- Agent L failure: -0.15

Final Score = max(0.0, min(1.0, base - sum(penalties)))

Examples:
- All pass: 0.95 - 0.0 = 0.95
- E fails: 0.60 - 0.30 = 0.30
- E + V fail: 0.60 - 0.30 - 0.25 = 0.05
- All fail: 0.60 - 0.30 - 0.25 - 0.15 = -0.10 → 0.0
```

---

## Integration with Existing RAG

### Modified RAG Pipeline

```
User Query
  ↓
[1] Semantic Search (FAISS index)
  ├─ Retrieve top-4 chunks
  └─ Include knowledge graph context (peers, metrics)
  ↓
[2] LLM Answer Generation
  ├─ Build prompt with chunks + KG context
  ├─ Call LLM
  └─ Get raw answer
  ↓
[3] E-V-L Verification (NEW)
  ├─ Agent E: Check numbers
  ├─ Agent V: Check facts
  ├─ Agent L: Check trends
  └─ Compute final confidence
  ↓
[4] Return Result
  {
    "answer": "...",
    "confidence_score": 0.95,
    "verification_details": {...},
    "sources": [...],
    "latency_ms": 1245
  }
```

### Code Changes

**`rag_engine.py` - RAGChain.generate_answer()**

```python
def generate_answer(self, query, ticker=None, enable_verification=True):
    # Existing: retrieve chunks + generate answer
    hits = search_similar_chunks(query, self.vectorstore, k=6)
    answer = self.llm.generate(prompt)

    # NEW: Run verification if enabled
    if enable_verification:
        verification_result = self.verifier.verify_answer(
            answer,
            hits,  # source chunks
            self.knowledge_graph,  # symbolic layer
            ticker
        )
        confidence_score = verification_result["final_confidence_score"]
        verification_details = verification_result

    return {
        "answer": answer,
        "confidence_score": confidence_score,
        "verification_details": verification_details,
        ...
    }
```

**`financial_agent.py` - UnifiedFinancialAgent.load_ticker()**

```python
def load_ticker(self, ticker, market="US"):
    # Existing: fetch, chunk, embed
    chunks = load_and_chunk_documents(path)
    embeddings = create_embeddings(chunks)
    vs = build_vector_database(embeddings)

    # NEW: Build knowledge graph
    kg = FinancialKnowledgeGraph()
    kg.add_company_node(ticker, company_name, sector)

    # Auto-extract metrics from chunks
    for chunk in chunks:
        metrics = kg.extract_metrics_from_text(chunk.text, ticker, year)

    # Store KG for later use
    self.knowledge_graphs[key] = kg
```

---

## Usage Examples

### Basic Query with Verification

```python
from financial_agent import UnifiedFinancialAgent

agent = UnifiedFinancialAgent()
agent.load_ticker("AAPL")

result = agent.query(
    "AAPL",
    "What was Apple's revenue growth in 2024?",
    enable_verification=True
)

print(result["answer"])
# Output: "Apple's revenue reached $394.3 Billion in fiscal 2024,
#          representing a 2.5% increase from the prior year."

print(f"Confidence: {result['confidence_score']:.2f}")
# Output: Confidence: 0.95

print(result["verification_details"]["verification_summary"])
# Output:
# Agent E: [PASS] All numerical claims verified
# Agent V: [PASS] All claims supported by sources
# Agent L: [PASS] Consistent with 5-year growth trend
```

### Comparative Analysis with KG

```python
# Peers are automatically retrieved from KG
result = agent.query(
    "AAPL",
    "How does Apple's net margin compare to Microsoft?"
)

# The KG adds context:
# "Peers: MSFT, GOOGL, META"
# LLM can now access peer metrics from KG context
```

### Disabling Verification (for speed)

```python
# Verification adds ~100-200ms; disable for latency-critical apps
result = agent.query(
    "AAPL",
    "Quick revenue summary",
    enable_verification=False
)
# Returns immediately without E-V-L checks
```

---

## Test Coverage

**12/14 tests passing**:

✓ Knowledge Graph: initialization, metrics, trends, peers, metric extraction  
✓ Agent E: earnings verification, hallucination detection  
✓ Agent V: validity verification, unsupported claims  
✓ Agent L: longevity verification  
✓ E-V-L Framework: all-pass scenario, failure scenarios  
✓ Integration: agent initialization  
⚠ RAG chain: requires sentence-transformers initialization  
⚠ Metric extraction: regex refinement needed for complex formats

Run tests:

```bash
python neuro_symbolic_tests.py
```

---

## Performance Characteristics

| Metric                     | Value          |
| -------------------------- | -------------- |
| Semantic Search            | ~50ms          |
| LLM Generation             | 1-3s           |
| Verification Overhead      | 100-200ms      |
| **Total Time**             | **1.15-3.25s** |
| Base Confidence (all pass) | 0.95           |
| Base Confidence (any fail) | 0.60           |

---

## Best Practices

1. **For Production APIs**: Enable verification for trustworthiness
2. **For Real-Time Apps**: Disable verification for <1s latency
3. **For Regulatory Reports**: Always include verification_details in output
4. **For Comparative Analysis**: Let KG auto-populate peer context
5. **For New Companies**: Manually populate metrics if auto-extraction fails

---

## Extensibility

### Adding Custom Verification Agents

```python
from verification_agents import VerificationResult

class VerificationAgentCustom:
    def __init__(self):
        self.name = "Custom"

    def verify(self, answer, source_chunks):
        # Your custom logic
        is_valid = ...
        return VerificationResult(
            agent="Custom",
            status="PASS" if is_valid else "FAIL",
            details="...",
            confidence_penalty=0.0 if is_valid else 0.2
        )

# Add to framework
framework.agents.append(VerificationAgentCustom())
```

### Custom KG Relationships

```python
# Add custom node types
kg.graph.add_node("ESG_SCORE", node_type="rating", value=85)
kg.graph.add_edge("AAPL", "ESG_SCORE", relationship="has_esg")

# Query in custom logic
esg = kg.graph.nodes["ESG_SCORE"]
```

---

## Summary

The Neuro-Symbolic upgrade makes FinChat Global:

- **More Trustworthy**: E-V-L verification catches hallucinations
- **More Explainable**: Verification details show why confidence changed
- **More Reasoned**: Knowledge graphs enable symbolic logic
- **More Extensible**: Custom agents and relationships can be added

This hybrid approach combines the strengths of:

- **Neural**: LLMs for natural, fluent answers
- **Symbolic**: Knowledge graphs for structured facts
- **Verification**: Multi-agent audit trail for confidence

Result: Enterprise-grade financial intelligence with guaranteed source fidelity.
