#!/bin/bash
# Quick start script for School Commerce Platform

set -e

echo "======================================================"
echo "School Commerce Platform - Quick Start"
echo "======================================================"
echo ""

# Check prerequisites
echo "✓ Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Setup environment
echo "✓ Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
fi

# Build and start services
echo "✓ Starting Docker Compose services..."
docker-compose up -d

# Wait for services
echo "✓ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "✓ Running database migrations..."
docker-compose exec -T django python manage.py migrate

# Load fixtures
echo "✓ Loading sample data..."
docker-compose exec -T django python manage.py load_fixtures || true

# Create superuser (optional)
echo ""
echo "======================================================"
echo "Setup Complete!"
echo "======================================================"
echo ""
echo "Access the application:"
echo "  • API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/api/docs/"
echo "  • Admin: http://localhost:8000/admin/"
echo "  • Grafana: http://localhost:3000 (admin/admin)"
echo "  • Prometheus: http://localhost:9090"
echo ""
echo "Create superuser (optional):"
echo "  docker-compose exec django python manage.py createsuperuser"
echo ""
echo "Run tests:"
echo "  docker-compose exec django pytest tests/ -v"
echo ""
echo "View logs:"
echo "  docker-compose logs -f django"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
