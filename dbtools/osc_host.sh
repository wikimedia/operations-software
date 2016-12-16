#!/bin/bash
#
# Online (mostly) Schema Changes
# Started as Asher's script to wrap pt-online-schema-change.
# Stolen and rebuilt by Sean over time to:
# - Do more safety checks. And then some.
# - Support both pt-osc and regular DDL with ALTER [ONLINE]
# - Mostly not break our slightly odd replication tree (sanitarium, labs, toolserver)
#
# !!! NOTE !!! If using this on a master consider using --no-replicate. If you cannot
# do so, then the schema change probably deserves a master rotation instead :-)
#
# !!! NOTE !!! Go read about table metadata locking during DDL in MariaDB 5.5.
# Be afraid. Be very afraid...

set -e

osctool=$(which pt-online-schema-change)

usage() {
	echo $0 --host=... --dblist=... --table... \"SQL\"
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
altersql=""
method="percona"
cleanup=0
warn=1
analyze=0

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

	# percona toolkit or straight DDL
	if [[ "$var" =~ ^--method=(.+) ]]; then
		method="${BASH_REMATCH[1]}"
	fi

	if [[ "$var" =~ ^--warn ]]; then
		warn=1
	fi

	if [[ "$var" =~ ^--no-warn ]]; then
		warn=0
	fi

	if [[ "$var" =~ ^--analyze ]]; then
		analyze=1
	fi

	if [[ "$var" =~ ^--no-analyze ]]; then
		analyze=0
	fi

	if [[ ! "$var" =~ ^-- ]]; then
		altersql="$var"
	fi

done

[ "$host"     ] || usage
[ "$table"    ] || usage
[ "$altersql" ] || usage

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

# valid method?
if [[ ! "$method" =~ ^(percona|ddl|ddlonline)$ ]]; then
	echo "invalid method"
	exit 1
fi

mysql="mysql --skip-ssl -h $host -u $user -P $port"

if ! $mysql -e "status"; then
	echo "Connect failed: $user@$host:$port"
	exit
fi

ptdryargs=""
ptargs=""
ddlargs="SET SESSION innodb_lock_wait_timeout=1; SET SESSION lock_wait_timeout=60; "
ptrep="--recurse=0"
ddlrep=""

for var in "$@"; do

	if [[ "$var" =~ ^--no-replicate ]]; then
		ptrep="--recurse=0 --set-vars=sql_log_bin=off"
		ddlrep="set session sql_log_bin=0;"
	fi

	if [[ "$var" =~ ^--replicate ]]; then
		ptrep="--recurse=1 --chunk-size-limit=10"
		ddlrep="set session sql_log_bin=1;"
	fi

	# pt-online-schema-change will try to panic when altering a primary key. Tell it that we
	# know about the risks and have decided to go for gold...
	if [[ "$var" =~ ^--primary-key ]]; then
		ptdryargs="$ptdryargs --no-check-alter"
		ptargs="$ptargs --no-check-alter"
	fi

	# Don't actually switch the new and old tables on completion, but await a sanity check
	# This is handy for checking data consistency and/or avoiding metadata locking pile-ups
	if [[ "$var" =~ ^--no-cleanup ]]; then
		# not in ptdryargs because --dry-run does not create triggers
		ptargs="$ptargs --no-swap-tables --no-drop-new-table --no-drop-old-table --no-drop-triggers"
		cleanup=1
	fi

done

slave=$($mysql --skip-column-names -e "show slave status" | wc -l)

if [ $slave -gt 0 ]; then
	ptrep="$ptrep --check-slave-lag=$host"
fi

ptdryargs="$ptdryargs $ptrep"
ptargs="$ptargs $ptrep"
ddlargs="$ddlargs $ddlrep"

echo "Host        : $host"
echo "Port        : $port"
echo "Databases   : ${dblist[@]}"
echo "Table       : $table"
echo "Alter       : $altersql"
echo "method      : $method"
echo "pt dry args : $ptdryargs"
echo "pt args     : $ptargs"
echo "ddl args    : $ddlargs"
echo "analyze     : $analyze"

confirm

for db in "${dblist[@]}"; do

	reconfirm=0
	echo
	echo "host: $host, database: $db"

	collision=$($mysql --skip-column-names $db -e "show tables like '_${table}_new'" | wc -l)

	if [ $collision -gt 0 ]; then
		echo "_${table}_new already exists!"
		confirm
	fi

	# dry run
	if [[ $method =~ ^ddl ]] || $osctool \
		--critical-load Threads_running=400 \
		--max-load Threads_running=300 \
		--dry-run \
		--alter-foreign-keys-method=none --force \
		--nocheck-replication-filters \
		--no-version-check \
		$ptdryargs \
		--alter "$altersql" \
		D=$db,t=$table,h=$host,P=$port,u=$user >/dev/null
	then

		if [ "$method" == "percona" ]; then
			# execute
			if $osctool --critical-load Threads_running=400 \
				--max-load Threads_running=300 \
				--execute \
				--alter-foreign-keys-method=none --force \
				--nocheck-replication-filters \
				--no-version-check \
				$ptargs \
				--alter "$altersql" \
				D=$db,t=$table,h=$host,P=$port,u=$user
			then
				if [ $cleanup -gt 0 ]; then
					echo "Ready for cleanup. Will do this:"
					sqlcom="$ddlrep rename table ${table} to _${table}_done, _${table}_new to ${table}"
					echo $sqlcom
					confirm
					$mysql $db -e "$sqlcom"
					sqlcom="$ddlrep drop trigger if exists pt_osc_${db}_${table}_ins"
					echo $sqlcom
					$mysql $db -e "$sqlcom"
					sqlcom="$ddlrep drop trigger if exists pt_osc_${db}_${table}_upd"
					echo $sqlcom
					$mysql $db -e "$sqlcom"
					sqlcom="$ddlrep drop trigger if exists pt_osc_${db}_${table}_del"
					echo $sqlcom
					$mysql $db -e "$sqlcom"
					sqlcom="$ddlrep drop table if exists _${table}_done"
					echo $sqlcom
					$mysql $db -e "$sqlcom"
				fi
				if [ $analyze -eq 1 ]; then
					echo "$ddlrep analyze table $table"
					$mysql $db -e "$ddlrep analyze table $table"
				fi
			else
				echo "WARNING $db : $table encountered problems"
				reconfirm=$warn
			fi

		elif [ "$method" == "ddl" ]; then
			echo "$ddlargs alter table $table $altersql"
			if ! $mysql $db -e "$ddlargs alter table $table $altersql"; then
				echo "WARNING $db : $table encountered problems"
				reconfirm=$warn
			fi

		elif [ "$method" == "ddlonline" ]; then
			echo "$ddlargs alter online table $table $altersql"
			if ! $mysql $db -e "$ddlargs alter online table $table $altersql"; then
				echo "WARNING $db : $table encountered problems"
				reconfirm=$warn
			fi
		fi

	else
		echo "SKIPPING $db : $table - dry-run encountered problems"
		reconfirm=$warn
	fi

	if [ $reconfirm -gt 0 ]; then
		confirm
	fi

done
