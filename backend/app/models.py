from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum
from sqlalchemy.sql import func
from .database import Base
import enum

class PDFStatus(enum.Enum):
    PRE_SIGNED = "PRE_SIGNED"
    UPLOADED = "UPLOADED"
    PARSED = "PARSED"

class PDF(Base):
    __tablename__ = "pdfs"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    s3_key = Column(String, nullable=False, unique=True)
    file_size = Column(Integer)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(PDFStatus), default=PDFStatus.PRE_SIGNED)
    vector_index_id = Column(String, nullable=True)
    content_summary = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<PDF(id={self.id}, filename='{self.filename}', s3_key='{self.s3_key}', status='{self.status.value}')>" 