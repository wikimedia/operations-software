#!/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RETEVAL=0
case "$1" in
  "")
    echo "Options:"
    echo "check_depooled --all (to show all depooled hosts)"
    echo "check_depooled sX (to display depooled hosts for the given section. Values: s1,s2,s3,s4,s5,s6,s7,s8,wikitech"
    RETVAL=1
    ;;
  --all)
echo "All depooled hosts"
dbctl instance all get  | jq 'select(..|.pooled? == false)' | egrep "db" | awk -F "\"" '{print $2}'  | uniq | while read instance; do dbctl instance $instance get ; done

echo "To get more information about an specific host run: dbctl instance dbXXXX get"
;;
  $1)

  echo "Depooled hosts in $1"
dbctl instance all get | jq 'select(.. | .sections? | has("'$1'")) | select(.. |  .pooled? == false)'
;;
esac
exit $RETVAL
