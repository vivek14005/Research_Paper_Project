from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class PaperBase(BaseModel):
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    publication_date: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    keywords: List[str] = []

class PaperCreate(PaperBase):
    filename: str
    file_path: str
    user_id: str

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    
class PaperInDB(PaperBase):
    id: str = Field(..., alias="_id")
    user_id: str
    filename: str
    file_path: str
    status: str = "processing" # processing, completed, error
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Paper(PaperInDB):
    pass

class PaperChunk(BaseModel):
    id: str
    paper_id: str
    content: str
    page_number: int
    metadata: Dict[str, Any] = {}
