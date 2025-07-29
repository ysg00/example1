from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """
    Get database URL based on environment.
    For local development: uses .env file or default localhost
    For Kubernetes: uses service endpoints and environment variables
    """
    # Check if running in Kubernetes (service endpoints available)
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        # Kubernetes deployment - use service endpoints
        mysql_host = os.getenv("MYSQL_HOST", "mysql-service")
        mysql_port = os.getenv("MYSQL_PORT", "3306")
        mysql_user = os.getenv("MYSQL_USER", "root")
        mysql_password = os.getenv("MYSQL_ROOT_PASSWORD", "rootpassword")
        mysql_database = os.getenv("MYSQL_DATABASE", "pdfs")
        
        return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    else:
        # Local development - use .env file or default
        return os.getenv("DATABASE_URL", "mysql+pymysql://root:12341234@localhost/pdfs")

# Database configuration
DATABASE_URL = get_database_url()

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