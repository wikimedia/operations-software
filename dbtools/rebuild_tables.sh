#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <hostname>"
    exit 1
fi

# Ensure the script is running inside a screen session
if [ -z "$STY" ]; then
    echo "Error: This script must be run inside a screen session."
    exit 1
fi

HOSTNAME=$1

# Tables to alter
TABLES=("pagelinks" "recentchanges")

for TABLE in "${TABLES[@]}"; do
    SCHEMAS=$(db-mysql "$HOSTNAME" information_schema -e \
        "SELECT DISTINCT table_schema FROM tables WHERE table_name='$TABLE';" -BN)

    if [ -z "$SCHEMAS" ]; then
        echo "No schemas found for table: $TABLE"
        continue
    fi

    for SCHEMA in $SCHEMAS; do
        echo "Processing schema: $SCHEMA, table: $TABLE"
        START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
        echo "Start time: $START_TIME"

        db-mysql "$HOSTNAME" "$SCHEMA" -e \
            "SET SESSION sql_log_bin=0; ALTER TABLE $TABLE ENGINE=InnoDB, FORCE;"

        if [ $? -eq 0 ]; then
            END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
            echo "Successfully altered $TABLE in schema $SCHEMA"
            echo "End time: $END_TIME"
        else
            END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
            echo "Failed to alter $TABLE in schema $SCHEMA"
            echo "End time: $END_TIME"
        fi
    done

done
