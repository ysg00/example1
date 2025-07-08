# PDF Management API

A FastAPI application for managing PDF uploads, storage, and analysis with vector database integration.

## Features

- **PDF Upload**: Generate pre-signed S3 URLs for secure file uploads
- **PDF Management**: List, retrieve, and delete PDF metadata
- **PDF Analysis**: Extract text content and store in OpenSearch vector database
- **Vector Search**: Search for similar PDFs based on content
- **Docker Support**: Complete containerized setup with docker-compose

## Architecture

- **FastAPI**: Modern Python web framework
- **MySQL**: SQL database for PDF metadata storage
- **AWS S3**: Object storage for PDF files
- **OpenSearch**: Vector database for PDF content analysis and search
- **Docker**: Containerization for easy deployment

## API Endpoints

### 1. Upload PDF
```
POST /api/v1/upload_pdf
```
Generate a pre-signed URL for uploading a PDF file.

**Request Body:**
```json
{
  "filename": "document.pdf"
}
```

**Response:**
```json
{
  "upload_url": "https://s3.amazonaws.com/...",
  "pdf_id": 1,
  "s3_key": "pdfs/uuid.pdf"
}
```

### 2. Mark PDF as Uploaded
```
POST /api/v1/mark_uploaded/{pdf_id}
```
Mark a PDF as uploaded after successful S3 upload.

**Response:**
```json
{
  "message": "PDF marked as uploaded",
  "pdf_id": 1
}
```

### 3. List PDFs
```
GET /api/v1/list_pdf?skip=0&limit=100
```
Retrieve list of all uploaded PDFs.

**Response:**
```json
{
  "pdfs": [
    {
      "id": 1,
      "filename": "document.pdf",
      "s3_key": "pdfs/uuid.pdf",
      "file_size": 1024000,
      "upload_date": "2024-01-01T12:00:00Z",
      "status": "PARSED",
      "vector_index_id": "pdf_1",
      "content_summary": "PDF content has been extracted, embedded, and indexed in vector database"
    }
  ],
  "total_count": 1
}
```

**Status Values:**
- `PRE_SIGNED`: Pre-signed URL generated, file not yet uploaded
- `UPLOADED`: File uploaded to S3, ready for analysis
- `PARSED`: File parsed, embedded, and indexed in vector database

### 4. Get PDF Metadata
```
GET /api/v1/get_pdf/{pdf_id}
```
Retrieve PDF metadata by ID.

### 5. Delete PDF
```
DELETE /api/v1/delete_pdf/{pdf_id}
```
Delete PDF from S3, vector database, and metadata database.

### 6. Analyze PDF
```
POST /api/v1/analyze_pdf/{pdf_id}
```
Extract PDF content and store in vector database for similarity search.

**Response:**
```json
{
  "message": "PDF analyzed and indexed successfully",
  "pdf_id": 1,
  "vector_index_id": "pdf_1"
}
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- AWS S3 bucket and credentials
- Python 3.11+ (for local development)

### 1. Environment Setup

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your AWS credentials and other configuration:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-pdf-bucket-name
```

### 2. Start Services

```bash
docker-compose up -d
```

This will start:
- MySQL database (port 3306)
- OpenSearch (port 9200)
- FastAPI application (port 8000)

### 3. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **OpenSearch**: http://localhost:9200

## Development

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export $(cat .env | xargs)
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

### Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

## Production Deployment

### Docker Deployment

1. Build the production image:
```bash
docker build -t pdf-management-api .
```

2. Run with proper environment variables:
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  pdf-management-api
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | `mysql://root:password@localhost/rag` |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET_NAME` | S3 bucket name | `pdf-storage-bucket` |
| `OPENSEARCH_HOST` | OpenSearch host | `localhost` |
| `OPENSEARCH_PORT` | OpenSearch port | `9200` |
| `OPENSEARCH_USER` | OpenSearch username | `admin` |
| `OPENSEARCH_PASSWORD` | OpenSearch password | `admin` |

## Security Considerations

- Configure proper CORS settings for production
- Use environment variables for sensitive data
- Implement proper authentication and authorization
- Use HTTPS in production
- Configure proper AWS IAM roles and policies
- Secure OpenSearch with proper authentication

## Monitoring and Logging

The application includes:
- Health check endpoint (`/health`)
- Structured logging
- Docker health checks
- OpenSearch monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License 