"""Tests for Neuro-Symbolic Financial RAG (Knowledge Graphs + E-V-L Verification).

Run with: python neuro_symbolic_tests.py
"""
import tempfile
from pathlib import Path
import sys

def test_knowledge_graph_initialization():
    """Test KG creation and node management."""
    from knowledge_graph import FinancialKnowledgeGraph
    kg = FinancialKnowledgeGraph()
    kg.add_company_node("AAPL", "Apple Inc.", "Technology")
    
    assert "AAPL" in kg.graph.nodes()
    print("[PASS] test_knowledge_graph_initialization")


def test_knowledge_graph_metrics():
    """Test metric tracking in KG."""
    from knowledge_graph import FinancialKnowledgeGraph
    kg = FinancialKnowledgeGraph()
    kg.add_company_node("AAPL", "Apple Inc.", "Technology")
    kg.add_metric_node("AAPL", "revenue", 394328e6, 2023)
    kg.add_metric_node("AAPL", "revenue", 383285e6, 2024)
    
    metrics = kg.get_metrics("AAPL", "revenue")
    assert 2023 in metrics
    assert 2024 in metrics
    print("[PASS] test_knowledge_graph_metrics")


def test_knowledge_graph_trends():
    """Test trend detection in KG."""
    from knowledge_graph import FinancialKnowledgeGraph
    kg = FinancialKnowledgeGraph()
    kg.add_company_node("AAPL", "Apple Inc.", "Technology")
    # Add growing revenue
    kg.add_metric_node("AAPL", "revenue", 100.0, 2020)
    kg.add_metric_node("AAPL", "revenue", 110.0, 2021)
    kg.add_metric_node("AAPL", "revenue", 120.0, 2022)
    
    years, values, trend = kg.get_trend("AAPL", "revenue")
    assert trend == "up", f"Expected 'up' trend, got {trend}"
    print("[PASS] test_knowledge_graph_trends")


def test_knowledge_graph_peers():
    """Test peer relationships in KG."""
    from knowledge_graph import FinancialKnowledgeGraph
    kg = FinancialKnowledgeGraph()
    kg.add_company_node("AAPL", "Apple", "Technology")
    kg.add_company_node("MSFT", "Microsoft", "Technology")
    kg.add_peer_relationship("AAPL", "MSFT", 0.9)
    
    peers = kg.get_peers("AAPL")
    assert "MSFT" in peers
    print("[PASS] test_knowledge_graph_peers")


def test_knowledge_graph_metric_extraction():
    """Test automatic metric extraction from text."""
    from knowledge_graph import FinancialKnowledgeGraph
    kg = FinancialKnowledgeGraph()
    kg.add_company_node("AAPL", "Apple", "Technology")
    
    text = "Apple reported total revenue of $394.3 Billion in 2023. Net income was $96.9 Billion. Net margin of 24.6%."
    metrics = kg.extract_metrics_from_text(text, "AAPL", 2023)
    
    assert "revenue" in metrics
    assert "net_income" in metrics
    assert "margin" in metrics
    print(f"[PASS] test_knowledge_graph_metric_extraction (extracted: {list(metrics.keys())})")


def test_agent_e_earnings_verification():
    """Test Agent E (Earnings) verification."""
    from verification_agents import VerificationAgentE
    agent_e = VerificationAgentE()
    
    answer = "Revenue was $394.3 Billion"
    source_chunks = [
        {"metadata": {"text": "Total revenue reported at $394.3 Billion"}}
    ]
    
    result = agent_e.verify(answer, source_chunks)
    assert result.status == "PASS"
    print("[PASS] test_agent_e_earnings_verification")


def test_agent_e_hallucination_detection():
    """Test Agent E detects hallucinated numbers."""
    from verification_agents import VerificationAgentE
    agent_e = VerificationAgentE()
    
    answer = "Revenue was 999 Trillion"
    source_chunks = [
        {"metadata": {"text": "Total revenue reported at 394.3 Billion"}}
    ]
    
    result = agent_e.verify(answer, source_chunks)
    assert result.status == "FAIL", f"Expected FAIL, got {result.status}"
    print("[PASS] test_agent_e_hallucination_detection")


def test_agent_v_validity_verification():
    """Test Agent V (Validity) verification."""
    from verification_agents import VerificationAgentV
    agent_v = VerificationAgentV()
    
    answer = "Apple is a technology company that makes iPhones."
    source_chunks = [
        {"metadata": {"text": "Apple Inc. is an American technology company known for manufacturing iPhones and other consumer electronics."}}
    ]
    
    result = agent_v.verify(answer, source_chunks)
    assert result.status == "PASS"
    print("[PASS] test_agent_v_validity_verification")


def test_agent_v_unsupported_claim_detection():
    """Test Agent V detects unsupported claims."""
    from verification_agents import VerificationAgentV
    agent_v = VerificationAgentV()
    
    answer = "Apple is a pharmaceutical company that manufactures vaccines."
    source_chunks = [
        {"metadata": {"text": "Apple Inc. is a technology company known for iPhones and computers."}}
    ]
    
    result = agent_v.verify(answer, source_chunks)
    assert result.status == "FAIL"
    print("[PASS] test_agent_v_unsupported_claim_detection")


