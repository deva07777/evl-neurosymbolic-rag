"""RAG chain and LLM integration with Neuro-Symbolic verification.

Provides LLM provider interface and retrieval-augmented generation pipeline
with E-V-L verification framework.
"""
from typing import Any, Dict, List, Optional
import time
import logging
from utils import logger, timeit
from config import config
from verification_agents import EVLVerificationFramework

# Minimal provider abstraction
class LLMProvider:
    def __init__(self, provider: str = None, model: str = None, **kwargs):
        self.provider = provider or config.LLM_PROVIDER
        self.model = model or config.LLM_MODEL
        self.temperature = kwargs.get('temperature', config.LLM_TEMPERATURE)
        self.max_tokens = kwargs.get('max_tokens', config.LLM_MAX_TOKENS)
        # provider-specific initialization
        if self.provider == 'openai':
            try:
                import openai
                self.client = openai
            except Exception:
                logger.warning('openai not installed')
                self.client = None
        else:
            self.client = None

    def generate(self, prompt: str) -> Dict[str, Any]:
        start = time.time()
        if self.provider == 'openai' and self.client:
            resp = self.client.ChatCompletion.create(
                model=self.model,
                messages=[{"role":"user","content":prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            text = resp['choices'][0]['message']['content']
        else:
            # simple echo fallback
            text = "[LLM stub] " + prompt[:200]
        return {"text": text, "elapsed": time.time()-start}


class RAGChain:
    def __init__(self, vectorstore, llm: LLMProvider, prompt_template: Optional[str] = None, knowledge_graph: Optional[Any] = None):
        self.vectorstore = vectorstore
        self.llm = llm
        self.knowledge_graph = knowledge_graph
        self.prompt_template = prompt_template or "Use only the provided contexts to answer the question. Cite sources inline.\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
        self.verifier = EVLVerificationFramework()

    @timeit
    def generate_answer(self, query: str, ticker: Optional[str] = None, k: int = 4, threshold: float = 0.6, return_sources: bool = True, enable_verification: bool = True) -> Dict:
        from embedding_manager import search_similar_chunks
        t0 = time.time()
        hits = search_similar_chunks(query, self.vectorstore, k=k, threshold=threshold)
        retrieval_time = (time.time() - t0)
        context_parts = []
        sources = []
        for i, (meta, score) in enumerate(hits):
            context_parts.append(f"[S{i+1}] (score={score:.3f})\n{meta.get('text','') or meta.get('excerpt','') or meta.get('source','')}")
            sources.append({"metadata": meta, "score": score})
        context = "\n\n".join(context_parts)[:4000]
        
        # Add knowledge graph context if available
        kg_context = ""
        if self.knowledge_graph and ticker:
            kg_context = "\n\n[Knowledge Graph Context]\n" + self.knowledge_graph.get_context_prompt(ticker)
        
        prompt = self.prompt_template.format(context=context + kg_context, question=query)
        t1 = time.time()
        gen = self.llm.generate(prompt)
        generation_time = time.time() - t1
        answer = gen.get('text', '')
        
        # Run E-V-L verification if enabled
        verification_details = None
        confidence_score = 0.8
        if enable_verification:
            logger.info("Running E-V-L verification framework...")
            # Convert sources to format expected by verifier
            verification_sources = [{"metadata": s.get("metadata", {}), "text": s.get("metadata", {}).get("text", "")} for s in sources]
            verification_result = self.verifier.verify_answer(answer, verification_sources, self.knowledge_graph, ticker)
            verification_details = {
                "all_agents_pass": verification_result["all_pass"],
                "agent_e": verification_result["agent_results"][0].__dict__,
                "agent_v": verification_result["agent_results"][1].__dict__,
                "agent_l": verification_result["agent_results"][2].__dict__,
                "verification_summary": verification_result["verification_summary"]
            }
            confidence_score = verification_result["final_confidence_score"]
        
        return {
            'answer': answer,
            'source_documents': sources if return_sources else [],
            'confidence_score': confidence_score,
            'retrieval_time_ms': int(retrieval_time*1000),
            'generation_time_ms': int(generation_time*1000),
            'verification_details': verification_details
        }


def setup_llm(provider: str = None, model: str = None, **kwargs) -> LLMProvider:
    return LLMProvider(provider=provider, model=model, **kwargs)


def build_rag_chain(vectorstore, llm: LLMProvider, prompt_template: str = None, knowledge_graph: Optional[Any] = None) -> RAGChain:
    return RAGChain(vectorstore, llm, prompt_template, knowledge_graph)
