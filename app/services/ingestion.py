from pathlib import Path
import csv
import re
import logging
import fitz
from typing import List, Generator

from app.models.schemas import DocumentRecord

logger = logging.getLogger(__name__)

def ingest_pdf(filepath: Path) -> List[DocumentRecord]:
    filename = filepath.name
    results = []
    
    try:
        doc = fitz.open(str(filepath))
    except Exception as e:
        logger.error(f"Failed to open PDF {filepath}: {e}")
        return []
        
    current_section = None
    
    for page_num_0, page in enumerate(doc):
        page_num = page_num_0 + 1
        text = page.get_text()
        if not text.strip():
            continue
            
        lines = text.split('\n')
        current_text = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Deterministic section detection relying strictly on exact corpus patterns
            is_section = False
            if re.match(r'^Section \d+:', line_stripped):
                is_section = True
            elif "Medicaps University" in line_stripped and ("Regulations" in line_stripped or "Handbook" in line_stripped):
                is_section = True
                
            if is_section:
                # Flush existing accumulated text on this page to the previous section
                if current_text:
                    parsed_text = "\n".join(current_text).strip()
                    if parsed_text:
                        results.append(DocumentRecord(
                            document=filename,
                            file_type="pdf",
                            text=parsed_text,
                            section=current_section,
                            page=page_num
                        ))
                    current_text = []
                current_section = line_stripped
                
            # Accumulate this line (including the header itself seamlessly)
            current_text.append(line_stripped)
            
        # Flush end of page boundary
        if current_text:
            parsed_text = "\n".join(current_text).strip()
            if parsed_text:
                results.append(DocumentRecord(
                    document=filename,
                    file_type="pdf",
                    text=parsed_text,
                    section=current_section,
                    page=page_num
                ))
                
    return results

def ingest_markdown(filepath: Path) -> List[DocumentRecord]:
    filename = filepath.name
    results = []
    current_section = None
    current_text = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(('# ', '## ', '### ', '#### ')):
                    if current_text:
                        parsed_text = "\n".join(current_text).strip()
                        if parsed_text:
                            results.append(DocumentRecord(
                                document=filename,
                                file_type="markdown",
                                text=parsed_text,
                                section=current_section,
                                page=None
                            ))
                        current_text = []
                    current_section = line.strip("# \n")
                current_text.append(line.rstrip('\n'))
                
        if current_text:
            parsed_text = "\n".join(current_text).strip()
            if parsed_text:
                results.append(DocumentRecord(
                    document=filename,
                    file_type="markdown",
                    text=parsed_text,
                    section=current_section,
                    page=None
                ))
    except Exception as e:
        logger.error(f"Failed to ingest markdown {filepath}: {e}")
        
    return results

def ingest_csv(filepath: Path) -> List[DocumentRecord]:
    filename = filepath.name
    results = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pairs = []
                for k, v in row.items():
                    val = str(v).strip()
                    if val:
                        pairs.append(f"{k}: {val}")
                
                if not pairs:
                    continue
                    
                text = ". ".join(pairs) + "."
                section = row.get("Category", None)
                if not section or not str(section).strip():
                    section = None
                    
                results.append(DocumentRecord(
                    document=filename,
                    file_type="csv",
                    text=text,
                    section=section,
                    page=None
                ))
    except Exception as e:
        logger.error(f"Failed to ingest CSV {filepath}: {e}")
        
    return results

def ingest_file(filepath: Path) -> List[DocumentRecord]:
    if filepath.name.endswith('.pdf'):
        return ingest_pdf(filepath)
    elif filepath.name.endswith('.md'):
        return ingest_markdown(filepath)
    elif filepath.name.endswith('.csv'):
        return ingest_csv(filepath)
    else:
        logger.warning(f"Unsupported file type: {filepath.name}")
        return []

def ingest_corpus(data_dir: str | Path) -> Generator[DocumentRecord, None, None]:
    """
    Deterministically ingests all supported files from the data directory.
    Ignores strict subsets like contradictions.json or .keep
    """
    path = Path(data_dir)
    if not path.exists() or not path.is_dir():
        logger.error(f"Data directory {data_dir} not found.")
        return
        
    # Discover and sort deterministically
    files = sorted([f for f in path.iterdir() if f.is_file()])
    
    for f in files:
        # Ignore metadata and unstated files
        if f.name == "contradictions.json" or f.name.startswith("."):
            continue
            
        records = ingest_file(f)
        for record in records:
            yield record
