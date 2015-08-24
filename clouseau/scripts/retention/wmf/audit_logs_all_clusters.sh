#!/bin/bash

# audit logs on all clusters

BASEDIR="/srv/audits/retention"

SCRIPTS="$BASEDIR/scripts"
DATE=`date +%Y%m%d`
OUTPUT="$BASEDIR/output/logs/$DATE"

mkdir -p $SCRIPTS $OUTPUT

clusters=`salt '*' --timeout 30 grains.item cluster | grep 'cluster:' | sort | uniq | mawk '{ print $2 }'`
if [ -z "$clusters" ]; then
    echo "failed to get list of clusters, exiting"
    exit 1
fi

for c in $clusters; do
    echo "doing CLUSTER: $c"
    outfile="$OUTPUT/${c}-logs-report.txt"
    count=0
    while true; do
        if [ -s "$outfile" ]; then
            echo "$c complete"
            break
        fi
        count=$(( $count+1 ))
	if [ $count -gt 5 ]; then
	    echo "still failing after 5 retries, going on to next cluster"
            rm -f "$outfile"
	    break
	fi
        echo python $SCRIPTS/audit_files.py -t "grain:cluster:$c" -a logs -d 2 -T 60 -o -r -m 400 into "$outfile"
        python $SCRIPTS/audit_files.py -t "grain:cluster:$c" -a logs -d 2 -T 60 -o -r -m 400 > "$outfile"
	sleep 5
    done
done


