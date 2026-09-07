import sys
import os
from pathlib import Path
from collections import defaultdict

# Add app to path securely
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.ingestion import ingest_file

DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"

def main():
    supported_extensions = {".pdf", ".md", ".csv"}
    
    discovered_supported = []
    ignored_unsupported = []
    failed_files = []
    success_files = []
    
    total_records = 0
    records_per_file = {}
    pdf_pages = defaultdict(int)
    
    # 1. Discover 
    for f in DATA_DIR.iterdir():
        if not f.is_file(): continue
        
        if f.suffix in supported_extensions and not f.name.startswith('.'):
            discovered_supported.append(f)
        else:
            ignored_unsupported.append(f)
            
    discovered_supported = sorted(discovered_supported)
    
    print("=== CORPUS INGESTION VERIFICATION ===")
    print(f"Supported Files Discovered: {len(discovered_supported)}")
    for f in discovered_supported:
        print(f" - {f.name}")
        
    print(f"\nUnsupported Files Ignored: {len(ignored_unsupported)}")
    for f in ignored_unsupported:
        print(f" - {f.name}")
        
    # 2. Process
    print("\n=== PROCESSING ===")
    for f in discovered_supported:
        try:
            records = ingest_file(f)
            rec_count = len(records)
            records_per_file[f.name] = rec_count
            total_records += rec_count
            success_files.append(f.name)
            
            if f.suffix == '.pdf':
                # calculate unique pages observed via records
                observed_pages = set(r.page for r in records if r.page is not None)
                pdf_pages[f.name] = len(observed_pages)
                
            print(f"Ingested {f.name} -> {rec_count} records.")
        except Exception as e:
            failed_files.append(f.name)
            print(f"FAILED {f.name}: {e}")
            
    # 3. Report Totals
    print("\n=== SUMMARY ===")
    print(f"Files Successfully Ingested: {len(success_files)}")
    print(f"Files Failed: {len(failed_files)}")
    print(f"Total Normalized Records: {total_records}")
    print("\nRecords per source file:")
    for f_name, count in records_per_file.items():
        if f_name.endswith('.pdf'):
            pages = pdf_pages.get(f_name, 0)
            print(f"  {f_name} → {count} records | {pages} PDF pages evaluated")
        else:
            print(f"  {f_name} → {count} records")

if __name__ == "__main__":
    main()
