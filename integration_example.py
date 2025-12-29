"""Integration example: Using the Neuro-Symbolic Financial RAG Agent.

This script demonstrates the complete workflow with knowledge graphs
and E-V-L verification framework.
"""
from financial_agent import UnifiedFinancialAgent
import json

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def demo_basic_query():
    """Demo 1: Basic query with verification."""
    print_section("DEMO 1: Basic Query with E-V-L Verification")
    
    agent = UnifiedFinancialAgent()
    
    print("\n[1] Loading AAPL ticker and building knowledge graph...")
    load_result = agent.load_ticker("AAPL", market="US")
    print(f"    Status: {load_result.get('status')}")
    if 'knowledge_graph' in load_result:
        print(f"    {load_result['knowledge_graph']}")
    
    print("\n[2] Asking question about Apple...")
    question = "What was Apple's total revenue in the most recent filing?"
    print(f"    Question: {question}")
    
    print("\n[3] Running query with E-V-L verification...")
    result = agent.query("AAPL", question, enable_verification=True)
    
    print(f"\n[4] Answer:")
    print(f"    {result.get('answer', 'No answer generated')[:200]}...")
    
    print(f"\n[5] Confidence Score: {result.get('confidence_score', 'N/A'):.2f}")
    
    print(f"\n[6] Verification Details:")
    if result.get('verification_details'):
        vd = result['verification_details']
        print(f"    All Agents Pass: {vd.get('all_agents_pass')}")
        print(f"    Summary:")
        for line in vd.get('verification_summary', '').split('\n'):
            if line.strip():
                print(f"      {line}")
    
    print(f"\n[7] Performance Metrics:")
    print(f"    Retrieval Time: {result.get('retrieval_time_ms', 0)}ms")
    print(f"    Generation Time: {result.get('generation_time_ms', 0)}ms")
    print(f"    Total Latency: {result.get('latency_ms', 0)}ms")
    
    return agent


def demo_comparison():
    """Demo 2: Comparative analysis using KG peers."""
    print_section("DEMO 2: Comparative Analysis with Auto-Peer Context")
    
    agent = UnifiedFinancialAgent()
    agent.load_ticker("AAPL", market="US")
    
    print("\n[1] Knowledge graph automatically includes peers:")
    kg = agent.knowledge_graphs.get("US::AAPL")
    if kg:
        peers = kg.get_peers("AAPL")
        print(f"    Peers: {peers if peers else 'None extracted (can be manually added)'}")
        print(f"    Sector: Technology")
    
    print("\n[2] Comparing with Microsoft...")
    question = "How does Apple's profitability compare to competitors?"
    print(f"    Question: {question}")
    
    result = agent.query("AAPL", question, enable_verification=True)
    print(f"\n[3] Answer: {result.get('answer', '')[:300]}...")
    print(f"    Confidence: {result.get('confidence_score', 0):.2f}")


def demo_verification_failure():
    """Demo 3: Showing how verification catches hallucinations."""
    print_section("DEMO 3: Verification Catching Hallucinations")
    
    print("""
    Scenario: LLM generates a plausible-sounding but false claim:
    
    LLM Answer: "Apple's quarterly revenue reached $500 Billion in 2024"
    
    E-V-L Verification Results:
    
    [Agent E - Earnings]
    Status: FAIL
    Details: "Unverified numerical claim: 500 Billion"
    Correction: "Verified number from sources: 394.3 Billion. 
                Claimed 500B is not found in any retrieved chunk."
    Penalty: -0.30
    
    [Agent V - Validity]
    Status: PASS
    Details: "Claim structure is supported (revenue + number + period)"
    Penalty: 0.0
    
    [Agent L - Longevity]
    Status: PASS
    Details: "Trend consistent with historical growth"
    Penalty: 0.0
    
    Final Confidence Score: 0.95 - 0.30 = 0.65
    
    RESULT: Answer returned with lower confidence + correction shown to user
    """)


