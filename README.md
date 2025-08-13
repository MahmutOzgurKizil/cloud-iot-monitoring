# Huawei Internship — Microservices on Cloud (Learning Project)

A small microservices system built to learn service decomposition, async messaging, caching, persistence, containerization, and cloud deployment.

## Architecture
- Flask API (HTTP REST)
- Kafka (async writes)
- Worker (Kafka consumer → DB writes + cache invalidation)
- PostgreSQL (storage)
- Redis (read cache)
- Docker Compose (local orchestration)

## Tech
- Python (Flask), PostgreSQL, Redis, Kafka
- Docker / Docker Compose

## Quick Start (Local)
```bash
docker compose up -d
open http://localhost
```

## Environment (.env)
Use these variables (update values as needed):
```
# Database (PostgreSQL)
DB_HOST=postgres
DB_NAME=iot_devices_db
DB_USER=admin
DB_PASSWORD=admin1234
DB_PORT=5432

# Cache (Redis)
REDIS_HOST=redis
REDIS_PORT=6379

# Message Queue (Kafka)
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# App
FLASK_ENV=development
FLASK_DEBUG=True
```

## Cloud Deployment

Option A — Single VM with Docker Compose (fastest)
1) Create a Linux VM (Huawei Cloud ECS), assign a Elastic IP (EIP).
2) Install Docker + Docker Compose.
3) Copy the repo and .env to the VM.
4) If all services run via Compose, keep:
   - DB_HOST=postgres, REDIS_HOST=redis, KAFKA_BOOTSTRAP_SERVERS=kafka:9092
5) Start:
   ```bash
   docker compose up -d
   ```
6) Open ports 80/443 in the security group; map API to 80/443 in compose if needed.
7) Verify: http://\<vm-public-ip>/health

Option B — Managed Services (recommended)
- Use Huawei Cloud: RDS for PostgreSQL, DCS for Redis, DMS for Kafka. Run API + worker on ECS or CCE.
- Update .env to managed endpoints:
  ```
  DB_HOST=<rds-endpoint>
  DB_PORT=5432
  DB_NAME=iot_devices_db
  DB_USER=<rds-user>
  DB_PASSWORD=<rds-password>

  REDIS_HOST=<dcs-endpoint>
  REDIS_PORT=6379

  KAFKA_BOOTSTRAP_SERVERS=<dms-bootstrap-servers>

  FLASK_ENV=production
  FLASK_DEBUG=False
  ```
- Put the API behind an Elastic Load Balance (ELB).

## API (short)
- POST /api/device/data
- POST /api/device/data/bulk
- GET  /api/devices
- GET  /api/device/\<device_id>/latest
- GET  /api/device/\<device_id>/history
- GET  /health

## Operations
```bash
docker compose logs -f flask-app
docker compose logs -f device-data-worker
```