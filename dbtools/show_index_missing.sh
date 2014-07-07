#!/bin/bash

set -e

osctool=$(which pt-online-schema-change)

usage() {
	echo $0 --host=... --dblist=... --table... \"SQL\"
	exit
}

confirm() {
	read -p "continue? yes/no " yn
	if [[ ! "$yn" =~ ^y ]]; then
		echo "abort"
		exit 1
	fi
}

user="root"
hosts=""
dblist=""
table=""
index=""

for var in "$@"; do

	if [[ "$var" =~ ^--hosts=(.+) ]]; then
		hosts="${BASH_REMATCH[1]}"
	fi

	if [[ "$var" =~ ^--user=(.+) ]]; then
		user="${BASH_REMATCH[1]}"
	fi

	if [[ "$var" =~ ^--dblist=(.+) ]]; then
		dblist="${BASH_REMATCH[1]}"
	fi

	if [[ "$var" =~ ^--table=(.+) ]]; then
		table="${BASH_REMATCH[1]}"
	fi

	if [[ "$var" =~ ^--index=(.+) ]]; then
		index="${BASH_REMATCH[1]}"
	fi

done

[ "$hosts"    ] || usage
[ "$dblist"   ] || usage
[ "$table"    ] || usage
[ "$index"    ] || usage

if [ ! -f "$dblist" ] ; then
	echo "ERROR: $dblist not found"
	exit 1
fi

echo "Hosts     : $hosts"
echo "Databases : $dblist"
echo "Table     : $table"
echo "index     : $index"

confirm

for db in $(cat $dblist) ; do

	for host in $hosts; do

		port="3306"

		if [[ "$host" =~ ^(.+):([0-9]+)$ ]]; then
			host="${BASH_REMATCH[1]}"
			port="${BASH_REMATCH[2]}"
		fi

		echo -n "host $host, port $port, database $db..."

		sql="select * from statistics where table_schema = '$db' and table_name = '$table' and index_name = '$index'"
		state=$(mysql -u $user -h $host -P $port --skip-column-names information_schema -e "$sql" | wc -l)

		if [ $state -gt 0 ]; then
			echo "present"
		else
			echo "missing"
		fi

	done

done
