import os
import sys
import logging
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.ingestion import ingest_corpus
from app.services.chunking import chunk_corpus
from app.services.embeddings import generate_embeddings, save_embeddings, load_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"

def main():
    print("=== PHASE 5: EMBEDDING VERIFICATION ===")
    
    root_dir = Path(__file__).resolve().parent.parent
    try:
        from dotenv import load_dotenv
        load_dotenv(root_dir / ".env")
    except ImportError:
        pass
    
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[SKIPPED]")
        print("OPENAI_API_KEY is not set.")
        print("Production embedding generation was not executed to prevent unintended billing.")
        print("Set OPENAI_API_KEY to run the real OpenAI API payload.")
        return
        
    print("\n1. Ingesting Corpus...")
    records = list(ingest_corpus(DATA_DIR))
    
    print("\n2. Chunking Corpus...")
    chunks = chunk_corpus(records)
    print(f"Chunks generated: {len(chunks)}")
    
    print("\n3. Generating Embeddings via OpenAI (Real API Call)...")
    try:
        embeddings_matrix = generate_embeddings(chunks)
        print(f"Embeddings generated successfully. Matrix shape: {embeddings_matrix.shape}")
        
        print("\n4. Persisting Embeddings...")
        save_embeddings(embeddings_matrix, chunks, STORAGE_DIR)
        print(f"Persisted to {STORAGE_DIR}")
        
        print("\n5. Validating Reload...")
        loaded_embs, loaded_chunks = load_embeddings(STORAGE_DIR)
        print(f"Reload shape: {loaded_embs.shape}")
        print(f"Reload chunk count: {len(loaded_chunks)}")
        
        # Verify alignment
        if loaded_embs.shape[0] != len(loaded_chunks):
            print("ERROR: Reload mismatch!")
            sys.exit(1)
            
        if np.allclose(embeddings_matrix, loaded_embs):
            print("Mathematical bounds match perfectly.")
        else:
            print("ERROR: Math boundary mismatch after load!")
            sys.exit(1)
            
        print("\nVerification completed successfully.")
        
    except Exception as e:
        logger.exception("Failed during verification pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    main()
