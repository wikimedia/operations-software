function usage {
   echo "reimport_from_master.sh <master> <slave> <database> <table>"
}

MASTER=$1
SLAVE=$2
DATABASE=$3
TABLE=$4

if [[ $MASTER == "" ]]; then
   usage
   exit
fi
if [[ $SLAVE == "" ]]; then
   usage
   exit
fi
if [[ $DATABASE == "" ]]; then
   usage
   exit
fi
#if [[ $TABLE == "" ]]; then
#   usage
#   exit
#fi

TMPFILE="import_$DATABASE.$TABLE.sql.gz"

echo "Warming up the original table..." &&
mysqldump --single-transaction --routines --quick -h $MASTER $DATABASE $TABLE | pv > /dev/null &&
echo "Stopping the slave..." &&
mysql -h $SLAVE -e "STOP SLAVE" &&
echo "Exporting the table..." &&
mysqldump --routines --quick --skip-disable-keys -h $MASTER $DATABASE $TABLE | pv | pigz -c > $TMPFILE &&
echo "Importing it back..." &&
(echo "SET SESSION SQL_LOG_BIN=0;"; pv $TMPFILE | pigz -c -d ) | mysql -h $SLAVE $DATABASE &&
rm $TMPFILE &&
mysql -h $SLAVE
