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

mysql="mysql -S /tmp/mysql.$shard.sock --skip-column-names"
mysqldump="mysqldump -S /tmp/mysql.$shard.sock --single-transaction --quick --no-create-info --skip-add-locks --skip-triggers --hex-blob"

for db in $(cat mediawiki-config/$shard.dblist); do
    for tbl in $($mysql $db -e "select table_name from repl_tables"); do
        while [ $(pgrep mysqldump | wc -l) -gt 10 ]; do
            sleep 1s
        done
        echo "$db.$tbl"
        $mysqldump $db $tbl | pigz >${db}_${tbl}.sql.gz &
    done
done