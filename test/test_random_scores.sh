#!/bin/bash

API_URL="http://127.0.0.1:5000/score"
COUNT=40

for ((i=1; i<=COUNT; i++)); do
  player_id=$((RANDOM % 20))
  score=$((RANDOM % 101))
  
  echo "[$i] Submitting: $player_id -> $score"
  sleep 0.3
  

  response=$(curl -s -X POST "$API_URL" \
    -d "player_id=$player_id&score=$score")

  echo "Response: $response"
done
