#!/bin/bash

# YTT Production Deployment Script
# This script builds and deploys YTT with LibreTranslate

set -e

echo "🚀 YTT Production Deployment"
echo "============================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Build the YTT image
echo "📦 Building YTT Docker image..."
cd ..
docker build -t ytt:latest .
cd production

# Start services
echo "🔄 Starting services..."
docker compose down
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check service health
echo "🔍 Checking service status..."
docker compose ps

# Test endpoints
echo "🧪 Testing endpoints..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    echo "✅ YTT is running at http://localhost:8000"
else
    echo "⚠️  YTT health check failed"
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/languages | grep -q "200"; then
    echo "✅ LibreTranslate is running at http://localhost:5000"
else
    echo "⚠️  LibreTranslate health check failed"
fi

echo ""
echo "🎉 Deployment complete!"
echo "Access YTT at: http://localhost:8000"