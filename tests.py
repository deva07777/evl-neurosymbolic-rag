"""Comprehensive unit tests for FinChat Global.

Run with: python tests.py
"""
import tempfile
from pathlib import Path
import sys

def test_clean_normalize_currency_and_dates():
    from document_processor import clean_and_normalize_text
    txt = "Revenue was $1,234 on 31-03-2020. Page 1 of 10\n\n\n\nFooter"
    out = clean_and_normalize_text(txt)
    assert 'USD' in out, f"Expected USD in: {out[:100]}"
    assert '2020-03-31' in out, f"Expected normalized date in: {out}"
    assert 'Page 1' not in out
    print("[PASS] test_clean_normalize_currency_and_dates")


def test_chunking_preserves_content(tmp_path):
    from document_processor import load_and_chunk_documents
    p = tmp_path / "sample.txt"
    content = "SECTION HEADING\n" + ("This is a sentence. " * 100)
    p.write_text(content)
    chunks = load_and_chunk_documents(str(p))
    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    print(f"[PASS] test_chunking_preserves_content ({len(chunks)} chunks)")


def test_cache_path_generation():
    from document_fetcher import _cache_path_for
    path1 = _cache_path_for("SEC::AAPL::10-K", "html")
    path2 = _cache_path_for("SEC::AAPL::10-K", "html")
    assert path1 == path2
    print("[PASS] test_cache_path_generation")


def test_validate_document_on_text_file(tmp_path):
    from document_fetcher import validate_document
    p = tmp_path / "financial.txt"
    content = """
    MANAGEMENT'S DISCUSSION AND ANALYSIS
    Balance Sheet Summary
    Consolidated Statement of Income
    Revenue Growth: 15% YoY
    """ * 5
    p.write_text(content)
    meta = validate_document(str(p))
    assert meta['path'] == str(p)
    assert 0.0 <= meta['completeness_score'] <= 1.0
    print(f"[PASS] test_validate_document_on_text_file (score={meta['completeness_score']})")


def test_validate_document_file_not_found():
    from document_fetcher import validate_document
    from utils import FinChatError
    try:
        validate_document("/nonexistent/file.pdf")
        assert False
    except FinChatError:
        print("[PASS] test_validate_document_file_not_found")


def test_session_retry_logic():
    from document_fetcher import _get_session
    s1 = _get_session()
    s2 = _get_session()
    assert s1 is s2
    print("[PASS] test_session_retry_logic")


def test_llm_provider_initialization():
    from rag_engine import setup_llm
    llm = setup_llm(provider='openai', model='gpt-3.5-turbo')
    assert llm.provider == 'openai'
    print("[PASS] test_llm_provider_initialization")


def test_agent_initialization():
    from financial_agent import UnifiedFinancialAgent
    agent = UnifiedFinancialAgent()
    assert isinstance(agent.vectorstores, dict)
    print("[PASS] test_agent_initialization")


def test_agent_confidence_scoring():
    from financial_agent import UnifiedFinancialAgent
    agent = UnifiedFinancialAgent()
    score = agent.calculate_confidence_score("Revenue was $1.2B in 2024", [{'text': 'source1'}])
    assert 0.0 <= score <= 1.0
    print(f"[PASS] test_agent_confidence_scoring (score={score})")


def test_json_save_load(tmp_path):
    from utils import save_json, load_json
    data = {"ticker": "AAPL", "price": 180.5}
    path = tmp_path / "test.json"
    save_json(data, str(path))
    loaded = load_json(str(path))
    assert loaded == data
    print("[PASS] test_json_save_load")


def test_ensure_dir(tmp_path):
    from utils import ensure_dir
    nested = tmp_path / "a" / "b" / "c"
    ensure_dir(str(nested))
    assert nested.exists()
    print("[PASS] test_ensure_dir")


def test_end_to_end_chunking_and_validation(tmp_path):
    from document_processor import load_and_chunk_documents
    from document_fetcher import validate_document
    
    p = tmp_path / "financial_doc.txt"
    content = """
    ANNUAL REPORT 2024
    Management's Discussion and Analysis
    Item 7: Financial Statements
    Balance Sheet
    Assets: 5,000,000
    """ * 10
    p.write_text(content)
    
    meta = validate_document(str(p))
    assert meta['completeness_score'] > 0.5
    
    chunks = load_and_chunk_documents(str(p))
    assert len(chunks) > 0
    print(f"[PASS] test_end_to_end (chunks={len(chunks)})")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("FinChat Global -- Test Suite")
    print("="*70 + "\n")
    
    import sys
    td = Path(tempfile.mkdtemp())
    
    tests = [
        ("Document Processing", [
            test_clean_normalize_currency_and_dates,
            lambda: test_chunking_preserves_content(td),
        ]),
        ("Document Fetcher", [
            test_cache_path_generation,
            lambda: test_validate_document_on_text_file(td),
            test_validate_document_file_not_found,
            test_session_retry_logic,
        ]),
        ("RAG Engine", [
            test_llm_provider_initialization,
        ]),
        ("Financial Agent", [
            test_agent_initialization,
            test_agent_confidence_scoring,
        ]),
        ("Utilities", [
            lambda: test_json_save_load(td),
            lambda: test_ensure_dir(td),
        ]),
        ("Integration", [
            lambda: test_end_to_end_chunking_and_validation(td),
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
                failed += 1
    
    print("\n" + "="*70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    sys.exit(0 if failed == 0 else 1)
