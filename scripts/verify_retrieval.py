import os
import sys
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.retrieval import RetrievalService

logging.basicConfig(level=logging.ERROR)

def main():
    print("=== PHASE 6: RETRIEVAL VERIFICATION ===\n")
    
    # Safely load the root .env dynamically regardless of current working directory
    root_dir = Path(__file__).resolve().parent.parent
    try:
        from dotenv import load_dotenv
        load_dotenv(root_dir / ".env")
    except ImportError:
        pass
    
    if not os.getenv("OPENAI_API_KEY"):
        print("[SKIPPED]")
        print("OPENAI_API_KEY is not set.")
        print("Production retrieval using embeddings API was not executed computationally.")
        return
        
    storage_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "storage"
    
    if not (storage_dir / "embeddings.npy").exists():
        print("[ERROR]")
        print("Embeddings do not exist. Please run verify_embeddings.py first.")
        return
        
    print("Initializing Service...")
    service = RetrievalService(storage_dir)
    print("WARNING: This script performs REAL OpenAI API calls to test retrieval bounds.\n")
    
    test_queries = [
        "What attendance percentage is required to sit for examinations?",
        "When is the tuition fee deadline?",
        "What time must undergraduate hostel residents return?",
        "Does Medicaps University provide free laptops to every first-year student?"
    ]
    
    for q in test_queries:
        print(f"\n--- QUERY: {q} ---")
        try:
            results = service.retrieve(q)
            if not results:
                print("Results: NO EVIDENCE MET THRESHOLD.")
            else:
                for idx, r in enumerate(results):
                    print(f"[{idx+1}] Score: {r.similarity_score:.4f} | Chunk: {r.chunk_id}")
                    print(f"    Source: {r.document} - {r.section}")
                    snippet = r.text[:80].replace('\n', ' ')
                    print(f"    Preview: {snippet}...")
        except Exception as e:
            print(f"ERROR: {e}")
            
    print("\nRetrieval Verification complete.")

if __name__ == "__main__":
    main()
