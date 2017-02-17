#!/bin/bash

# The dsns tables are used by pt-table-checksum as another method to
# discover slaves instead of "show processlist".

# We are using this method in order to tell pt-table-checksum which slaves
# it should look for, so we can discard dbstores and sanitarium hosts
# which might be delayed and then would stop the check forever.

# This quick and small shell script just parses the output from *.hosts
# files to identify the slaves, remove the dbstore or sanitarium ones, as
# well as the primary master and builds the syntax to run on mysql to
# populate the dsns tables.

# The dsns tables live under the dsns database on Tendril hosts.
# There is one table per shard at the moment.

set -e

if [ $# -eq 0 ]
then
    echo "Usage: generate_dsns_table.sh shard_number"
    echo "Example: generate_dsns_table.sh s1"
    echo "Valid shards: m3,s1,s2,s3,s4,s5,s6,s7,s8"
    exit 1
fi
SHARD="$1"
HOST_FILE_PATH="/home/marostegui/git/software/dbtools/"
FILE="$SHARD.hosts"
for i in $(cat "$HOST_FILE_PATH/$FILE"  | grep "^db" | egrep -v "dbstore*|db1095|db1069" | cut -d " " -f1 | head -n-1)
# The master is delete from the list of hosts as it is not a slave that needs to be checked
do
    echo "insert into dsns.dsns_$SHARD (dsn) values (\"h=$i,u=root\");";
done
echo "-- The master is not included on this list as this is only for slaves to be checked"
