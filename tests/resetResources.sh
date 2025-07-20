#!/bin/bash

FILE1="./tests/resources/counter1"
FILE2="./tests/resources/counter2"
DEVICE="./tests/resources/device"

echo "0" > "$FILE1"
echo "0" > "$FILE2"
echo "idle" > "$DEVICE"