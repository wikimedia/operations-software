#!/bin/bash
COMPARE="/home/jynus/compare.py"
SECTION="/home/marostegui/section"
display_usage() {
	echo -e "Usage: section database table column"
	echo -e "example: s4 commonswiki change_tag ct_id"
	}

if [  $# != 4 ]
	then
		display_usage
		exit 1
fi
if [[ ( $# == "--help") ||  $# == "-h" ]]
	then
		display_usage
		exit 0
fi

if [ ! -f "$COMPARE" ]
then
    echo "compare.py on $COMPARE is not present"
    exit 1
fi

if [ ! -f "$SECTION" ]
then
    echo "compare.py on $SECTION is not present"
    exit 1
fi

echo "***********************************************************************************************************************************************"
echo "Reminder: double check your table isn't filtered (or ignore sanitarium hosts (db1124,db1125,db2094,db2095) as those will show up as differences"
echo "***********************************************************************************************************************************************"
# Ignoring dbstore1002 as it will be decommissioned and it is not in a very healthy state
# Ignoring labsdb hosts as compare.py doesn't support connecting to labs yet
HOSTS=`$SECTION $1 | egrep -v "dbstore1002|labsdb" | while read host port; do echo -n "$host:$port " ; done`
sleep 5

# $2=database
# $3=table
# $4=column

$COMPARE $2 $3 $4 $HOSTS
