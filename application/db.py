import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

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
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create device_data table for storing sensor readings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS device_data (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(100) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            value DECIMAL(10, 4) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Create indexes for better query performance
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_device_data_device_id 
        ON device_data(device_id)
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_device_data_metric_type 
        ON device_data(metric_type)
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_device_data_timestamp 
        ON device_data(timestamp DESC)
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_device_data_device_metric 
        ON device_data(device_id, metric_type, timestamp DESC)
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def insert_device_data(device_id, metric_type, value, timestamp):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO device_data (device_id, metric_type, value, timestamp)
        VALUES (%s, %s, %s, %s)
    """, (device_id, metric_type, value, timestamp))
    conn.commit()
    cur.close()
    conn.close()

def get_latest_device_data(device_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT DISTINCT ON (metric_type) 
               metric_type, value, timestamp
        FROM device_data 
        WHERE device_id = %s 
        ORDER BY metric_type, timestamp DESC
    """, (device_id,))
    latest_data = cur.fetchall()
    cur.close()
    conn.close()
    return latest_data

def get_device_history(device_id, metric_type=None, limit=100):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if metric_type:
        cur.execute("""
            SELECT metric_type, value, timestamp
            FROM device_data 
            WHERE device_id = %s AND metric_type = %s
            ORDER BY timestamp DESC 
            LIMIT %s
        """, (device_id, metric_type, limit))
    else:
        cur.execute("""
            SELECT metric_type, value, timestamp
            FROM device_data 
            WHERE device_id = %s
            ORDER BY timestamp DESC 
            LIMIT %s
        """, (device_id, limit))
    
    history_data = cur.fetchall()
    cur.close()
    conn.close()
    return history_data

def get_all_devices_latest():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Pull only the latest row per (device_id, metric_type) directly from SQL
    cur.execute("""
        SELECT device_id, metric_type, value, timestamp
        FROM (
            SELECT device_id,
                   metric_type,
                   value,
                   timestamp,
                   ROW_NUMBER() OVER (
                       PARTITION BY device_id, metric_type
                       ORDER BY timestamp DESC
                   ) AS rn
            FROM device_data
        ) t
        WHERE rn = 1
    """)
    latest_rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Group by device_id and assemble metrics, tracking last_updated per device
    devices = {}
    for row in latest_rows:
        device_id = row['device_id']
        if device_id not in devices:
            devices[device_id] = {
                'device_id': device_id,
                'metrics': {},
                'last_updated': row['timestamp']
            }

        devices[device_id]['metrics'][row['metric_type']] = {
            'value': float(row['value']),
            'timestamp': row['timestamp']
        }

        # Update last_updated to the most recent timestamp among metrics
        if row['timestamp'] > devices[device_id]['last_updated']:
            devices[device_id]['last_updated'] = row['timestamp']
    
    return list(devices.values())

def delete_all_device_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM device_data")
    conn.commit()
    cur.close()
    conn.close()
