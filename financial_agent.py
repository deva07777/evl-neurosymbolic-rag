"""UnifiedFinancialAgent: multi-market RAG orchestration with Neuro-Symbolic layer."""
from typing import Dict, List, Optional, Any
from embedding_manager import VectorStore, create_embeddings, build_vector_database
from rag_engine import setup_llm, build_rag_chain
from document_fetcher import fetch_sec_filing, fetch_indian_annual_report, validate_document
from document_processor import load_and_chunk_documents, extract_financial_tables
from knowledge_graph import FinancialKnowledgeGraph
from utils import logger, save_json, load_json
from config import config
import time
import threading

class UnifiedFinancialAgent:
    def __init__(self):
        self.vectorstores: Dict[str, VectorStore] = {}
        self.documents: Dict[str, List] = {}
        self.cache: Dict[str, Any] = {}
        self.knowledge_graphs: Dict[str, FinancialKnowledgeGraph] = {}  # NEW: Symbolic layer

    def load_ticker(self, ticker: str, market: str = "US") -> Dict[str, Any]:
        key = f"{market}::{ticker}"
        if key in self.vectorstores:
            return {"status": "cached", "documents": len(self.documents.get(key, []))}
        try:
            if market.upper() == 'US':
                path = fetch_sec_filing(ticker, "10-K")
            else:
                path = fetch_indian_annual_report(ticker, ticker)
            meta = validate_document(str(path))
            chunks = load_and_chunk_documents(str(path))
            # attach chunk metadata for search
            for c in chunks:
                c.metadata.update({'text': c.text, 'source': meta.get('path')})
            embs, meta_list = create_embeddings(chunks)
            vs = build_vector_database(embs, meta_list, db_path=str(config.VECTOR_DB_DIR + f"/{key}"))
            self.vectorstores[key] = vs
            self.documents[key] = chunks
            
            # NEW: Build knowledge graph
            kg = FinancialKnowledgeGraph()
            kg.add_company_node(ticker, ticker, "Technology" if ticker in ["AAPL", "MSFT"] else "Finance")
            
            # Extract metrics from chunks
            for chunk in chunks:
                try:
                    extracted = kg.extract_metrics_from_text(chunk.text, ticker, 2024)
                    if extracted:
                        logger.info(f"Extracted metrics for {ticker}: {extracted}")
                except Exception as e:
                    logger.debug(f"Could not extract metrics: {e}")
            
            self.knowledge_graphs[key] = kg
            
            return {"status": "loaded", "documents": len(chunks), "knowledge_graph": kg.visualize_summary(ticker)}
        except Exception as e:
            logger.exception("Failed to load ticker %s", ticker)
            return {"status": "error", "error": str(e)}

    def query(self, ticker: str, question: str, market: str = "US", enable_verification: bool = True) -> Dict[str, Any]:
        key = f"{market}::{ticker}"
        if key not in self.vectorstores:
            self.load_ticker(ticker, market)
        vs = self.vectorstores.get(key)
        kg = self.knowledge_graphs.get(key)  # NEW: Get knowledge graph
        if not vs:
            return {"error": "no data"}
        llm = setup_llm()
        rag = build_rag_chain(vs, llm, knowledge_graph=kg)  # NEW: Pass KG to RAG chain
        t0 = time.time()
        res = rag.generate_answer(question, ticker=ticker, k=6, threshold=config.SIMILARITY_THRESHOLD, enable_verification=enable_verification)
        res['latency_ms'] = int((time.time() - t0)*1000)
        # Use confidence from verification if available, else calculate
        if 'confidence_score' not in res or res['confidence_score'] is None:
            res['confidence_score'] = self.calculate_confidence_score(res.get('answer',''), res.get('source_documents', []))
        self.track_audit_trail(question, res.get('source_documents', []), res.get('answer',''), res.get('confidence_score', 0.0))
        return res

    def calculate_confidence_score(self, answer: str, sources: List[Any]) -> float:
        # heuristics: presence of numeric citations and number of sources
        score = 0.0
        if any(ch.isdigit() for ch in answer):
            score += 0.4
        if len(sources) >= 2:
            score += 0.4
        score += min(0.2, 0.05 * len(sources))
        return min(1.0, score)

    def track_audit_trail(self, query: str, retrieved_chunks: List[Any], answer: str, confidence: float) -> None:
        rec = {
            'timestamp': time.time(),
            'query': query,
            'retrieved': retrieved_chunks,
            'answer_excerpt': answer[:400],
            'confidence': confidence
        }
        logger.info('Audit: %s', rec)
        # store lightweight
        self.cache[f"audit::{int(time.time())}"] = rec

    def compare_companies(self, ticker1: str, ticker2: str, metric: str) -> Dict[str, Any]:
        q = f"Extract the {metric} for {ticker1} and {ticker2} and compare their latest values. Provide sources."
        r1 = self.query(ticker1, q, market='US')
        return {'comparison': r1}

    def get_financial_summary(self, ticker: str, market: str = 'US') -> Dict[str, Any]:
        q = "Provide a concise financial summary: revenue, margin, growth, debt, moats. Use only document context."
        return self.query(ticker, q, market)

    def batch_query(self, queries: List[str]) -> List[Dict[str, Any]]:
        results = []
        threads = []
        lock = threading.Lock()
        def worker(q):
            r = self.query(q.get('ticker'), q.get('question'), q.get('market','US'))
            with lock:
                results.append(r)
        for q in queries:
            t = threading.Thread(target=worker, args=(q,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        return results

    def compare_answers(self, query: str, providers: List[str]) -> Dict[str, Any]:
        out = {}
        for p in providers:
            llm = setup_llm(provider=p)
            # reuse a global vectorstore? For demo use the first loaded one
            if not self.vectorstores:
                return {"error": "No index loaded"}
            key = next(iter(self.vectorstores.keys()))
            rag = build_rag_chain(self.vectorstores[key], llm)
            res = rag.generate_answer(query)
            out[p] = res
        return out
