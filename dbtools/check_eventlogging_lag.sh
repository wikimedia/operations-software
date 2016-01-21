#!/bin/bash

server=$1
warnlag=3600 # seconds
critlag=86400
master='m4-master.eqiad.wmnet'

mysql -BN -A -h $master log -e "SELECT table_name FROM information_schema.tables WHERE table_schema = 'log' AND table_name rlike '^[a-zA-Z]+_[0-9]+$'" |
while read table; do
#  echo "Checking $table..."
  date1=$(mysql -BN -A -h $master log -e "SELECT max(\`timestamp\`) FROM \`$table\`")
#  echo "Last modification on $table on $master: $date"
  date2=$(mysql -BN -A -h $server log -e "SELECT max(\`timestamp\`) FROM \`$table\`")
#  echo "Last modification on $table on $server: $timestamp"
  if [ $date1 != "NULL" -a $date2 != "NULL" ]; then
    lag=$(($(date -d "${date1:0:8} ${date1:8:2}:${date1:10:2}:${date1:12:2}" +%s) - $(date -d "${date2:0:8} ${date2:8:2}:${date2:10:2}:${date2:12:2}" +%s)))
    if [[ "$lag" -gt "$critlag" ]]; then
      echo "[CRITICAL] $table lag > 1 day ($lag seconds)"
    else
      if [[ "$lag" -gt "$warnlag" ]]; then
        echo "[Warning] $table lag: $(date -d @$lag +%T)"
      else
        echo -n '' 
        #echo "$table lag: $lag seconds"
      fi
    fi
  fi
done

