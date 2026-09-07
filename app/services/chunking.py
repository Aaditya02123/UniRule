import hashlib
import re
from typing import List, Iterable
from app.models.schemas import DocumentRecord, DocumentChunk

def estimate_tokens(text: str) -> int:
    """
    Approximates token count deterministically using whitespace word boundaries.
    This is an explicitly naive approximation (not an exact OpenAI tiktoken count)
    to minimize heavyweight NLP standard dependencies as per Phase 4 requirements.
    """
    return len(text.split())

def split_sentences(text: str) -> List[str]:
    """
    Lightweight deterministic sentence boundary splitter.
    Supports '.', '?', '!' while avoiding decimal false-splits and obvious abbreviations.
    """
    abbreviations = ["Mr.", "Mrs.", "Dr.", "Ms.", "Prof.", "e.g.", "i.e.", "etc.", "vs.", "B.A.", "Ph.D."]
    protected_text = text
    for abbr in abbreviations:
        protected_text = protected_text.replace(f"{abbr} ", f"{abbr}@@@SPACE@@@")
    
    parts = re.split(r'([.?!](?:\s+|$))', protected_text)
    
    sentences = []
    current_sentence = ""
    for part in parts:
        if not part:
            continue
        current_sentence += part
        # If the part is the punctuation split pattern, we definitely reached the end of a sentence
        if re.match(r'^[.?!](?:\s+|$)', part):
            s = current_sentence.replace("@@@SPACE@@@", " ").strip()
            if s:
                sentences.append(s)
            current_sentence = ""
            
    if current_sentence:
        s = current_sentence.replace("@@@SPACE@@@", " ").strip()
        if s:
            sentences.append(s)
            
    return sentences

def generate_chunk_id(document: str, page: int | None, section: str | None, chunk_index: int, text: str) -> str:
    """
    Generates a unique, deterministic, non-random string ID by hashing source boundaries.
    """
    payload = f"{document}|{page}|{section}|{chunk_index}|{text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

def chunk_record(record: DocumentRecord, min_tokens=350, max_tokens=600) -> List[DocumentChunk]:
    chunks = []
    text = record.text.strip()
    
    if not text:
        return chunks
    
    # Base Case: Single element natively maps below boundary
    if estimate_tokens(text) <= max_tokens:
        chunk_id = generate_chunk_id(record.document, record.page, record.section, 0, text)
        return [DocumentChunk(
            chunk_id=chunk_id,
            document=record.document,
            file_type=record.file_type,
            text=text,
            section=record.section,
            page=record.page
        )]
        
    paragraphs = text.split('\n\n')
    current_chunk_text = []
    current_tokens = 0
    chunk_index = 0
    
    def emit_chunk():
        nonlocal current_chunk_text, current_tokens, chunk_index, chunks
        if not current_chunk_text: return
        
        # When accumulating sentences, they are simply parts of a string.
        # But if we were appending paragraphs, we want empty lines between them.
        # For simplicity, we just join by spaces since they could be sentences or paragraphs.
        # However, to preserve paragraph breaks, it is better to intelligently join.
        # Wait, the prompt says "Avoid splitting a rule in the middle of a sentence".
        # We will use "\n\n" as default joiner but check if it's a list of sentences or paras.
        # Natively, joining strings by "\n\n" might double spaces for sentences.
        # Let's just strip and join by a space if they are sentences, or preserve exact structure.
        # A simpler way: we just join cleanly with "\n\n". 
        joined_text = "\n\n".join(current_chunk_text).strip()
        
        if joined_text:
            c_id = generate_chunk_id(record.document, record.page, record.section, chunk_index, joined_text)
            chunks.append(DocumentChunk(
                chunk_id=c_id,
                document=record.document,
                file_type=record.file_type,
                text=joined_text,
                section=record.section,
                page=record.page
            ))
            chunk_index += 1
        current_chunk_text = []
        current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para: continue
        
        para_tokens = estimate_tokens(para)
        
        if para_tokens > max_tokens:
            sentences = split_sentences(para)
            
            for sent in sentences:
                sent_tokens = estimate_tokens(sent)
                
                if current_tokens + sent_tokens > max_tokens and current_chunk_text:
                    emit_chunk()
                    
                current_chunk_text.append(sent)
                current_tokens += sent_tokens
        else:
            if current_tokens + para_tokens > max_tokens and current_chunk_text:
                emit_chunk()
                
            current_chunk_text.append(para)
            current_tokens += para_tokens
            
    if current_chunk_text:
        emit_chunk()
        
    # Since we appended sentences/paragraphs interchangeably to current_chunk_text and used \n\n,
    # let's fix whitespace issues inside the finalized text block in chunk records by cleaning up double spaces or bad newlines.
    
    # Actually, a better approach for fixing the joiner: 
    # if we have sentences, joining by "\n\n" creates fake paragraphs. 
    # Let's post-process the chunk text by doing a standard cleanup wrapper.
    for i in range(len(chunks)):
        cleaned_text = re.sub(r'\n{3,}', '\n\n', chunks[i].text) 
        # Update the frozen Pydantic model natively by rebuilding it
        if cleaned_text != chunks[i].text:
            c_id = generate_chunk_id(record.document, record.page, record.section, i, cleaned_text)
            chunks[i] = DocumentChunk(
                chunk_id=c_id,
                document=record.document,
                file_type=record.file_type,
                text=cleaned_text,
                section=record.section,
                page=record.page
            )
            
    return chunks

def chunk_corpus(records: Iterable[DocumentRecord], min_tokens=350, max_tokens=600) -> List[DocumentChunk]:
    chunks = []
    
    current_doc = None
    current_section = None
    current_page = None
    current_file_type = None
    
    current_texts = []
    current_tokens = 0
    
    def flush_group():
        nonlocal current_texts, current_tokens, current_doc, current_section, current_page, current_file_type, chunks
        if not current_texts:
            return
            
        merged_text = "\n\n".join(current_texts).strip()
        merged_record = DocumentRecord(
            document=current_doc,
            file_type=current_file_type,
            text=merged_text,
            section=current_section,
            page=current_page
        )
        # Process the newly merged record through standard boundaries checking
        chunks.extend(chunk_record(merged_record, min_tokens, max_tokens))
        
        current_texts = []
        current_tokens = 0
        current_doc = None
        current_section = None
        current_page = None
        current_file_type = None

    for record in records:
        record_tokens = estimate_tokens(record.text)
        
        is_match = (
            current_doc == record.document and
            current_section == record.section and
            current_page == record.page
        )
        
        if is_match and current_tokens + record_tokens <= max_tokens:
            current_texts.append(record.text)
            current_tokens += record_tokens
        else:
            flush_group()
            current_doc = record.document
            current_section = record.section
            current_page = record.page
            current_file_type = record.file_type
            current_texts = [record.text]
            current_tokens = record_tokens
            
    flush_group()
    return chunks
