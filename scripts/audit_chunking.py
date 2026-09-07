import sys
import os
from pathlib import Path
from collections import defaultdict
import random

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.ingestion import ingest_corpus
from app.services.chunking import chunk_corpus, estimate_tokens

DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"

def main():
    records = list(ingest_corpus(DATA_DIR))
    chunks = chunk_corpus(records)
    
    token_counts = []
    
    thresholds = {50: 0, 100: 0, 200: 0, 350: 0}
    total_chunks = len(chunks)
    
    for c in chunks:
        toks = estimate_tokens(c.text)
        token_counts.append(toks)
        for t in thresholds.keys():
            if toks < t:
                thresholds[t] += 1
                
    print("=== CHUNK SIZE DISTRIBUTION ===")
    print(f"Total Chunks: {total_chunks}")
    for t in sorted(thresholds.keys()):
        pct = (thresholds[t] / total_chunks) * 100 if total_chunks else 0
        print(f"Below {t} tokens: {thresholds[t]} ({pct:.2f}%)")
        
    print("\n=== REPRESENTATIVE EXAMPLES ===")
    # Find a very small chunk < 20 tokens
    small_chunk = next((c for c in chunks if estimate_tokens(c.text) < 20), None)
    if small_chunk:
        print(f"GOOD SMALL CHUNK (Tokens: {estimate_tokens(small_chunk.text)})")
        print(f"Doc: {small_chunk.document}, Sec: {small_chunk.section}")
        print(f"Text: '{small_chunk.text}'\n")
        
    # Analyze adjacent fragment merging
    # Let's inspect sequentially
    adjacency_count = 0
    adj_example = None
    
    for i in range(len(chunks) - 1):
        c1 = chunks[i]
        c2 = chunks[i+1]
        
        if c1.document == c2.document and c1.section == c2.section and c1.page == c2.page:
            adjacency_count += 1
            if not adj_example and estimate_tokens(c1.text) < 50:
                adj_example = (c1, c2)
                
    print(f"Count of contiguous adjacent chunks in same logical document+section: {adjacency_count}")
    if adj_example:
        print(f"\nADJACENT FRAGMENTATION EXAMPLE:")
        print(f"Doc: {adj_example[0].document}, Sec: {adj_example[0].section}, Page: {adj_example[0].page}")
        print(f"Snippet 1 (Tokens: {estimate_tokens(adj_example[0].text)}): '{adj_example[0].text[:100]}...'")
        print(f"Snippet 2 (Tokens: {estimate_tokens(adj_example[1].text)}): '{adj_example[1].text[:100]}...'")
        
    print("\n=== CRITICAL CONTRADICTION AUDIT ===")
    targets = {
        "75% attendance rule": "75%",
        "60% attendance rule": "60%",
        "July 15 deadline": "July 15",
        "July 31 deadline": "July 31",
        "10:00 PM curfew": "10:00 PM",
        "11:00 PM curfew": "11:00 PM"
    }
    
    for target_name, substring in targets.items():
        found = False
        print(f"\n--- {target_name} ---")
        for c in chunks:
            if substring in c.text:
                found = True
                print(f"chunk_id: {c.chunk_id}")
                print(f"document: {c.document}")
                print(f"section: {c.section}")
                print(f"page: {c.page}")
                print(f"estimated token count: {estimate_tokens(c.text)}")
                print(f"Text excerpt: {c.text}")
                break
        if not found:
            print("NOT FOUND")
            
if __name__ == "__main__":
    main()
