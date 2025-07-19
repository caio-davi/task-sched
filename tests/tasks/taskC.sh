#!/bin/bash

FILE="../resources/counter1"
DEVICE="../resources/device"

echo "busy" > "$DEVICE"

sleep 5

COUNTER=$(cat "$FILE")
NEW_COUNTER=$((COUNTER + 1))

echo "$NEW_COUNTER" > "$FILE"
echo "idle" > "$DEVICE"