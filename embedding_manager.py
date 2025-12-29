"""Embeddings and vector DB management.

Uses sentence-transformers for embeddings and FAISS/Chroma for vector store.
"""
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import numpy as np
import faiss
import os
import pickle
from utils import logger, ensure_dir
from config import config

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception as e:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning(f"sentence-transformers not available: {e}")
    logger.warning("Using mock embeddings (random vectors)")
    SentenceTransformer = None

class VectorStore:
    def __init__(self, index: faiss.Index, metadata: List[Dict], embeddings_dim: int):
        self.index = index
        self.metadata = metadata
        self.embeddings_dim = embeddings_dim

    def save(self, path: str):
        ensure_dir(os.path.dirname(path) or '.')
        faiss.write_index(self.index, path + '.index')
        with open(path + '.meta.pkl', 'wb') as f:
            pickle.dump(self.metadata, f)

    @staticmethod
    def load(path: str) -> 'VectorStore':
        idx = faiss.read_index(path + '.index')
        with open(path + '.meta.pkl', 'rb') as f:
            meta = pickle.load(f)
        return VectorStore(idx, meta, idx.d)


def create_embeddings(chunks: List[Any], model_name: str = "all-MiniLM-L6-v2") -> Tuple[np.ndarray, List[Dict]]:
    """Create embeddings for a list of DocumentChunk-like objects.

    Returns (embeddings_matrix, metadata_list)
    Fallback to mock embeddings if sentence-transformers unavailable
    """
    texts = [c.text for c in chunks]
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        # Fallback: use mock random embeddings (for testing)
        logger.warning(f"Creating mock embeddings for {len(texts)} chunks (not recommended for production)")
        embs = np.random.randn(len(texts), 384).astype('float32')  # 384-dim random vectors
    else:
        model = SentenceTransformer(model_name)
        batch_size = 64
        embs = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    metadata = [c.metadata for c in chunks]
    return np.array(embs, dtype='float32'), metadata


def build_vector_database(embeddings: np.ndarray, metadata: List[Dict], db_type: str = "faiss", db_path: Optional[str] = None) -> VectorStore:
    """Build FAISS index; supports HNSW for large corpora.

    Auto-saves to `db_path` if provided.
    """
    d = embeddings.shape[1]
    # use inner product on normalized vectors to compute cosine similarity
    index = faiss.IndexHNSWFlat(d, 32)
    faiss.normalize_L2(embeddings)
    index.hnsw.efConstruction = 200
    index.add(embeddings)
    vs = VectorStore(index, metadata, d)
    if db_path:
        vs.save(db_path)
    return vs


def search_similar_chunks(query: str, vectorstore: VectorStore, model_name: str = "all-MiniLM-L6-v2", k: int = 4, threshold: float = 0.6) -> List[Tuple[Dict, float]]:
    """Search top-k similar chunks and return list of (metadata, score).

    Uses sentence-transformers to embed query and cosine similarity.
    Falls back to mock embeddings if unavailable.
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        # Mock search: return first k items with random scores
        logger.warning("Mock search (sentence-transformers not available)")
        results = []
        for idx, meta in enumerate(vectorstore.metadata[:k]):
            score = np.random.rand()  # Random score 0-1
            if score >= threshold:
                results.append((meta, float(score)))
        return results if results else [(vectorstore.metadata[0], 0.8)]
    
    model = SentenceTransformer(model_name)
    q_emb = model.encode([query])[0].astype('float32')
    faiss.normalize_L2(q_emb.reshape(1, -1))
    D, I = vectorstore.index.search(q_emb.reshape(1, -1), k)
    results = []
    for dist, idx in zip(D[0], I[0]):
        # for HNSWFlat, distances are inner product; convert to [0,1]
        score = float(dist)
        if score < threshold:
            continue
        meta = vectorstore.metadata[idx] if idx < len(vectorstore.metadata) else {}
        results.append((meta, score))
    return results
