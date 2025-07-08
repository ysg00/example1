from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ..database import get_db
from ..models import PDF, PDFStatus
from ..schemas import (
    PDFUploadRequest, PDFUploadResponse, PDFMetadata, 
    PDFListResponse, AnalysisResponse
)
from ..services.s3_service import S3Service
from ..services.opensearch_service import OpenSearchService

router = APIRouter(prefix="/api/v1", tags=["pdfs"])

# Initialize services
s3_service = S3Service()
opensearch_service = OpenSearchService()

@router.post("/upload_pdf", response_model=PDFUploadResponse)
async def upload_pdf(request: PDFUploadRequest, db: Session = Depends(get_db)):
    """Generate a pre-signed URL for uploading a PDF file"""
    try:
        # Generate pre-signed URL and S3 key
        presigned_url, s3_key = s3_service.generate_presigned_url(s3_key="", filename=request.filename)
        
        # Create PDF record in database with PRE_SIGNED status
        pdf_record = PDF(
            filename=request.filename,
            s3_key=s3_key,
            status=PDFStatus.PRE_SIGNED
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

@router.post("/mark_uploaded/{pdf_id}")
async def mark_uploaded(pdf_id: int, db: Session = Depends(get_db)):
    """Mark PDF as uploaded (called after successful S3 upload)"""
    try:
        pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
        
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # Update status to UPLOADED
        pdf.status = PDFStatus.UPLOADED
        
        # Get file size from S3
        file_size = s3_service.get_file_size(pdf.s3_key)
        if file_size:
            pdf.file_size = file_size
        
        db.commit()
        
        return {"message": "PDF marked as uploaded", "pdf_id": pdf_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking PDF as uploaded: {str(e)}"
        )

@router.get("/list_pdf", response_model=PDFListResponse)
async def list_pdfs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all uploaded PDFs"""
    try:
        pdfs = db.query(PDF).offset(skip).limit(limit).all()
        total_count = db.query(PDF).count()
        
        return PDFListResponse(
            pdfs=[PDFMetadata.from_orm(pdf) for pdf in pdfs],
            total_count=total_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving PDFs: {str(e)}"
        )

@router.get("/get_pdf/{pdf_id}", response_model=PDFMetadata)
async def get_pdf(pdf_id: int, db: Session = Depends(get_db)):
    """Get PDF metadata by ID"""
    try:
        pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
        
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        return PDFMetadata.from_orm(pdf)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving PDF: {str(e)}"
        )

@router.delete("/delete_pdf/{pdf_id}")
async def delete_pdf(pdf_id: int, db: Session = Depends(get_db)):
    """Delete PDF by ID"""
    try:
        pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
        
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # Delete from S3
        s3_service.delete_file(pdf.s3_key)
        
        # Delete from vector database if analyzed
        if pdf.vector_index_id:
            opensearch_service.delete_pdf_from_index(pdf.vector_index_id)
        
        # Delete from database
        db.delete(pdf)
        db.commit()
        
        return {"message": "PDF deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting PDF: {str(e)}"
        )

@router.post("/analyze_pdf/{pdf_id}", response_model=AnalysisResponse)
async def analyze_pdf(pdf_id: int, db: Session = Depends(get_db)):
    """Analyze PDF and store in vector database"""
    try:
        pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
        
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        if pdf.status == PDFStatus.PARSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF is already analyzed and parsed"
            )
        
        if pdf.status == PDFStatus.PRE_SIGNED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF has not been uploaded yet. Please upload the file first."
            )
        
        # Analyze and index PDF
        vector_index_id = opensearch_service.analyze_and_index_pdf(
            pdf_id=pdf.id,
            filename=pdf.filename,
            s3_key=pdf.s3_key
        )
        
        # Update PDF record
        pdf.status = PDFStatus.PARSED
        pdf.vector_index_id = vector_index_id
        pdf.content_summary = "PDF content has been extracted, embedded, and indexed in vector database"
        
        db.commit()
        
        return AnalysisResponse(
            message="PDF analyzed and indexed successfully",
            pdf_id=pdf.id,
            vector_index_id=vector_index_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing PDF: {str(e)}"
        ) 