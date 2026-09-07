import pytest
from app.models.schemas import DocumentRecord, DocumentChunk
from app.services.chunking import chunk_record, chunk_corpus, estimate_tokens, split_sentences, generate_chunk_id

def test_estimate_tokens():
    text = "This is a simple count."
    assert estimate_tokens(text) == 5

def test_split_sentences():
    text = "Hello there. Mr. Smith went to Washington! Did he? Yes, e.g. today."
    sentences = split_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "Hello there."
    assert sentences[1] == "Mr. Smith went to Washington!"
    assert sentences[2] == "Did he?"
    assert sentences[3] == "Yes, e.g. today."

def test_small_section_remains_intact():
    record = DocumentRecord(
        document="test.pdf",
        file_type="pdf",
        text="This is a small rule.",
        section="Rule 1",
        page=1
    )
    chunks = chunk_record(record, max_tokens=600)
    assert len(chunks) == 1
    assert chunks[0].text == "This is a small rule."
    assert chunks[0].section == "Rule 1"
    assert chunks[0].page == 1

def test_large_section_is_split():
    # Construct a string large enough to breach 50 tokens (since we will set max_tokens=50 for test)
    text = " ".join([f"Word{i}" for i in range(100)]) + ". " + " ".join([f"Word{i}" for i in range(30)]) + "."
    record = DocumentRecord(
        document="test.md",
        file_type="markdown",
        text=text,
        section="Big Rule"
    )
    chunks = chunk_record(record, max_tokens=50) # artificially lower max_tokens
    
    assert len(chunks) > 1
    assert chunks[0].section == "Big Rule"
    assert chunks[1].section == "Big Rule"
    
def test_metadata_preservation():
    record = DocumentRecord(
        document="important.pdf",
        file_type="pdf",
        text="A rule that means a lot.",
        section="Section 4.1",
        page=4
    )
    chunks = chunk_record(record)
    assert chunks[0].document == "important.pdf"
    assert chunks[0].file_type == "pdf"
    assert chunks[0].section == "Section 4.1"
    assert chunks[0].page == 4

def test_chunk_ids_deterministic_and_unique():
    record = DocumentRecord(
        document="doc.md",
        file_type="markdown",
        text="Hello world. " * 300, # Large enough to split if max_tokens=50
        section="A"
    )
    chunks = chunk_record(record, max_tokens=50)
    
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs must be unique within same document."
    
    # Rerunning should yield exact same IDs
    chunks2 = chunk_record(record, max_tokens=50)
    ids2 = [c.chunk_id for c in chunks2]
    
def test_adjacent_merging():
    r1 = DocumentRecord(document="test.md", file_type="md", text="Line 1.", section="Sec1")
    r2 = DocumentRecord(document="test.md", file_type="md", text="Line 2.", section="Sec1")
    r3 = DocumentRecord(document="test.md", file_type="md", text="Line 3.", section="Sec2") 
    
    chunks = chunk_corpus([r1, r2, r3], min_tokens=100, max_tokens=200)
    assert len(chunks) == 2
    assert chunks[0].text == "Line 1.\n\nLine 2."
    assert chunks[1].text == "Line 3."

def test_non_contiguous_duplicates():
    r1 = DocumentRecord(document="test.md", file_type="md", text="Header", section="H")
    r2 = DocumentRecord(document="test.md", file_type="md", text="Different", section="D")
    r3 = DocumentRecord(document="test.md", file_type="md", text="Header", section="H")
    
    chunks = chunk_corpus([r1, r2, r3], min_tokens=100, max_tokens=200)
    assert len(chunks) == 3
    
    # 0 and 2 are identical structurally but must yield explicit distinct IDs natively
    assert chunks[0].text == "Header"
    assert chunks[2].text == "Header"
    assert chunks[0].chunk_id != chunks[2].chunk_id  
    # Non-matching pages
    records_page = [
        DocumentRecord(document="d1.pdf", file_type="pdf", text="Row A", section="Sec 1", page=1),
        DocumentRecord(document="d1.pdf", file_type="pdf", text="Row B", section="Sec 1", page=2)
    ]
    chunks_page = chunk_corpus(records_page)
    assert len(chunks_page) == 2
    
    # Non-matching sections
    records_sec = [
        DocumentRecord(document="d1.pdf", file_type="pdf", text="Row A", section="Sec 1", page=1),
        DocumentRecord(document="d1.pdf", file_type="pdf", text="Row B", section="Sec 2", page=1)
    ]
    chunks_sec = chunk_corpus(records_sec)
    assert len(chunks_sec) == 2
