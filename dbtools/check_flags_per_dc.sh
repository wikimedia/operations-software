#!/bin/bash
# Ugly one-liner, do not trust it too much :)
# DC to check
DC="eqiad"
echo
echo "If a section reports something unsual, inspect it deeper to find out which host it is"
echo
for i in s1 s2 s3 s4 s5 s6 s7 s8 x1 x2 pc1 pc2 pc3 es1 es2 es3 es4 es5
do

echo "== Check event_scheduler=OFF for $i in $DC ==="
/home/marostegui/section $i | grep -v clouddb | grep $DC | while read host port; do db-mysql $host:$port -e "show global variables like 'event_scheduler'" | grep -v Variable_name | grep -v ON; done

echo "== Check for non installed query killers in $i $DC (5=OK, 3=OK (masters) ==="
/home/marostegui/section $i | grep -v clouddb | grep -v pc | grep $DC | while read host port; do db-mysql $host:$port ops -e "show events" | wc -l ; done

echo "== Check for DISABLED events in $i $DC  ==="
/home/marostegui/section $i | grep -v clouddb | grep -v pc | grep $DC | while read host port; do db-mysql $host:$port ops -e "show events"| grep DISABLED ; done

echo "== Check for disabled GTID in $i $DC  ==="
/home/marostegui/section $i | grep $DC | while read host port; do db-mysql $host:$port -e "show slave status\G"| grep Using | grep -v Slave_Pos; done
done
