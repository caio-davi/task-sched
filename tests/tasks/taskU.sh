#!/bin/bash

FILE2="./tests/resources/counter2"

RANDOM_NUMBER=$(( ( RANDOM % 1000 ) + 1 ))

sleep 4

COUNTER2=$(cat "$FILE2")

NEW_COUNTER2=$(($COUNTER2 + $RANDOM_NUMBER))

echo "$NEW_COUNTER2" > "$FILE2"