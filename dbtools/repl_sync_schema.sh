#!/bin/bash

set -e

usage() {
    echo $0 --master-host=... --slave-host=... --master-db=... --slave-db=...
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
mhost=""
mport="3306"
shost=""
sport="3306"
mdbname=""
sdbname=""
fullsync=0
fulldump=0
docreate=0
doprompt=1
interval=""

for var in "$@"; do

    if [[ "$var" =~ ^--master-host=(.+) ]]; then
        mhost="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--master-port=(.+) ]]; then
        mport="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--slave-host=(.+) ]]; then
        shost="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--slave-port=(.+) ]]; then
        sport="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--user=(.+) ]]; then
        user="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--master-db=(.+) ]]; then
        mdbname="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--slave-db=(.+) ]]; then
        sdbname="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--full-sync ]]; then
        fullsync=1
    fi

    if [[ "$var" =~ ^--full-dump ]]; then
        fulldump=1
    fi

    if [[ "$var" =~ ^--interval=(.+) ]]; then
        interval="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--create ]]; then
        docreate=1
    fi

    if [[ "$var" =~ ^--yes ]]; then
        doprompt=0
    fi

done

[ "$mdbname"   ] || usage
[ "$mhost" ] || usage
[ "$shost" ] || usage

if [[ ! "$sdbname" =~ .+ ]]; then
    sdbname="$mdbname"
fi

mysql="mysql -h $shost -P $sport -u $user --skip-column-names $sdbname"

tables="select t.table_name from information_schema.tables t"
tables="$tables left join $sdbname.repl_ignore i on t.table_name = i.table_name"
tables="$tables where t.table_schema = '$sdbname' and t.table_name not like 'repl\_%' and i.table_name is null"

echo "master : ${mhost}:${mport} ${mdbname}"
echo "slave  : ${shost}:${sport} ${sdbname}"
echo "flags  : create:${docreate} full-sync:${fullsync} full-dump:${fulldump} interval:${interval}"

yes="--yes"

if [ $doprompt -eq 1 ]; then
    confirm
    yes=""
fi

if [ $docreate -eq 1 ]; then
    mysql="mysql -h $mhost -P $mport -u $user --skip-column-names $mdbname"
    for tablename in $($mysql -e "select table_name from repl_tables"); do
        ./repl_sync_table.sh --master-host=$mhost --master-port=$mport --slave-host=$shost --slave-port=$sport \
            --user=$user --master-db=$mdbname --slave-db=$sdbname --table=$tablename --create $yes
    done
    exit
fi

if [ $fulldump -eq 1 ]; then
    echo "not implemented" 1>&2
    exit
fi

if [ $fullsync -eq 1 ]; then
    for tablename in $($mysql -e "$tables"); do
        ./repl_sync_table.sh --master-host=$mhost --master-port=$mport --slave-host=$shost --slave-port=$sport \
            --user=$user --master-db=$mdbname --slave-db=$sdbname --table=$tablename --full-sync $yes
    done
    exit
fi

for tablename in $($mysql -e "$tables"); do
    ./repl_sync_table.sh --master-host=$mhost --master-port=$mport --slave-host=$shost --slave-port=$sport \
        --user=$user --master-db=$mdbname --slave-db=$sdbname --table=$tablename --interval="$interval" $yes
done
