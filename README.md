# EduMart

A highly scalable, enterprise-grade web application for managing school product purchases and transactions. Supports millions of requests per hour with guaranteed transaction safety, asynchronous processing, and zero data loss.

## Architecture Overview

### System Components
- **User Service** - Authentication, authorization, role management
- **Product Service** - Catalog, categories, inventory management
- **Cart Service** - Shopping cart with Redis caching
- **Order Service** - Order management and processing
- **Transaction Service** - Payment processing with Kafka event-driven architecture
- **Notification Service** - Email/SMS notifications via Celery
- **Audit Service** - Transaction logging and tracing

### Technology Stack
- **Backend**: Python 3.11, Django 4.2, Django REST Framework
- **Database**: PostgreSQL (primary), Redis (cache/sessions)
- **Message Queue**: Apache Kafka (event streaming)
- **Task Queue**: Celery + RabbitMQ
- **API**: REST with JWT authentication, OpenAPI/Swagger
- **Deployment**: Docker, Docker Compose, Nginx, Gunicorn
- **Monitoring**: Prometheus, Grafana

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Local Development Setup

1. **Clone and setup**
```bash
git clone <repository>
cd django_project
cp .env.example .env
```

2. **Start services with Docker Compose**
```bash
docker-compose up -d
```

3. **Initialize database**
```bash
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py load_fixtures
docker-compose exec django python manage.py createsuperuser
```

4. **Access the application**
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## Key Features

✅ **Scalability**: Handles millions of requests/hour with horizontal scaling
✅ **Event-Driven Architecture**: Apache Kafka for reliable event streaming
✅ **Transaction Safety**: Guaranteed zero data loss with distributed transactions
✅ **Async Processing**: Celery workers for background jobs
✅ **Caching**: Redis cache for high performance
✅ **API Documentation**: OpenAPI/Swagger auto-generated docs
✅ **Monitoring**: Prometheus metrics and Grafana dashboards
✅ **Security**: JWT authentication, role-based access control
✅ **Docker Ready**: Complete Docker Compose setup for local dev and production

## Documentation

- See `IMPLEMENTATION_GUIDE.md` for detailed implementation steps
- See `docs/` directory for architecture diagrams and design docs
- See API documentation at http://localhost:8000/api/docs/