## IoT Device Monitoring Service (Huawei Internship Project)


Practical reference implementation for ingesting IoT device metrics via REST API, buffering with Kafka, persisting to PostgreSQL, caching latest values in Redis, and exposing both a small HTML dashboard and JSON APIs. Built during a Huawei internship.


### Components
- Flask app: API + dashboard
- Kafka: queue for readings
- Worker: consumes, validates, inserts, updates cache
- PostgreSQL: durable storage
- Redis: cache, latest value per (device, metric)

### Run Locally
Prereq: Docker + Docker Compose.
```
docker compose up -d --build
```
Open http://localhost (dashboard) and http://localhost/health.

Stop (keep data): `docker compose down`
Stop + wipe db: `docker compose down -v`

### Configuration (.env) Defaults
```
DB_HOST=postgres
DB_PORT=5432
DB_NAME=iot_devices_db
DB_USER=admin
DB_PASSWORD=admin1234
REDIS_HOST=redis
REDIS_PORT=6379
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
FLASK_ENV=development
FLASK_DEBUG=True
```

### Data Model (Simplified)
```
reading(device_id TEXT,
            metric_type ENUM(...),
            value DOUBLE PRECISION,
            timestamp TIMESTAMPTZ)
```
Metric types: temperature, humidity, pressure, voltage, current, power.

### API
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/device/data | Single reading |
| POST | /api/device/data/bulk | Up to 100 readings |
| GET | /api/devices | Latest per device/metric |
| GET | /api/device/<device_id>/latest | Latest per metric for one device |
| GET | /api/device/<device_id>/history?metric_type=&limit= | Historical list (limit ≤ 1000) |
| POST | /api/delete-all | Clear DB + cache (demo only) |
| GET | /health | Liveness |

Examples:
```
curl -s -X POST http://localhost/api/device/data \
   -H 'Content-Type: application/json' \
   -d '{"device_id":"device_01","metric_type":"temperature","value":22.5}'

curl -s -X POST http://localhost/api/device/data/bulk \
   -H 'Content-Type: application/json' \
   -d '{"readings":[{"device_id":"d1","metric_type":"humidity","value":55.2},{"device_id":"d1","metric_type":"temperature","value":21.1}]}'
```

### Generating Sample Data
Script arguments: device_count metrics_per_device iterations
```
bash test/test_random_data.sh
```

### Deployment (Huawei Cloud)
First, create a VPC, subnets, security group for a simple web app (ports 80/443). All the components ca run in the same VPC.

**Option A (single ECS):** run the same compose stack. Open ports 80/443. Attach Elastic IP.

**Option B (managed services):** use RDS (Postgres), DCS (Redis), DMS (Kafka). Run API + worker on ECS or CCE.
Minimal production overrides:
```
DB_HOST=<rds-endpoint>
DB_USER=<user>
DB_PASSWORD=<password>
REDIS_HOST=<dcs-endpoint>
KAFKA_BOOTSTRAP_SERVERS=<dms-bootstrap>
FLASK_ENV=production
FLASK_DEBUG=False
```
Put API behind ELB; add Auto Scaling if required.


Reset (demo only):
```
curl -X POST http://localhost/api/delete-all
```
