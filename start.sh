#!/bin/bash

# RadiomicsHub - AI+影像组学全流程协作平台
# 启动脚本

set -e

echo "🚀 Starting RadiomicsHub..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/app
mkdir -p frontend/src

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build and start services
echo "🔨 Building containers..."
docker-compose build

echo "▶️  Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🏥 Checking service health..."

# Check backend
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend may not be ready yet. Check logs: docker-compose logs backend"
fi

# Check MinIO
if curl -s http://localhost:9000/minio/health/live > /dev/null; then
    echo "✅ MinIO is healthy"
else
    echo "⚠️  MinIO may not be ready yet. Check logs: docker-compose logs minio"
fi

echo ""
echo "🎉 RadiomicsHub is starting!"
echo ""
echo "📍 Access points:"
echo "   Frontend:     http://localhost"
echo "   Backend API:  http://localhost:8000/api/docs"
echo "   MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "📝 Useful commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Stop:         docker-compose down"
echo "   Restart:      docker-compose restart"
echo ""
echo "🔐 Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📚 Documentation: http://localhost:8000/api/docs"