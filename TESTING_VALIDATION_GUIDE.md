## QUICK START & VALIDATION GUIDE

### Getting Started in 5 Minutes

```bash
# 1. Navigate to project
cd c:\work\django_project

# 2. Copy environment file
cp .env.example .env

# 3. Start all services with Docker
docker-compose up -d

# 4. Run migrations and load data
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py load_fixtures
docker-compose exec django python manage.py createsuperuser  # Optional

# 5. Access the platform
# API: http://localhost:8000
# Docs: http://localhost:8000/api/docs/
# Admin: http://localhost:8000/admin/
# Grafana: http://localhost:3000 (admin/admin)
```

---

## TESTING THE API

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@school.com",
    "username": "student1",
    "first_name": "John",
    "last_name": "Doe",
    "mobile": "9876543210",
    "role": "STUDENT",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123",
    "school_code": "SCHOOL001"
  }'
```

### 2. Login and Get JWT Tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@school.com",
    "password": "SecurePass123"
  }'

# Response includes JWT tokens
```

### 3. Browse Products

```bash
curl http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Add Items to Cart

```bash
curl -X POST http://localhost:8000/api/v1/cart/items \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_UUID",
    "quantity": 2
  }'
```

### 5. Create Order

```bash
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "total_amount": "500.00",
    "items": [
      {"product_id": "PRODUCT_UUID", "quantity": 2}
    ]
  }'
```

### 6. Track Order Status

```bash
curl http://localhost:8000/api/v1/orders/ORDER_UUID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## TESTING KAFKA EVENTS

### 1. Verify Kafka is Running

```bash
docker-compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --list
```

Expected output:
```
__consumer_offsets
order-created
payment-processed
inventory-updated
notification-events
transaction-dlq
```

### 2. Monitor Kafka Events

```bash
# In a separate terminal, watch order events
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic order-created \
  --from-beginning
```

### 3. Test Order-to-Event Flow

When you create an order:
1. Event published to `order-created` topic
2. Consumer processes event
3. Transaction created
4. Payment event published to `payment-processed`
5. Inventory updated
6. Email notification queued in Celery

---

## TESTING CELERY TASKS

### 1. View Celery Logs

```bash
docker-compose logs -f celery
```

You should see tasks being executed:
- `send_order_confirmation_email`
- `send_payment_receipt_email`
- `cleanup_expired_carts`

### 2. Monitor Task Queue

```bash
docker-compose exec celery celery -A config inspect active
```

This shows currently executing tasks.

### 3. Check Task Results

```bash
docker-compose exec django python manage.py shell
>>> from celery.result import AsyncResult
>>> AsyncResult('task-id').result
```

---

## TESTING REDIS CACHING

### 1. Check Redis Connection

```bash
docker-compose exec redis redis-cli ping
# Response: PONG
```

### 2. View Cached Items

```bash
docker-compose exec redis redis-cli

# In Redis CLI
> KEYS *
> GET cart:user_uuid
> FLUSHDB  # Clear all cache (for testing)
```

### 3. Monitor Cache Performance

```bash
docker-compose exec redis redis-cli INFO stats
```

---

## TESTING DATABASE

### 1. Connect to PostgreSQL

```bash
docker-compose exec postgres psql -U postgres -d school_commerce_dev

# List tables
\dt

# View users
SELECT * FROM users;

# View orders
SELECT * FROM orders;
```

### 2. Run Database Queries

```bash
# Check product inventory
SELECT p.product_name, p.stock_quantity, p.availability_status 
FROM products p;

# Check order history
SELECT o.id, u.email, o.total_amount, o.status 
FROM orders o 
JOIN users u ON o.user_id = u.id;
```

---

## MONITORING DASHBOARD

### 1. Access Prometheus

Visit: http://localhost:9090

Query examples:
```
# Request rate
rate(django_http_requests_total[1m])

# Error rate
rate(django_http_requests_total{status="500"}[5m])

# Celery task execution time
celery_task_execution_time_bucket

# Database connection pool
django_db_connection_pool_usage
```

### 2. Access Grafana

Visit: http://localhost:3000 (admin/admin)

