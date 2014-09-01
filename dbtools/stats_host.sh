#!/bin/bash
#
# Engine-independent index statistics

set -e

usage() {
    echo $0 --host=... --dblist=... --table=...
    exit 1
}

confirm() {
    read -p "continue? yes/no " yn
    if [[ ! "$yn" =~ ^y ]]; then
        echo "abort"
        exit 1
    fi
}

user="root"
host=""
port="3306"
dblist=()
db=""
table=""

for var in "$@"; do

    if [[ "$var" =~ ^--host=(.+) ]]; then
        host="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--port=(.+) ]]; then
        port="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--user=(.+) ]]; then
        user="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--dblist=(.+) ]]; then
        dblist="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--db=(.+) ]]; then
        db="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--table=(.+) ]]; then
        table="${BASH_REMATCH[1]}"
    fi

done

[ "$host"     ] || usage

# got .dblist?
if [[ "$dblist" =~ \.dblist ]]; then
    if [ -f "$dblist" ] ; then
        dblist=($(cat $dblist))
    else
        echo "Can't read $dblist"
        exit 1
    fi
# got db?
elif [ -n "$db" ]; then
    dblist=($db)
fi

[ "$dblist"   ] || usage

mysql="mysql -h $host -u $user -P $port --skip-column-names"

if ! $mysql -e "status"; then
    echo "Connect failed: $user@$host:$port"
    exit
fi

echo "Host        : $host"
echo "Port        : $port"
echo "Databases   : ${dblist[@]}"
echo "Table       : $table"

confirm

for db in "${dblist[@]}"; do

    echo "host: $host, database: $db"

    tlist="$table"
    if [[ ! "$table" =~ .+ ]]; then
        tlist=$($mysql -e "select table_name from information_schema.tables where table_schema = '$db'")
    fi

    for tbl in $tlist; do

        echo "host: $host, database: $db, table: $tbl"

        if ! $mysql -e "analyze table $db.$tbl persistent for all" >/dev/null; then
            echo "errors reported"
        fi

    done

done
