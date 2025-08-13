#!/bin/bash

# Post N random readings (default 100) to the API
BASE_URL="http://localhost"
COUNT=${1:-100}
COUNT_BULK=${2:-100}
ITEMS_PER_BULK=${3:-5}

DEVICES=("device_01" "device_02" "device_03" "sensors" "temp_monitor")
METRICS=("temperature" "humidity" "pressure" "voltage" "current" "power")

gen_value() {
    case $1 in
        temperature) echo $((RANDOM%51-10)) ;;
        humidity)    echo $((RANDOM%101)) ;;
        pressure)    echo $((RANDOM%201+950)) ;;
        voltage)     awk -v r="$RANDOM" 'BEGIN{printf "%.2f", r/32767*24}' ;;
        current)     awk -v r="$RANDOM" 'BEGIN{printf "%.3f", r/32767*5}' ;;
        power)       echo $((RANDOM%1001)) ;;
    esac
}

echo "Sending $COUNT random readings..."
success=0
for ((i=1;i<=COUNT;i++)); do
    device=${DEVICES[$((RANDOM % ${#DEVICES[@]}))]}
    metric=${METRICS[$((RANDOM % ${#METRICS[@]}))]}
    value=$(gen_value "$metric")
    payload=$(printf '{"device_id":"%s","metric_type":"%s","value":%s}' "$device" "$metric" "$value")
    resp=$(curl -s -X POST "$BASE_URL/api/device/data" -H 'Content-Type: application/json' -d "$payload")
    if echo "$resp" | grep -q "successfully"; then
        ((success++))
    else
        echo "[$i] failed: $resp"
    fi
done

echo "Done. Success: $success/$COUNT"

# Bulk submissions
echo "Sending $COUNT_BULK bulk submissions (each with $ITEMS_PER_BULK items)..."
bulk_success=0
for ((b=1;b<=COUNT_BULK;b++)); do
    items=""
    for ((k=1;k<=ITEMS_PER_BULK;k++)); do
        device=${DEVICES[$((RANDOM % ${#DEVICES[@]}))]}
        metric=${METRICS[$((RANDOM % ${#METRICS[@]}))]}
        value=$(gen_value "$metric")
        item=$(printf '{"device_id":"%s","metric_type":"%s","value":%s}' "$device" "$metric" "$value")
        items+="${items:+,}$item"
    done
    bulk_json='{"readings":['"$items"']}'
    resp=$(curl -s -X POST "$BASE_URL/api/device/data/bulk" -H 'Content-Type: application/json' -d "$bulk_json")
    if echo "$resp" | grep -q "successfully"; then
        ((bulk_success++))
    else
        echo "[bulk $b] failed: $resp"
    fi
done
echo "Bulk done. Success: $bulk_success/$COUNT_BULK"