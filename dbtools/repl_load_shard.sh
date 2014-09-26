#!/bin/bash

set -e

usage() {
    echo $0 --host=... --db=...
    exit 1
}

shard=""

for var in "$@"; do

    if [[ "$var" =~ ^--shard=(.+) ]]; then
        shard="${BASH_REMATCH[1]}"
    fi

done

[ "$shard" ] || usage

mysql="mysql -S /tmp/mysql.sock --skip-column-names"

for db in $(cat mediawiki-config/$shard.dblist); do
    for tbl in $($mysql repl_${db} -e "select table_name from repl_tables"); do
        while [ $(pgrep gzip | wc -l) -gt 10 ]; do
            sleep 1s
        done
        echo "repl_${db}.${tbl}"
        zcat ${db}_${tbl}.sql.gz | $mysql repl_${db} &
    done
done