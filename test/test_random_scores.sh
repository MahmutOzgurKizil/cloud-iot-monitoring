#!/bin/bash

API_URL="http://localhost:80/score"
COUNT=200

for ((i=1; i<=COUNT; i++)); do
  player_id=$((RANDOM % 100))
  score=$((RANDOM % 1001))

  echo "[$i] Submitting: $player_id -> $score"

  response=$(curl -s -X POST "$API_URL" \
    -d "player_id=$player_id&score=$score")


  echo "Response: $response"
done