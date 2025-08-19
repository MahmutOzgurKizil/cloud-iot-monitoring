import db
from redis_client import rc
import kafka_client as kc
from flask import Flask, request, jsonify, render_template
import json
from datetime import datetime

app = Flask(__name__)

ALLOWED_METRICS = {
    'temperature', 'humidity', 'pressure', 'voltage', 'current', 'power'
}

def validate_input(device_id, metric_type, value_raw, timestamp_raw=None):
    if device_id is None or metric_type is None or value_raw is None:
        raise ValueError('Missing device_id, metric_type, or value')
    
    if not isinstance(device_id, str) or len(device_id.strip()) == 0:
        raise ValueError('device_id must be a non-empty string')
    
    if metric_type not in ALLOWED_METRICS:
        raise ValueError("Invalid metric_type")
    
    try:
        value = float(value_raw)
    except ValueError:
        raise ValueError('Value must be a number')
    
    timestamp = None
    if timestamp_raw:
        try:
            timestamp = datetime.fromisoformat(timestamp_raw.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('Timestamp must be in ISO format (e.g., 2023-01-01T12:00:00Z)')
    else:
        timestamp = datetime.utcnow()
    
    return device_id.strip(), metric_type, value, timestamp

def process_submission(device_id, metric_type, value, timestamp):
    kc.send_device_data_update(device_id, metric_type, value, timestamp)

@app.route('/api/device/data', methods=['POST'])
def handle_submit_device_data():
    try:
        if request.is_json:
            data = request.get_json()
            device_id = data.get('device_id')
            metric_type = data.get('metric_type')
            value_raw = data.get('value')
            timestamp_raw = data.get('timestamp')
        else:
            device_id = request.form.get('device_id')
            metric_type = request.form.get('metric_type')
            value_raw = request.form.get('value')
            timestamp_raw = request.form.get('timestamp')

        device_id, metric_type, value, timestamp = validate_input(
            device_id, metric_type, value_raw, timestamp_raw
        )

        process_submission(device_id, metric_type, value, timestamp)

        return jsonify({
            'message': 'Device data submitted successfully',
            'device_id': device_id,
            'metric_type': metric_type,
            'value': value,
            'timestamp': timestamp.isoformat()
        }), 200

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/<device_id>/history', methods=['GET'])
def handle_get_device_history(device_id):
    try:
        metric_type = request.args.get('metric_type')
        limit = request.args.get('limit', 100, type=int)
        
        if limit > 1000:
            limit = 1000  # Cap at 1000 records
            
        cache_key = f"device_history_{device_id}_{metric_type}_{limit}"
        cache = rc.get(cache_key)
        if cache:
            history_data = json.loads(cache)
        else:
            history_data = db.get_device_history(device_id, metric_type, limit)
            rc.set(cache_key, json.dumps(history_data, default=str), ex=300)  # 5 minutes cache
        
        return jsonify({
            'device_id': device_id,
            'metric_type': metric_type,
            'data': history_data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_all_devices_data():
    cache = rc.get("all_devices")
    if cache:
        devices_data = json.loads(cache)
    else:
        devices_data = db.get_all_devices_latest()
        rc.set("all_devices", json.dumps(devices_data, default=str), ex=120)
    return devices_data

@app.route('/api/devices', methods=['GET'])
def handle_get_all_devices():
    try:
        devices_data = get_all_devices_data()
        return jsonify({'devices': devices_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# Bulk submission endpoint for device data
# that accepts a JSON array of readings
@app.route('/api/device/data/bulk', methods=['POST'])
def handle_bulk_device_data():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        readings = data.get('readings', [])
        
        if not isinstance(readings, list) or len(readings) == 0:
            return jsonify({'error': 'readings must be a non-empty array'}), 400
            
        if len(readings) > 100:
            return jsonify({'error': 'Maximum 100 readings per bulk request'}), 400
        
        processed_readings = []
        for i, reading in enumerate(readings):
            try:
                device_id, metric_type, value, timestamp = validate_input(
                    reading.get('device_id'),
                    reading.get('metric_type'),
                    reading.get('value'),
                    reading.get('timestamp')
                )
                process_submission(device_id, metric_type, value, timestamp)
                processed_readings.append({
                    'device_id': device_id,
                    'metric_type': metric_type,
                    'value': value,
                    'timestamp': timestamp.isoformat()
                })
            except ValueError as ve:
                return jsonify({'error': f'Reading {i}: {str(ve)}'}), 400
        
        return jsonify({
            'message': f'Bulk data submitted successfully',
            'processed_count': len(processed_readings),
            'readings': processed_readings
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# Since this is a demo and not a production app, I will provide a simple endpoint to delete all data to reset the state
@app.route('/api/delete-all', methods=['POST'])
def handle_delete_all():
    try:
        db.delete_all_device_data()
        rc.flushdb()
        return jsonify({'message': 'All device data deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Render the main dashboard page
@app.route('/', methods=['GET'])
def render_dashboard_page():
    devices = get_all_devices_data()
    return render_template('dashboard.html', devices=devices)

@app.route('/device/<device_id>', methods=['GET'])
def render_device_page(device_id):
    try:
        device_data = db.get_device_history(device_id)
        return render_template('device.html', device_id=device_id, device=device_data)
    except Exception as e:
        print(f"Error: {e}")  # Debugging
        return jsonify({'error': str(e)}), 500

# Simple health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    db.init_db()  
    app.run(host='0.0.0.0', port=5000)
