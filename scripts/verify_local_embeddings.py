import os
import sys
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

# Ensure app is in path explicitly
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from app.services.ingestion import ingest_corpus
from app.services.chunking import chunk_corpus
from app.services.embeddings import get_embedding_provider, save_embeddings

def main():
    # Load env safely
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # Force configurations strictly validating local mapping bounds explicitly
    os.environ["EMBEDDING_PROVIDER"] = "local"
    
    print("=== LOCAL EMBEDDING PIPELINE VERIFICATION ===")
    
    print("Initializing Local Provider (SentenceTransformer)...")
    print("Note: If the model has not been fetched before, this will actively download sizes ~80MB.")
    provider = get_embedding_provider()
    
    data_dir = project_root / "data"
    storage_dir = project_root / "storage"
    
    print(f"\nIngesting corpus natively from {data_dir}...")
    records = list(ingest_corpus(data_dir))
    print(f"Loaded {len(records)} raw DocumentRecord rows.")
    
    print("\nExecuting deterministic structure-aware chunking...")
    chunks = chunk_corpus(records)
    print(f"Generated exactly {len(chunks)} DocumentChunks.")
    
    print("\nGenerating deterministic local sentence-transformer vector encodings...")
    embeddings_matrix = provider.generate_embeddings(chunks, batch_size=100)
    
    print(f"Local Embedding Matrix mathematical bounds: {embeddings_matrix.shape}")
    
    if np.isfinite(embeddings_matrix).all():
        print("Validity Check passed: All vector numbers are strictly mathematically finite.")
    else:
        raise ValueError("Matrix integrity failure - Non-finite numbers detected.")
        
    print(f"\nPersisting {embeddings_matrix.shape} atomic index into storage bounds: {storage_dir}")
    save_embeddings(embeddings_matrix, chunks, storage_dir)
    
    print("\nSUCCESS: The standalone Local Embedding infrastructure produced structural bounds fully bypassing OpenAI natively.")

if __name__ == "__main__":
    main()
