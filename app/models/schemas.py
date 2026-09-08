from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict
from enum import Enum

class Classification(str, Enum):
    ANSWERED = "ANSWERED"
    CONFLICT = "CONFLICT"
    NOT_COVERED = "NOT_COVERED"

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

class EvidenceAnalysisResult(BaseModel):
    classification: Classification
    supporting_evidence: List[RetrievalResult] = Field(default_factory=list)
    conflict_groups: Dict[str, List[RetrievalResult]] = Field(default_factory=dict)
    
    model_config = ConfigDict(frozen=True)

class GeneratedAnswer(BaseModel):
    classification: Classification
    answer: str
    evidence: List[RetrievalResult] = Field(default_factory=list)
    
    model_config = ConfigDict(frozen=True)
