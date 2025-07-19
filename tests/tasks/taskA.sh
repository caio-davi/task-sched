#!/bin/bash

FILE="./tests/resources/counter1"

sleep 2

COUNTER=$(cat "$FILE")

NEW_COUNTER=$((COUNTER + 1))
echo "$NEW_COUNTER" > "$FILE"