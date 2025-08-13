# Huawei Internship — Learning Project

This project was built during my Huawei internship. It is a simple IoT device monitoring service.

## What this project does
- Receives device data over HTTP (JSON)
- Sends data to Kafka
- A worker saves data to PostgreSQL and refreshes Redis cache
- Shows a small web dashboard at `/`

## Tech stack
- Flask (API and dashboard)
- Kafka (message queue)
- PostgreSQL (database)
- Redis (cache)
- Docker Compose (local setup)

## Run locally
Prerequisites: Docker Desktop and Docker Compose.

1) Optional: create a `.env` file (see below). Defaults work for local use.
2) Start everything:
```bash
docker compose up -d --build
```
3) Open http://localhost (dashboard)
4) Health: http://localhost/health

To stop: `docker compose down` (add `-v` to also remove the Postgres volume).

### Environment (.env)
```
# Database
DB_HOST=postgres
DB_NAME=iot_devices_db
DB_USER=admin
DB_PASSWORD=admin1234
DB_PORT=5432

# Cache
REDIS_HOST=redis
REDIS_PORT=6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# App
FLASK_ENV=development
FLASK_DEBUG=True
```

## API
- POST `/api/device/data` — send one reading
   - `{ device_id, metric_type, value, timestamp? }`
- POST `/api/device/data/bulk` — send many readings
   - `{ readings: [ { device_id, metric_type, value, timestamp? }, ... ] }` (max 100)
- GET `/api/devices` — latest values per device/metric
- GET `/api/device/<device_id>/latest` — latest per metric for a device
- GET `/api/device/<device_id>/history?metric_type=&limit=` — history (limit ≤ 1000)
- POST `/api/delete-all` — clear DB and cache (demo only)
- GET `/health` — liveness check

Allowed metrics: `temperature`, `humidity`, `pressure`, `voltage`, `current`, `power`.

## Sample data
Send one reading:
```bash
curl -s -X POST http://localhost/api/device/data \
   -H 'Content-Type: application/json' \
   -d '{"device_id":"device_01","metric_type":"temperature","value":22.5}'
```

Generate random readings:
```bash
bash test/test_random_data.sh 50 10 5
```

## Deploy on Huawei Cloud
Option A — Single ECS with Docker Compose
1) Create an ECS VM and assign an Elastic IP
2) Install Docker and Docker Compose
3) Copy the repo and optional `.env`
4) Run `docker compose up -d`
5) Open ports 80/443; visit `http://<EIP>/health`

Option B — Managed services
- Use RDS (PostgreSQL), DCS (Redis), DMS (Kafka). Run API/worker on ECS or CCE.
- Update `.env`:
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
- Put the API behind ELB. Add Auto Scaling if needed.

## Troubleshooting
- Worker can retry until Kafka is ready
- To reset: POST `/api/delete-all` or remove the DB volume
- If the dashboard is empty, post some data and refresh

## Short roadmap
- Local MVP with compose
- Background worker and bulk ingest
- Single ECS deploy with Docker
- Move DB/Cache/Queue to RDS/DCS/DMS + ELB
- Scale out with Auto Scaling and health checks
