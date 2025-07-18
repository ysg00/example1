from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum
from sqlalchemy.sql import func
from .database import Base
import enum

class PDFStatus(enum.Enum):
    PENDING = "PENDING"
    UPLOADED = "UPLOADED"
    INDEXED = "INDEXED"

class PDF(Base):
    __tablename__ = "pdfs"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    file_size = Column(Integer)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(PDFStatus), default=PDFStatus.PENDING)
    vector_index_id = Column(String(255), nullable=True)
    content_summary = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<PDF(id={self.id}, filename='{self.filename}', s3_key='{self.s3_key}', status='{self.status.value}')>" 