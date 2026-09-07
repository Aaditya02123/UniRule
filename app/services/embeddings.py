import os
import json
import logging
import time
import numpy as np
from pathlib import Path
from typing import List, Any
from openai import OpenAI
from pydantic import ValidationError

from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)

def generate_embeddings(chunks: List[DocumentChunk], batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))) -> np.ndarray:
    """
    Generates deterministic embeddings for a list of DocumentChunks via OpenAI API.
    Maintains exact 1:1 order alignment.
    """
    if not chunks:
        raise ValueError("Empty chunk list provided for embedding generation.")
        
    chunk_ids = set()
    for c in chunks:
        if not c.text.strip():
            raise ValueError(f"Chunk {c.chunk_id} has empty text.")
        if c.chunk_id in chunk_ids:
            raise ValueError(f"Duplicate chunk_id detected: {c.chunk_id}")
        chunk_ids.add(c.chunk_id)
        
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for generating embeddings.")
        
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    client = OpenAI(api_key=api_key)
    
    all_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.text for c in batch]
        
        try:
            response = client.embeddings.create(
                input=texts,
                model=model
            )
            
            # The API returns them in `.data` array, but they might not be sorted identically depending on the client payload.
            # We must map them securely using the `index` property returned by the OpenAI API response.
            sorted_data = sorted(response.data, key=lambda x: x.index)
            
            for item in sorted_data:
                all_embeddings.append(item.embedding)
                
        except Exception as e:
            logger.error(f"Failed to fetch embeddings for batch starting at index {i}: {e}")
            raise RuntimeError(f"OpenAI API embedding failure: {e}") from e
            
    matrix = np.array(all_embeddings, dtype=np.float32)
    
    if len(matrix.shape) != 2:
        raise ValueError(f"Expected 2D matrix, got shape {matrix.shape}")
        
    if matrix.shape[0] != len(chunks):
        raise ValueError(f"Metadata/Vector length mismatch: generated {matrix.shape[0]} vectors for {len(chunks)} chunks.")
        
    return matrix


def save_embeddings(embeddings: np.ndarray, chunks: List[DocumentChunk], storage_dir: Path | str) -> None:
    """
    Safely atomically persists the 2D numpy matrix alongside structured metadata.
    """
    directory = Path(storage_dir)
    directory.mkdir(parents=True, exist_ok=True)
    
    if embeddings.shape[0] != len(chunks):
        raise ValueError(f"Row count mismatch: {embeddings.shape[0]} vs metadata list length {len(chunks)}")
        
    chunk_ids = set()
    for c in chunks:
        if c.chunk_id in chunk_ids:
            raise ValueError(f"Duplicate chunk_id detected during save: {c.chunk_id}")
        chunk_ids.add(c.chunk_id)

    if not np.isfinite(embeddings).all():
        raise ValueError("Embedding matrix contains non-finite numeric values.")

    metadata_payload = [c.model_dump() for c in chunks]
    
    emb_path = directory / "embeddings.npy"
    emb_path_tmp = directory / "embeddings.tmp.npy"
    
    meta_path = directory / "metadata.json"
    meta_path_tmp = directory / "metadata.tmp.json"
    
    try:
        # Atomic Write Block
        np.save(str(emb_path_tmp), embeddings)
        
        with open(meta_path_tmp, "w", encoding="utf-8") as f:
            json.dump(metadata_payload, f, ensure_ascii=False, indent=2)
            
        # Swap safely
        os.replace(emb_path_tmp, emb_path)
        os.replace(meta_path_tmp, meta_path)
        
    except Exception as e:
        logger.error(f"Failed to persist embeddings to {storage_dir}: {e}")
        # Purge temporary files if stranded
        try:
            if emb_path_tmp.exists():
                emb_path_tmp.unlink()
            if meta_path_tmp.exists():
                meta_path_tmp.unlink()
        except:
            pass
        raise e
        
def load_embeddings(storage_dir: Path | str) -> tuple[np.ndarray, List[DocumentChunk]]:
    directory = Path(storage_dir)
    emb_path = directory / "embeddings.npy"
    meta_path = directory / "metadata.json"
    
    if not emb_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Storage files missing.")
        
    embeddings = np.load(str(emb_path))
    
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata_json = json.load(f)
        
    chunks = [DocumentChunk(**m) for m in metadata_json]
    
    if embeddings.shape[0] != len(chunks):
        raise ValueError(f"Corruption detected: Row count mismatch in storage ({embeddings.shape[0]} vs {len(chunks)})")
        
    return embeddings, chunks
