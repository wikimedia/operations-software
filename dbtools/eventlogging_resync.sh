#!/bin/bash

# Event Logging tables hold time-series data which is not updated, but may be purged.
# Every table includes a uuid and a timestamp.
#
# ./eventlogging_resync.sh dbstore1002 20150201000000

db='log'
ls="regexp '^[A-Z0-9].*[0-9]+$'"
mhost='m2-master'
shost="$1"
since="$2"

slave="mysql -h $shost --compress --skip-column-names"
master="mysql -h $mhost --compress --skip-column-names"
dump="mysqldump -h $mhost --skip-opt --single-transaction --quick --skip-triggers"
dumpdata="$dump --no-create-info --order-by-primary --insert-ignore --extended-insert --compress --hex-blob"
querytables="select table_name from information_schema.tables where table_schema = '$db' and table_name"

set -e

for table in $($master $db -e "$querytables $ls order by rand()"); do

    echo -n $table

    ts1="$since"
    ts2=$($master $db -e "select max(timestamp) from \`$table\`")

    if [ ! "$ts2" = "NULL" ]; then

        echo " $ts1 to $ts2"

        while [ $($slave -e "select if('$ts1'<'$ts2',1,0)") -eq 1 ]; do
            tsn=$($slave -e "select date_format('$ts1' + interval 1 hour, '%Y%m%d%H%i%s')")

            scount=$($slave $db -e "select count(*) from \`$table\` where timestamp >= '$ts1' and timestamp < '$tsn'")
            mcount=$($master $db -e "select count(*) from \`$table\` where timestamp >= '$ts1' and timestamp < '$tsn'")

            if [ $mcount -ne $scount ]; then 
                echo "$table $ts1:$tsn $mcount $scount"
                $dumpdata --insert-ignore --where="timestamp >= '$ts1' and timestamp < '$tsn'" $db "$table" | $slave $db
            fi
            ts1="$tsn"
        done
    else
        echo " empty"
    fi
done