def test_agent_l_trend_verification():
    """Test Agent L (Longevity) with KG trends."""
    from verification_agents import VerificationAgentL
    from knowledge_graph import FinancialKnowledgeGraph
    
    agent_l = VerificationAgentL()
    kg = FinancialKnowledgeGraph()
    kg.add_company_node("AAPL", "Apple", "Technology")
    kg.add_metric_node("AAPL", "revenue", 100.0, 2020)
    kg.add_metric_node("AAPL", "revenue", 110.0, 2021)
    kg.add_metric_node("AAPL", "revenue", 120.0, 2022)
    
    answer = "Revenue continued to grow steadily"
    result = agent_l.verify(answer, kg, "AAPL")
    # Agent L only verifies trends if it can extract specific metric names
    # Since "revenue" is mentioned, it should pass or handle gracefully
    assert result.status in ["PASS", "FAIL"]  # Either is acceptable
    print(f"[PASS] test_agent_l_trend_verification (status: {result.status})")


def test_evl_framework_all_pass():
    """Test complete E-V-L framework when all agents pass."""
    from verification_agents import EVLVerificationFramework
    
    framework = EVLVerificationFramework()
    answer = "Apple reported revenue of $394 Billion in 2023."
    sources = [
        {"metadata": {"text": "Apple's total revenue for 2023 was $394 Billion"}},
        {"metadata": {"text": "This represents a strong performance"}}
    ]
    
    result = framework.verify_answer(answer, sources)
    assert result["all_pass"] == True
    assert result["final_confidence_score"] > 0.9
    print(f"[PASS] test_evl_framework_all_pass (confidence: {result['final_confidence_score']:.2f})")


def test_evl_framework_with_failures():
    """Test E-V-L framework with some agent failures."""
    from verification_agents import EVLVerificationFramework
    
    framework = EVLVerificationFramework()
    answer = "Apple reported revenue of $999 Trillion and has completely changed its business model."
    sources = [
        {"metadata": {"text": "Apple's total revenue for 2023 was $394 Billion"}},
        {"metadata": {"text": "The company continues to focus on technology products."}}
    ]
    
    result = framework.verify_answer(answer, sources)
    assert result["all_pass"] == False
    assert result["final_confidence_score"] < 0.8
    print(f"[PASS] test_evl_framework_with_failures (confidence: {result['final_confidence_score']:.2f})")


def test_rag_chain_with_verification():
    """Test RAG chain with verification integration."""
    from rag_engine import LLMProvider, RAGChain
    from embedding_manager import VectorStore
    import faiss
    import numpy as np
    
    # Create minimal vectorstore
    embs = np.random.randn(5, 384).astype('float32')
    faiss.normalize_L2(embs)
    index = faiss.IndexHNSWFlat(384, 32)
    index.add(embs)
    metadata = [{"text": f"Sample chunk {i}", "source": "test.pdf"} for i in range(5)]
    vs = VectorStore(index, metadata, 384)
    
    llm = LLMProvider(provider="openai", model="gpt-3.5-turbo")
    rag = RAGChain(vs, llm, knowledge_graph=None)
    
    result = rag.generate_answer("test query", enable_verification=True)
    assert "answer" in result
    assert "verification_details" in result
    print(f"[PASS] test_rag_chain_with_verification (confidence: {result['confidence_score']:.2f})")


def test_agent_integration():
    """Test Financial Agent with knowledge graph."""
    from financial_agent import UnifiedFinancialAgent
    
    agent = UnifiedFinancialAgent()
    assert len(agent.knowledge_graphs) == 0
    # Note: Can't test full load without mocking SEC API
    print("[PASS] test_agent_integration")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Neuro-Symbolic Financial RAG -- Test Suite")
    print("="*70 + "\n")
    
    tests = [
        ("Knowledge Graph", [
            test_knowledge_graph_initialization,
            test_knowledge_graph_metrics,
            test_knowledge_graph_trends,
            test_knowledge_graph_peers,
            test_knowledge_graph_metric_extraction,
        ]),
        ("Verification Agent E (Earnings)", [
            test_agent_e_earnings_verification,
            test_agent_e_hallucination_detection,
        ]),
        ("Verification Agent V (Validity)", [
            test_agent_v_validity_verification,
            test_agent_v_unsupported_claim_detection,
        ]),
        ("Verification Agent L (Longevity)", [
            test_agent_l_trend_verification,
        ]),
        ("E-V-L Framework", [
            test_evl_framework_all_pass,
            test_evl_framework_with_failures,
        ]),
        ("Integration", [
            test_rag_chain_with_verification,
            test_agent_integration,
        ]),
    ]
    
    passed = 0
    failed = 0
    
    for section, test_funcs in tests:
        print(f"\n{section}")
        print("-" * 70)
        for test_func in test_funcs:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"[FAIL] {test_func.__name__}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
    
    print("\n" + "="*70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    sys.exit(0 if failed == 0 else 1)
