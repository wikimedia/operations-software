#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <hostname> <taskid>"
    exit 1
fi

# Ensure the script is running inside a screen session
if [ -z "$STY" ]; then
    echo "Error: This script must be run inside a screen session."
    exit 1
fi

HOSTNAME=$1
TASKID=$2

# Downtime the host
echo "Downtiming $HOSTNAME for 12 hours"

# For now, 12h hardcoded downtime
sudo cookbook sre.hosts.downtime --hours 12 -r "Index rebuild" -t $TASKID $HOSTNAME*

# Tables to alter
TABLES=("linter" "pagelinks" "recentchanges")

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
            "STOP SLAVE; SET SESSION sql_log_bin=0; ALTER TABLE $TABLE ENGINE=InnoDB, FORCE; START SLAVE;"

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

# Check replication lag
echo "Checking replication lag..."
while true; do
    REPL_LAG=$(db-mysql "$HOSTNAME" -e "SHOW SLAVE STATUS\\G" | grep 'Seconds_Behind_Master' | awk -F': ' '{print $2}')
    if [ "$REPL_LAG" -eq 0 ]; then
        echo "Replication lag is 0. Proceeding."
        break
    else
        echo "Replication lag: $REPL_LAG seconds. Waiting..."
        sleep 60
    fi
done

# Run repool cookbook - repooling in 4 steps
sudo cookbook sre.mysql.pool -r "Repooling after rebuild index $TASKID" $HOSTNAME
