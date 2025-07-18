#!/usr/bin/env python3

from app.database import engine
from app.models import Base

print("Testing database connection...")

try:
    # Test connection
    with engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
    
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    import traceback
    traceback.print_exc() 