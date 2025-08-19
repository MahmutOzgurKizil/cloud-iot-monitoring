#!/bin/bash

# Post N random readings (default 100) to the API
BASE_URL="http://localhost"
COUNT=${1:-200}


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

echo "Sending $COUNT readings for $DEVICE_ID..."
success=0
for ((i=1;i<=COUNT;i++)); do
    ID_NUM=$((RANDOM % 15 + 1))
    DEVICE_ID="device_${ID_NUM}"
    echo -n "[$i/$COUNT] "
    metric=${METRICS[$((RANDOM % ${#METRICS[@]}))]}
    value=$(gen_value "$metric")
    payload=$(printf '{"device_id":"%s","metric_type":"%s","value":%s}' "$DEVICE_ID" "$metric" "$value")
    resp=$(curl -s -X POST "$BASE_URL/api/device/data" -H 'Content-Type: application/json' -d "$payload")
    if echo "$resp" | grep -q "successfully"; then
        ((success++))
    else
        echo "[$i] failed: $resp"
    fi
done
