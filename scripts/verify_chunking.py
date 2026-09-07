import sys
import os
from pathlib import Path
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.ingestion import ingest_corpus
from app.services.chunking import chunk_record, estimate_tokens, chunk_corpus

DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"

def main():
    print("=== CORPUS CHUNKING VERIFICATION ===")
    records = list(ingest_corpus(DATA_DIR))
    
    all_chunks = chunk_corpus(records)
    
    # Metrics
    chunks_per_doc = defaultdict(int)
    record_split_count = 0
    token_counts = []
    
    for c in all_chunks:
        chunks_per_doc[c.document] += 1
        token_counts.append(estimate_tokens(c.text))
            
    num_chunks = len(all_chunks)
    min_tokens = min(token_counts) if token_counts else 0
    max_tokens = max(token_counts) if token_counts else 0
    avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
    
    in_range = len([t for t in token_counts if 350 <= t <= 600])
    small_chunks = len([t for t in token_counts if t < 350])
    large_chunks = len([t for t in token_counts if t > 600])
    
    print(f"Total DocumentRecords received: {len(records)}")
    print(f"Total Chunks generated: {num_chunks}")
    
    print("\nChunks per document:")
    for doc, count in sorted(chunks_per_doc.items()):
        print(f"  {doc}: {count} chunks")
        
    print("\nChunk Metrics:")
    print(f"  Minimum estimated token count: {min_tokens}")
    print(f"  Maximum estimated token count: {max_tokens}")
    print(f"  Average estimated token count: {avg_tokens:.2f}")
    
    print(f"\nTarget Range Compliance:")
    print(f"  Chunks in target range (350-600): {in_range}")
    print(f"  Intentionally smaller chunks (<350): {small_chunks}")
    print(f"  Records requiring splitting: {record_split_count}")
    print(f"  Unusually large chunks (>600): {large_chunks}")
    
    print("\n=== CONTRADICTION CHUNK MAPPING VERIFICATION ===")
    targets = {
        "75% attendance rule": "75%",
        "60% attendance rule": "60%",
        "July 15 deadline": "July 15",
        "July 31 deadline": "July 31",
        "10:00 PM curfew": "10:00 PM",
        "11:00 PM curfew": "11:00 PM"
    }
    
    found_targets = {k: False for k in targets}
    
    for c in all_chunks:
        for target_name, substring in targets.items():
            if substring in c.text:
                found_targets[target_name] = True
                print(f"FOUND: {target_name}")
                print(f"   -> chunk_id: {c.chunk_id}")
                print(f"   -> document: {c.document}, section: {c.section}, page: {c.page}")

if __name__ == "__main__":
    main()
