import os
import sys
from pathlib import Path
from dotenv import load_dotenv

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from app.services.retrieval import RetrievalService
from app.services.embeddings import get_embedding_provider

def execute_query(service: RetrievalService, query: str):
    results = service.retrieve(query)
    return results

def format_result(rank: int, r, target_substrings: list[str]) -> str:
    marker = []
    for t in target_substrings:
        if t in r.text.upper() or t in r.text:
            marker.append(t)
    marker_str = f" <-- TARGET({','.join(marker)})" if marker else ""
    return f"   {rank}. score={r.similarity_score:.4f} chunk={r.chunk_id} doc={r.document} sec={r.section} text={r.text[:50]}...{marker_str}"

def main():
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # We enforce LocalProvider configuration for Phase 6 test mathematically.
    os.environ["EMBEDDING_PROVIDER"] = "local"
    
    storage_dir = project_root / "storage"
    service = RetrievalService(storage_dir)
    
    top_k = int(os.getenv("RETRIEVAL_TOP_K", "8"))
    min_score = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.60"))
    
    provider = get_embedding_provider()
    provider_name = type(provider).__name__
    model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Metadata for contradictions
    tests = [
        {
            "name": "ATTENDANCE TEST",
            "targets": ["75%", "60%"],
            "target_names": ["75% evidence", "60% evidence"],
            "queries": [
                "What is the minimum attendance requirement, and are there any medical exceptions?",
                "What percentage attendance must students maintain, and can medical reasons reduce it?",
                "Is there an attendance relaxation for students with medical certificates?"
            ]
        },
        {
            "name": "FEE DEADLINE TEST",
            "targets": ["July 15", "July 31"],
            "target_names": ["July 15 evidence", "July 31 evidence"],
            "queries": [
                "What is the deadline for paying university tuition fees?",
                "When is the tuition fee payment due?",
                "What is the last date for paying university fees?"
            ]
        },
        {
            "name": "HOSTEL CURFEW TEST",
            "targets": ["10:00 PM", "11:00 PM"],
            "target_names": ["10 PM evidence", "11 PM evidence"],
            "queries": [
                "What time must undergraduate hostel residents return to the hostel?",
                "When do undergraduate hostel students have to return?",
                "What is the hostel curfew for undergraduate residents?"
            ]
        }
    ]
    
    unanswerable = [
        "Does Medicaps University provide free laptops to all first-year students?"
    ]

    print("=" * 50)
    print("RETRIEVAL QUALITY VALIDATION")
    print("=" * 50)
    print(f"Embedding provider:\n{provider_name}\n")
    print(f"Embedding model:\n{model_name}\n")
    print(f"Stored chunks:\n{len(service.chunks)}\n")
    print(f"TOP_K:\n{top_k}\n")
    print(f"MIN_SCORE:\n{min_score}\n")
    
    metrics = []

    for test in tests:
        print("-" * 50)
        print(test["name"])
        print("-" * 50)
        
        all_found = True
        
        for query in test["queries"]:
            print(f"\nQuery:\n{query}")
            results = execute_query(service, query)
            
            found = {t: False for t in test["targets"]}
            
            for i, r in enumerate(results):
                print(format_result(i+1, r, test["targets"]))
                for t in test["targets"]:
                    if t in r.text.upper() or t in r.text:
                        found[t] = True
                    
            print()
            for idx, target in enumerate(test["targets"]):
                status = "FOUND" if found[target] else "MISSING"
                print(f"Expected {test['target_names'][idx]}: {status}")
                if not found[target]:
                    all_found = False
                    
        print(f"\nContradiction discoverable: {'YES' if all_found else 'NO'}")
        metrics.append(all_found)
        print()

    print("-" * 50)
    print("UNANSWERABLE TEST")
    print("-" * 50)
    unans_pass = True
    for query in unanswerable:
        print(f"\nQuery:\n{query}")
        results = execute_query(service, query)
        if len(results) > 0:
            print("WARNING: Unanswerable query returned results over threshold:")
            for i, r in enumerate(results):
                print(format_result(i+1, r, []))
            unans_pass = False
        else:
            print("No direct laptop policy found.")
            
    print("\n" + "=" * 50)
    print("FINAL RESULT SUMMARY (INTERNAL DRY-RUN)")
    print("=" * 50)
    print(f"Attendance contradiction discoverable: {'PASS' if metrics[0] else 'FAIL'}")
    print(f"Fee contradiction discoverable: {'PASS' if metrics[1] else 'FAIL'}")
    print(f"Hostel contradiction discoverable: {'PASS' if metrics[2] else 'FAIL'}")
    print(f"Unanswerable separation: {'PASS' if unans_pass else 'FAIL'}")
    print("=" * 50)

if __name__ == "__main__":
    main()
