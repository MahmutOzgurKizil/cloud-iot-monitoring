import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'iot_devices_db')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin1234')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def init_db():
    # Minimal setup: table + one composite index that supports our queries
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS device_data (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(100) NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                value DECIMAL(10, 4) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """
        )
        # Single composite index covers latest-by-device/metric lookups
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_device_metric_ts
            ON device_data(device_id, metric_type, timestamp DESC)
            """
        )

def insert_device_data(device_id, metric_type, value, timestamp):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO device_data (device_id, metric_type, value, timestamp)
            VALUES (%s, %s, %s, %s)
            """,
            (device_id, metric_type, value, timestamp),
        )

def get_latest_device_data(device_id):
    # Latest row per metric for a single device
    with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT ON (metric_type)
                   metric_type, value, timestamp
            FROM device_data
            WHERE device_id = %s
            ORDER BY metric_type, timestamp DESC
            """,
            (device_id,),
        )
        return cur.fetchall()

def get_device_history(device_id, metric_type=None, limit=100):
    with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        if metric_type:
            cur.execute(
                """
                SELECT metric_type, value, timestamp
                FROM device_data
                WHERE device_id = %s AND metric_type = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (device_id, metric_type, limit),
            )
        else:
            cur.execute(
                """
                SELECT metric_type, value, timestamp
                FROM device_data
                WHERE device_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (device_id, limit),
            )
        return cur.fetchall()

def get_all_devices_latest():
    # Latest row per (device_id, metric_type) using a simple DISTINCT ON
    with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT ON (device_id, metric_type)
                   device_id, metric_type, value, timestamp
            FROM device_data
            ORDER BY device_id, metric_type, timestamp DESC
            """
        )
        latest_rows = cur.fetchall()

    # Group by device_id and assemble metrics, track last_updated per device
    devices = {}
    for row in latest_rows:
        device_id = row['device_id']
        if device_id not in devices:
            devices[device_id] = {
                'device_id': device_id,
                'metrics': {},
                'last_updated': row['timestamp'],
            }

        devices[device_id]['metrics'][row['metric_type']] = {
            'value': float(row['value']),
            'timestamp': row['timestamp'],
        }

        if row['timestamp'] > devices[device_id]['last_updated']:
            devices[device_id]['last_updated'] = row['timestamp']

    return list(devices.values())

def delete_all_device_data():
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM device_data")