def demo_knowledge_graph_operations():
    """Demo 4: Direct knowledge graph operations."""
    print_section("DEMO 4: Direct Knowledge Graph Operations")
    
    from knowledge_graph import FinancialKnowledgeGraph
    
    kg = FinancialKnowledgeGraph()
    
    print("\n[1] Building a knowledge graph...")
    kg.add_company_node("AAPL", "Apple Inc.", "Technology", market="US")
    kg.add_company_node("MSFT", "Microsoft Corp.", "Technology", market="US")
    kg.add_company_node("IBM", "IBM Corp.", "Technology", market="US")
    
    print("    Added 3 companies")
    
    print("\n[2] Adding financial metrics...")
    # Apple metrics
    kg.add_metric_node("AAPL", "revenue", 394.3e9, 2024)
    kg.add_metric_node("AAPL", "revenue", 383.3e9, 2023)
    kg.add_metric_node("AAPL", "net_income", 93.7e9, 2024)
    kg.add_metric_node("AAPL", "margin", 23.8, 2024)
    
    # Microsoft metrics
    kg.add_metric_node("MSFT", "revenue", 245.1e9, 2024)
    kg.add_metric_node("MSFT", "revenue", 198.3e9, 2023)
    
    print("    Added metrics: revenue, net_income, margin")
    
    print("\n[3] Adding peer relationships...")
    kg.add_peer_relationship("AAPL", "MSFT", similarity=0.88)
    kg.add_peer_relationship("AAPL", "IBM", similarity=0.65)
    
    print("    AAPL peers: MSFT (0.88), IBM (0.65)")
    
    print("\n[4] Analyzing trends...")
    years, values, trend = kg.get_trend("AAPL", "revenue")
    print(f"    AAPL Revenue Trend: {trend}")
    print(f"    Historical values (Billions): {[v/1e9 for v in values]}")
    
    years, values, trend = kg.get_trend("MSFT", "revenue")
    print(f"    MSFT Revenue Trend: {trend}")
    print(f"    Historical values (Billions): {[v/1e9 for v in values]}")
    
    print("\n[5] Extracting metrics from text...")
    text = "Microsoft reported total revenue of $245.1 Billion in 2024. Net income was $88.2 Billion. Operating margin improved to 36%."
    metrics = kg.extract_metrics_from_text(text, "MSFT", 2024)
    print(f"    Extracted: {list(metrics.keys())}")
    print(f"    Revenue: ${metrics.get('revenue', 0)/1e9:.1f}B")
    print(f"    Net Income: ${metrics.get('net_income', 0)/1e9:.1f}B")
    print(f"    Margin: {metrics.get('margin', 0):.1f}%")
    
    print("\n[6] Generating context for LLM...")
    context = kg.get_context_prompt("AAPL")
    print(context)


def main():
    """Run all demos."""
    print("\n" + "#"*70)
    print("# FinChat Global - Neuro-Symbolic RAG Agent")
    print("# Comprehensive Integration Demonstration")
    print("#"*70)
    
    try:
        # Demo 1: Basic query
        agent = demo_basic_query()
        
        # Demo 2: Comparison
        demo_comparison()
        
        # Demo 3: Verification failure scenario
        demo_verification_failure()
        
        # Demo 4: KG operations
        demo_knowledge_graph_operations()
        
    except Exception as e:
        print(f"\nNote: Some demos may fail due to missing API keys or data:")
        print(f"  {e}")
        print("\nTo run full demos:")
        print("  1. Set OPENAI_API_KEY environment variable")
        print("  2. Ensure SEC filings are cached or downloadable")
        print("  3. Run: python integration_example.py")
    
    print_section("Integration Example Complete")
    print("""
    Key Takeaways:
    
    1. Knowledge Graph (Symbolic Layer):
       - Automatically builds from document extraction
       - Tracks metrics, trends, and peer relationships
       - Provides structured context to LLM
    
    2. E-V-L Verification (Multi-Agent Audit):
       - Agent E: Validates numerical claims
       - Agent V: Validates factual claims
       - Agent L: Validates trend consistency
    
    3. Confidence Scoring:
       - All agents pass → 0.95 confidence
       - Any agent fails → reduced confidence (0.60-0.80)
       - Shows correction to user when hallucination detected
    
    4. Extensibility:
       - Add custom verification agents
       - Add custom graph relationships
       - Configure thresholds per use case
    
    For production use:
       - Enable verification for regulatory/audit scenarios
       - Disable for real-time requirements (<1s latency)
       - Monitor confidence scores as quality metric
    """)


if __name__ == '__main__':
    main()
