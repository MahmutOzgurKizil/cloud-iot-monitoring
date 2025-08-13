#!/bin/bash

# Test script for IoT Device Monitoring System
# Simulates various devices sending sensor data

BASE_URL="http://localhost"
DEVICES=("device_01" "device_02" "device_03" "sensor_hub_alpha" "temp_monitor_beta")
METRICS=("temperature" "humidity" "pressure" "voltage" "current" "power")

echo "IoT Device Monitoring System - Test Script"
echo "============================================="

# Function to generate random values based on metric type
generate_value() {
    local metric=$1
    case $metric in
        "temperature")
            echo "$((RANDOM % 50 - 10))" # -10 to 40°C
            ;;
        "humidity")
            echo "$((RANDOM % 100))" # 0 to 100%
            ;;
        "pressure")
            echo "$((RANDOM % 200 + 950))" # 950 to 1150 hPa
            ;;
        "voltage")
            echo "$(echo "scale=2; $RANDOM/32767*24" | bc -l)" # 0 to 24V
            ;;
        "current")
            echo "$(echo "scale=3; $RANDOM/32767*5" | bc -l)" # 0 to 5A
            ;;
        "power")
            echo "$((RANDOM % 1000))" # 0 to 1000W
            ;;
    esac
}

# Test health endpoint
echo "Testing health endpoint..."
curl -s "$BASE_URL/health"
echo

# Submit individual readings
echo "Submitting individual device readings..."
for i in {1..10}; do
    device=${DEVICES[$((RANDOM % ${#DEVICES[@]}))]}
    metric=${METRICS[$((RANDOM % ${#METRICS[@]}))]}
    value=$(generate_value $metric)
    
    response=$(curl -s -X POST "$BASE_URL/api/device/data" \
        -H "Content-Type: application/json" \
        -d "{\"device_id\":\"$device\",\"metric_type\":\"$metric\",\"value\":$value}")
    
    if echo "$response" | grep -q "successfully"; then
        echo "$device - $metric: $value"
    else
        echo "Failed to submit data for $device: $response"
    fi
    
    sleep 0.5
done

echo

# Submit bulk readings
echo "Testing bulk data submission..."
bulk_json='{"readings":['
for i in {1..5}; do
    device=${DEVICES[$((RANDOM % ${#DEVICES[@]}))]}
    metric=${METRICS[$((RANDOM % ${#METRICS[@]}))]}
    value=$(generate_value $metric)
    
    if [ $i -gt 1 ]; then
        bulk_json+=','
    fi
    
    bulk_json+="{\"device_id\":\"$device\",\"metric_type\":\"$metric\",\"value\":$value}"
done
bulk_json+=']}'

response=$(curl -s -X POST "$BASE_URL/api/device/data/bulk" \
    -H "Content-Type: application/json" \
    -d "$bulk_json")

if echo "$response" | grep -q "successfully"; then
    echo "Bulk submission successful"
else
    echo "Bulk submission failed: $response"
fi

echo


echo Simple manual test examples
echo "curl -X POST $BASE_URL/api/device/data -H 'Content-Type: application/json' -d '{\"device_id\":\"device_01\",\"metric_type\":\"temperature\",\"value\":25.5}'"
echo "curl $BASE_URL/api/devices"
echo "curl $BASE_URL/api/device/device_01/latest"