#!/bin/bash

DEVICE="./tests/resources/device"

echo "busy" > "$DEVICE"

sleep 1

NEW_COUNTER=$((COUNTER + 1))

echo "idle" > "$DEVICE"