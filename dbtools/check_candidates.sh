#!/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RETVAL=0
case "$1" in
  "")
    echo "Options:"
    echo "check_candidates --all (to show all candidate masters hosts)"
    echo "check_candidates sX (to display candidate masters hosts for the given section. Values: s1,s2,s3,s4,s5,s6,s7,s8,wikitech"
    RETVAL=1
    ;;
  --all)
echo "All candidate masters hosts"
dbctl instance all get | jq 'select(.. | .candidate_master?)'

echo "To get more information about an specific host run: dbctl instance dbXXXX get"
;;
  $1)

  echo "Candidate masters in $1"
dbctl instance all get | jq 'select(.. | .sections? | has("'$1'")) | select(.. | .candidate_master?)'
;;
esac
exit $RETVAL
