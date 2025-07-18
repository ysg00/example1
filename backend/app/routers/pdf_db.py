from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ..database import get_db
from ..models import PDF, PDFStatus
from ..schemas import (
    PDFUploadRequest, PDFUploadResponse, PDFConfirmRequest, 
    PDFConfirmResponse, PDFParseRequest, PDFParseResponse,
    ChatRequest, ChatResponse
)
from ..services.s3_service import S3Service
from ..services.opensearch_service import OpenSearchService
from ..services.chat_service import ChatService

router = APIRouter(tags=["pdf-upload"])

# Initialize services
s3_service = S3Service()
opensearch_service = OpenSearchService()
chat_service = ChatService()

@router.post("/upload-pdf", response_model=PDFUploadResponse)
async def upload_pdf(request: PDFUploadRequest, db: Session = Depends(get_db)):
    """Generate a pre-signed URL for uploading a PDF file and create a pending record"""
    try:
        # Check if PDF with same filename already exists
        existing_pdf = db.query(PDF).filter(PDF.filename == request.filename).first()
        
        if existing_pdf:
            # If PDF exists and is in PENDING status, return existing record
            if existing_pdf.status == PDFStatus.PENDING:
                presigned_url, s3_key = s3_service.generate_presigned_url(s3_key="", filename=request.filename)
                return PDFUploadResponse(
                    upload_url=presigned_url,
                    pdf_id=existing_pdf.id,
                    s3_key=existing_pdf.s3_key
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PDF with filename '{request.filename}' already exists with status {existing_pdf.status.value}"
                )
        
        # Generate pre-signed URL and S3 key
        presigned_url, s3_key = s3_service.generate_presigned_url(s3_key="", filename=request.filename)
        
        # Create PDF record in database with PENDING status
        pdf_record = PDF(
            filename=request.filename,
            s3_key=s3_key,
            status=PDFStatus.PENDING
        )
        
        db.add(pdf_record)
        db.commit()
        db.refresh(pdf_record)
        
        return PDFUploadResponse(
            upload_url=presigned_url,
            pdf_id=pdf_record.id,
            s3_key=s3_key
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating upload URL: {str(e)}"
        )

@router.post("/upload-pdf-confirm", response_model=PDFConfirmResponse)
async def confirm_pdf_upload(request: PDFConfirmRequest, db: Session = Depends(get_db)):
    """Confirm that PDF has been uploaded and update status to UPLOADED"""
    try:
        # Find PDF by ID
        pdf = db.query(PDF).filter(PDF.id == request.pdf_id).first()
        
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        if pdf.status != PDFStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF status is {pdf.status.value}, expected PENDING"
            )
        
        # Update status to UPLOADED
        pdf.status = PDFStatus.UPLOADED
        
        # Get file size from S3
        file_size = s3_service.get_file_size(pdf.s3_key)
        if file_size:
            pdf.file_size = file_size
        
        db.commit()
        
        return PDFConfirmResponse(
            message="PDF upload confirmed successfully",
            pdf_id=pdf.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming PDF upload: {str(e)}"
        )

@router.post("/parse-pdf", response_model=PDFParseResponse)
async def parse_pdf(request: PDFParseRequest, db: Session = Depends(get_db)):
    """Parse PDF and index content into OpenSearch"""
    try:
        # Find PDF by ID
        pdf = db.query(PDF).filter(PDF.id == request.pdf_id).first()
        
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        if pdf.status == PDFStatus.INDEXED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF is already indexed"
            )
        
        if pdf.status == PDFStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF has not been uploaded yet. Please upload and confirm first."
            )
        
        # Analyze and index PDF
        vector_index_id = opensearch_service.analyze_and_index_pdf(
            pdf_id=pdf.id,
            filename=pdf.filename,
            s3_key=pdf.s3_key
        )
        
        # Update PDF record
        pdf.status = PDFStatus.INDEXED
        pdf.vector_index_id = vector_index_id
        pdf.content_summary = "PDF content has been extracted, embedded, and indexed in vector database"
        
        db.commit()
        
        return PDFParseResponse(
            message="PDF parsed and indexed successfully",
            pdf_id=pdf.id,
            vector_index_id=vector_index_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing PDF: {str(e)}"
        )

@router.get("/list-pdfs")
async def list_pdfs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all PDFs with pagination"""
    try:
        pdfs = db.query(PDF).offset(skip).limit(limit).all()
        total_count = db.query(PDF).count()
        
        return {
            "pdfs": [
                {
                    "id": pdf.id,
                    "filename": pdf.filename,
                    "s3_key": pdf.s3_key,
                    "status": pdf.status.value,
                    "file_size": pdf.file_size,
                    "upload_date": pdf.upload_date.isoformat() if pdf.upload_date else None,
                    "vector_index_id": pdf.vector_index_id,
                    "content_summary": pdf.content_summary
                }
                for pdf in pdfs
            ],
            "total_count": total_count,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving PDFs: {str(e)}"
        )

@router.get("/pdfs")
async def get_all_pdfs(db: Session = Depends(get_db)):
    """Get all PDFs without pagination (simple list)"""
    try:
        pdfs = db.query(PDF).all()
        return {"pdfs": [
            {
                "id": pdf.id,
                "filename": pdf.filename,
                "s3_key": pdf.s3_key,
                "status": pdf.status.value,
                "file_size": pdf.file_size,
                "upload_date": pdf.upload_date.isoformat() if pdf.upload_date else None,
                "vector_index_id": pdf.vector_index_id,
                "content_summary": pdf.content_summary
            }
            for pdf in pdfs
        ]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving PDFs: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_pdfs(request: ChatRequest):
    """Chat with the AI assistant using RAG or direct LLM"""
    try:
        # Use the chat service to generate response
        response, sources = chat_service.chat(
            query=request.query,
            use_knowledge=request.use_knowledge
        )
        
        return ChatResponse(
            response=response,
            sources=sources if request.use_knowledge else None,
            use_knowledge=request.use_knowledge
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in chat: {str(e)}"
        ) 