#!/bin/bash
#
# Synchronize one table from Master to Slave

set -e

usage() {
    echo $0 --master-host=... --slave-host=... --master-db=... --slave-db=... --table...
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
tablename=""
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

    if [[ "$var" =~ ^--table=(.+) ]]; then
        tablename="${BASH_REMATCH[1]}"
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
[ "$tablename" ] || usage
[ "$mhost" ] || usage
[ "$shost" ] || usage

if [[ ! "$sdbname" =~ .+ ]]; then
    sdbname="$mdbname"
fi

mysql="mysql -h $shost -P $sport -u $user --compress --skip-column-names $sdbname"
mysqldump="mysqldump -h $mhost -P $mport -u $user --single-transaction --quick --compress --skip-triggers --hex-blob"
wheremd5="table_md5 = unhex(md5('${tablename}'))"

echo "table  : ${tablename}"
echo "master : ${mhost}:${mport} ${mdbname}"
echo "slave  : ${shost}:${sport} ${sdbname}"
echo "flags  : create:${docreate} full-sync:${fullsync} full-dump:${fulldump} interval:${interval}"

if [ $doprompt -eq 1 ]; then
    confirm
fi

badoptions="sed s/NO_AUTO_VALUE_ON_ZERO/NO_AUTO_VALUE_ON_ZERO,IGNORE_BAD_TABLE_OPTIONS/g"

if [ $docreate -eq 1 ]; then
    $mysqldump --no-data $mdbname $tablename | $badoptions | $mysql
    $mysql -e "replace into repl_tables (table_name) values ('${tablename}')"
    exit
fi

if [ $($mysql -e "select table_name from repl_tables where table_name = '${tablename}'" | wc -l) -eq 0 ]; then
    echo "ERROR: Table is not replicated on slave!" 1>&2
    exit
fi

if [ $fulldump -eq 1 ]; then
    $mysql -e "truncate table ${tablename};"
    $mysqldump --no-create-info $mdbname $tablename | $mysql
    exit
fi

if [ $fullsync -eq 1 ]; then
    if ! pt-table-sync --execute --verbose --no-check-slave --no-check-triggers --charset=binary \
        --no-check-child-tables --float-precision=3 --function=MD5 --where="repl_uuid is not null"\
        h=$mhost,P=$mport,u=$user,D=$mdbname,t=$tablename h=$shost,P=$sport,u=$user,D=$sdbname,t=$tablename; then
        echo "pt-table-sync $?" >&2
    fi
    exit
fi

if [ $($mysql -e "select is_free_lock('repl_${sdbname}_${tablename}')") -ne 1 ]; then
    echo "ERROR ${sdbname}.${tablename} already syncing." 1>&2
    exit 1
fi

chunkdump="$mysqldump --skip-opt --no-create-info --insert-ignore --extended-insert"
#chunkdump="$mysqldump --skip-opt --no-create-info --insert-ignore"

#time1=$($mysql -e "select ifnull(max(record_stamp), now() - interval 1 day) from repl_records where ${wheremd5}")
timesub="select * from repl_records where ${wheremd5} order by record_stamp desc limit 1"
time1=$($mysql -e "select ifnull(max(record_stamp), now() - interval 1 day) from (${timesub}) t where ${wheremd5}")

if [[ "$interval" =~ .+ ]]; then
    time1=$($mysql -e "select now() - interval ${interval}")
fi

# Process is, within one transaction:
# 1. Sync a chunk of repl_records from the Master, starting from our last known position.
# 2. Delete local copies of records that have changed by joining on repl_records (fairly efficient)
# 3. Bulk insert new versions of said records
# If records have been deleted upstream, #2 will get them.
# If records have been inserted or updated, #3 will get them.

echo -n "records from ${time1}... "

txn="tmp/${mdbname}_${tablename}.sql"
chunk="${wheremd5} and record_stamp >= '${time1}'"

echo "SELECT GET_LOCK('repl_${sdbname}_${tablename}', 86400); BEGIN;" >$txn

echo "delete from repl_records where ${chunk};" >>$txn
$chunkdump --where="${chunk}" $mdbname repl_records | { egrep '^INSERT' $tmp || true; } >>$txn

echo -n "delete t from ${tablename} t join repl_records d on t.repl_uuid = d.record_uuid" >>$txn
echo " where d.${wheremd5} and d.record_stamp >= '${time1}';" >>$txn

uuids="select distinct record_uuid from repl_records where ${chunk}"
$chunkdump --where="repl_uuid in ($uuids)" $mdbname $tablename | { egrep '^INSERT' $tmp || true; } >>$txn

echo "COMMIT;" >>$txn
$mysql <$txn >/dev/null

count=$($mysql -e "select count(*) from repl_records where ${chunk}")
echo "${count}"
