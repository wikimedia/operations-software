#!/bin/bash

set -e

usage() {
    echo $0 --host=... --port=... --user=... --db=...
    exit 1
}

user="root"
host=""
port="3306"
db=""

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

    if [[ "$var" =~ ^--db=(.+) ]]; then
        db="${BASH_REMATCH[1]}"
    fi

done

[ "$db"   ] || usage
[ "$host" ] || usage

my="mysql -h $host -P $port -u $user --skip-column-names"

echo $db

#$my -e "stop slave"

./repl_prepare_schema.sh --host=$host --port=$port --user=$user --db=$db

sql="select t.table_name from information_schema.tables t"
sql="$sql left join $db.repl_ignore i on t.table_name = i.table_name"
sql="$sql where t.table_schema = '$db' and t.table_name not like 'repl\_%' and i.table_name is null"

for tbl in $($my -e "$sql" $db); do
	echo $db.$tbl
	./repl_prepare_table.sh --host=$host --port=$port --user=$user --db=$db --table=$tbl
done

#$my -e "start slave"
