import os
import logging
import numpy as np
from typing import List
from pathlib import Path
from openai import OpenAI

from app.models.schemas import DocumentChunk, RetrievalResult
from app.services.embeddings import load_embeddings

logger = logging.getLogger(__name__)

def cosine_similarity(query_emb: np.ndarray, doc_embs: np.ndarray) -> np.ndarray:
    """
    Computes cosine similarity safely against a 2D matrix of Document vectors.
    """
    if query_emb.ndim != 1:
        raise ValueError(f"Query embedding must be 1D, got {query_emb.ndim}D")
    
    if doc_embs.ndim != 2:
        raise ValueError(f"Document embeddings must be 2D matrix, got {doc_embs.ndim}D")
        
    if doc_embs.shape[1] == 0:
        raise ValueError("Document embeddings matrix is empty (0 columns).")
        
    if query_emb.shape[0] != doc_embs.shape[1]:
        raise ValueError(f"Dimension mismatch: Query has {query_emb.shape[0]} but db has {doc_embs.shape[1]}")
        
    if not np.isfinite(query_emb).all():
        raise ValueError("Query embedding contains non-finite values.")
        
    if not np.isfinite(doc_embs).all():
        raise ValueError("Document embeddings matrix contains non-finite values.")
        
    query_norm = np.linalg.norm(query_emb)
    doc_norms = np.linalg.norm(doc_embs, axis=1)
    
    # Avoid zero division natively
    if query_norm == 0.0:
        return np.zeros(doc_embs.shape[0], dtype=np.float32)
        
    safe_doc_norms = np.where(doc_norms == 0.0, 1.0, doc_norms)
    
    dot_products = np.dot(doc_embs, query_emb)
    similarities = dot_products / (query_norm * safe_doc_norms)
    
    # Force zero where DB arrays themselves were null mathematically originally
    similarities = np.where(doc_norms == 0.0, 0.0, similarities)
    
    return similarities

class RetrievalService:
    def __init__(self, storage_dir: Path | str):
        self.storage_dir = Path(storage_dir)
        try:
            self.embeddings_matrix, self.chunks = load_embeddings(self.storage_dir)
        except Exception as e:
            logger.error(f"Failed to load embedded index from {self.storage_dir}")
            raise RuntimeError(f"Corrupted or missing storage index: {e}") from e
            
        if self.embeddings_matrix.ndim != 2:
            raise ValueError(f"Corrupted storage matrix dimensionality. Expected 2D, got {self.embeddings_matrix.ndim}D")
            
        if self.embeddings_matrix.shape[0] != len(self.chunks):
            raise ValueError(f"Vector/Metadata count mismatch explicitly mapped.")
            
        if not np.isfinite(self.embeddings_matrix).all():
            raise ValueError("Corrupted stored matrix: contains non-finite values.")

    def get_query_embedding(self, question: str) -> np.ndarray:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for generating query embeddings.")
            
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        client = OpenAI(api_key=api_key)
        
        try:
            response = client.embeddings.create(
                input=[question],
                model=model
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            raise RuntimeError(f"OpenAI API query embedding failure: {e}") from e

    def retrieve(self, question: str) -> List[RetrievalResult]:
        top_k = int(os.getenv("RETRIEVAL_TOP_K", "8"))
        min_score = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.60"))
        
        query_emb = self.get_query_embedding(question)
        
        similarities = cosine_similarity(query_emb, self.embeddings_matrix)
        
        results = []
        for i, score in enumerate(similarities):
            if score >= min_score:
                c = self.chunks[i]
                results.append(RetrievalResult(
                    chunk_id=c.chunk_id,
                    document=c.document,
                    file_type=c.file_type,
                    text=c.text,
                    section=c.section,
                    page=c.page,
                    similarity_score=float(score)
                ))
                
        # Deterministic Ranking mapping:
        # 1. Similarity Descending
        # 2. Chunk ID Ascending (Tie-Breaker)
        results.sort(key=lambda x: (-x.similarity_score, x.chunk_id))
        
        return results[:top_k]