Pre-built dashboards should show:
- API request metrics
- Error rates
- Celery task performance
- Database health
- Cache hit rates

---

## RUNNING TESTS

### 1. Run All Tests

```bash
docker-compose exec django pytest tests/ -v --cov=apps
```

### 2. Run Specific Test File

```bash
docker-compose exec django pytest tests/test_accounts.py -v
```

### 3. Run Specific Test

```bash
docker-compose exec django pytest tests/test_orders.py::TestOrderCreation::test_create_order -v
```

### 4. Run with Coverage Report

```bash
docker-compose exec django pytest --cov=apps --cov-report=html
# Open htmlcov/index.html to view coverage
```

---

## API DOCUMENTATION

Visit: http://localhost:8000/api/docs/

This interactive documentation allows you to:
- View all endpoints
- See request/response schemas
- Try out API calls directly
- View authentication requirements

---

## TROUBLESHOOTING

### Service Won't Start

```bash
# Check service logs
docker-compose logs <service_name>

# Restart service
docker-compose restart <service_name>

# Full restart
docker-compose down
docker-compose up -d
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready

# Reset migrations
docker-compose exec django python manage.py migrate --fake zero
docker-compose exec django python manage.py migrate
```

### Celery Tasks Not Running

```bash
# Check RabbitMQ
docker-compose exec rabbitmq rabbitmq-diagnostics -q ping

# Check Celery worker
docker-compose logs celery

# Restart Celery
docker-compose restart celery
```

### Kafka Connection Issues

```bash
# Check Kafka
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# List topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

## PERFORMANCE TESTING

### 1. Load Testing with Apache Bench

```bash
# Test API endpoint
ab -n 1000 -c 50 http://localhost:8000/api/v1/products/

# Results show:
# - Requests per second
# - Mean response time
# - Fastest/slowest requests
```

### 2. Load Testing with k6 (if installed)

```bash
# Create load test script (k6-test.js)
# Run: k6 run k6-test.js
```

### 3. Monitor Under Load

```bash
# Watch in Grafana while running load test
# Check:
# - CPU usage
# - Memory usage
# - Request latency
# - Database connections
# - Cache hit rates
```

---

## VERIFYING END-TO-END FLOW

### Complete Order Flow Test

1. **Register User**
   - Create new user with valid credentials
   - Verify JWT tokens returned

2. **Browse Products**
   - List products
   - Filter by category
   - Verify caching (subsequent requests are faster)

3. **Add to Cart**
   - Add items to cart
   - Verify Redis caching
   - Update quantities
   - Remove items

4. **Create Order**
   - Submit cart as order
   - Verify order created in database
   - Verify event published to Kafka

5. **Verify Events**
   - Check `order-created` topic in Kafka
   - Verify consumer processed event
   - Check Celery tasks queued

6. **Verify Payment**
   - Check transaction record created
   - Verify payment status
   - Check `payment-processed` event

7. **Verify Email**
   - Check email queue (console backend prints to logs)
   - Verify notification logged

8. **Verify Inventory**
   - Check product stock updated
   - Verify `inventory-updated` event
   - Check inventory movement record

---

## CLEANUP

### Stop All Services

```bash
docker-compose down
```

### Remove All Containers and Volumes

```bash
docker-compose down -v
```

### Remove Images

```bash
docker-compose down --rmi all
```

---

## SUCCESS CRITERIA CHECKLIST

- [ ] All Docker services running
- [ ] Database migrations successful
- [ ] Can register and login users
- [ ] Can browse products
- [ ] Can add items to cart
- [ ] Can create orders
- [ ] Kafka events being published
- [ ] Celery tasks being executed
- [ ] Emails being sent (logged)
- [ ] Redis caching working
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards displaying data
- [ ] All API endpoints responding
- [ ] Admin interface accessible
- [ ] API documentation loaded

---

## NEXT STEPS

1. Implement remaining app modules
2. Write comprehensive test suite
3. Create Kubernetes manifests
4. Set up CI/CD pipeline
5. Deploy to cloud platform
6. Monitor production system
7. Optimize based on metrics

Happy coding! 🚀
