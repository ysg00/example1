from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:12341234@localhost/pdfs")

# Explicitly use PyMySQL
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    connect_args={"charset": "utf8mb4"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 