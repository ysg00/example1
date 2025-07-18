from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .database import engine
from .models import Base

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️  Database connection failed: {e}")
    print("📝 Running in development mode without database")

# Create FastAPI app
app = FastAPI(
    title="PDF Management API",
    description="A FastAPI application for managing PDF uploads, storage, and analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from .routers import pdf_db
app.include_router(pdf_db.router)

@app.get("/")
async def root():
    return {
        "message": "PDF Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 