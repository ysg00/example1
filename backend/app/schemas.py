from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .models import PDFStatus

class PDFUploadRequest(BaseModel):
    filename: str

class PDFUploadResponse(BaseModel):
    upload_url: str
    pdf_id: int
    s3_key: str

class PDFConfirmRequest(BaseModel):
    pdf_id: int

class PDFConfirmResponse(BaseModel):
    message: str
    pdf_id: int

class PDFParseRequest(BaseModel):
    pdf_id: int

class PDFParseResponse(BaseModel):
    message: str
    pdf_id: int
    vector_index_id: str

class PDFMetadata(BaseModel):
    id: int
    filename: str
    s3_key: str
    file_size: Optional[int]
    upload_date: datetime
    status: PDFStatus
    vector_index_id: Optional[str]
    content_summary: Optional[str]
    
    class Config:
        from_attributes = True

class PDFListResponse(BaseModel):
    pdfs: list[PDFMetadata]
    total_count: int

class AnalysisResponse(BaseModel):
    message: str
    pdf_id: int
    vector_index_id: str 

class ChatRequest(BaseModel):
    query: str
    use_knowledge: bool = True

class ChatResponse(BaseModel):
    response: str
    sources: Optional[list[str]] = None
    use_knowledge: bool 