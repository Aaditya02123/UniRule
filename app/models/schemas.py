from pydantic import BaseModel, ConfigDict
from typing import Optional

class DocumentRecord(BaseModel):
    document: str          
    file_type: str         
    text: str              
    section: Optional[str] = None
    page: Optional[int] = None
    
    model_config = ConfigDict(frozen=True)


class DocumentChunk(BaseModel):
    chunk_id: str
    document: str
    file_type: str
    text: str
    section: Optional[str] = None
    page: Optional[int] = None
    
    model_config = ConfigDict(frozen=True)

class RetrievalResult(BaseModel):
    chunk_id: str
    document: str
    file_type: str
    text: str
    section: Optional[str] = None
    page: Optional[int] = None
    similarity_score: float
    
    model_config = ConfigDict(frozen=True)
