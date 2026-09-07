from pydantic import BaseModel
from typing import Optional

class DocumentRecord(BaseModel):
    document: str          
    file_type: str         
    text: str              
    section: Optional[str] = None
    page: Optional[int] = None
    
    class Config:
        frozen = True
