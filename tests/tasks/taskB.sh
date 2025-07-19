#!/bin/bash

FILE1="../resources/counter1"
FILE2="../resources/counter2"

RANDOM_NUMBER=$(( ( RANDOM % 1000 ) + 1 ))

sleep 8

COUNTER1=$(cat "$FILE1")
COUNTER2=$(cat "$FILE2")

NEW_COUNTER1=$(($COUNTER1 + 1))
NEW_COUNTER2=$(($COUNTER2 + $RANDOM_NUMBER))

echo "$NEW_COUNTER1" > "$FILE1"
echo "$NEW_COUNTER2" > "$FILE2"