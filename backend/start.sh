#!/bin/bash

# PDF Management API Startup Script

echo "🚀 Starting PDF Management API..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your AWS credentials and other settings."
    echo "   Then run this script again."
    exit 1
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Show API endpoints
echo ""
echo "✅ Services are running!"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo "🔍 OpenSearch: http://localhost:9200"
echo ""
echo "🧪 To test the API, run: python test_api.py"
echo ""
echo "🛑 To stop services, run: docker-compose down" 