#!/bin/bash

# audit home dirs on all clusters

BASEDIR="/srv/audits/retention"

SCRIPTS="$BASEDIR/scripts"
DATE=`date +%Y%m%d`
OUTPUT="$BASEDIR/output/homes/$DATE"

mkdir -p $SCRIPTS $OUTPUT

# for all clusters but misc:
clusters=`salt '*' --timeout 30 grains.item cluster | grep 'cluster:' | sort | uniq | mawk '{ print $2 }'`
if [ -z "$clusters" ]; then
    echo "failed to get list of clusters, exiting"
    exit 1
fi

for c in $clusters; do
    if [ "$c" == 'misc' ]; then
	continue
    fi

    echo "doing CLUSTER: $c"
    outfile="$OUTPUT/${c}-homes-final.txt"
    count=0
    while true; do
        if [ -s "$outfile" ]; then
            echo "$c complete"
            break
        fi
        count=$(( $count+1 ))
        if [ $count -gt 5 ]; then
            echo "still failing after 5 retries, going on to next group"
	    rm -f "$outfile"
            break
        fi
	echo python $SCRIPTS/audit_files.py -t "grain:cluster:$c" -a homes -d 2 -T 300  into "$outfile"
        python $SCRIPTS/audit_files.py -t "grain:cluster:$c" -a homes -d 2 -T 300 > "$outfile"
        sleep 5
    done
done

# for the misc cluster, all hosts together except for
# the statxxx hosts, they get done individually and with
# one homedir at a time

c='misc'
echo "CLUSTER: $c (no huge hosts)"
list=`salt --timeout 60 -G "cluster:${c}" test.ping | grep ':' | grep -v -e 'stat100[123]'`
if [ -z "$list" ]; then
    echo "failed to retrieve hostlist for cluster $c, giving up"
else
    list=`echo $list | sed -e 's/ /,/g; s/://g;'`

    outfile="$OUTPUT/misc-nohuge-homes-final.txt"
    count=0
    while true; do
        if [ -s "$outfile" ]; then
            echo "$c complete"
            break
        fi
        count=$(( $count+1 ))
        if [ $count -gt 5 ]; then
            echo "still failing after 5 retries, going on to next group"
	    rm -f "$outfile"
            break
        fi
        echo python $SCRIPTS/audit_files.py -t "list:${list}" -a homes -d 2 -T 300 into "$outfile"
        python $SCRIPTS/audit_files.py -t "list:${list}" -a homes -d 2 -T 300  > "$outfile"
        sleep 5
    done
fi

# these hosts have some very large homedirs, we do each homedir on
# each host separately
for h in stat1001.wikimedia.org stat1002.eqiad.wmnet stat1003.wikimedia.org; do
    homedirs=`salt "$h" cmd.run 'echo /home/*' | tail -n +2 | grep -v '*'`
    if [ -z "$homedirs" ]; then
	echo "no homedir list retrieved for $h, giving up"
	continue
    fi

    hostbase=`echo $h | mawk -F '.' '{ print $1 }'`
    outfile="$OUTPUT/misc-${hostbase}-homes-final.txt"
    rm -f $outfile
    outfile_tmp="${outfile}.tmp"
    for hdir in $homedirs; do
	count=0
        while true; do
            count=$(( $count+1 ))
            if [ $count -gt 5 ]; then
		echo "still failing after 5 retries, going on to next homedir"
		rm -f ${outfile_tmp}
		break
            fi
            echo python $SCRIPTS/audit_files.py -t $h -a homes -d 2 -f $hdir -T 300  into "${outfile_tmp}"
            python $SCRIPTS/audit_files.py -t $h -a homes -d 2 -f $hdir -T 300  > "${outfile_tmp}"
            if [ -s "${outfile_tmp}" ]; then
                echo "$hdir on $h complete"
                break
            fi
            sleep 10
        done
        cat "${outfile_tmp}" >> "$outfile"
        rm -f "${outfile_tmp}"
    done
done

