#!/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RETEVAL=0
# DB where data will be stored
DATABASE="zarcillo"
TABLE="nil_grants"
DB_HOST="db1215.eqiad.wmnet"
DB_USER="root"

# DB from where to get the list of live hosts
SOURCE_DB_HOST="db1215.eqiad.wmnet"
SOURCE_DB="zarcillo"
SOURCE_DB_TABLE="instances"
# Timeout in seconds
DB_TIMEOUT=5

MYSQL="`which db-mysql`"

if [ ! -f "$MYSQL" ]
then
    echo "db-mysql is not present"
    exit 1
fi

case "$1" in
  "")
    echo "Usage: $0 --empty-password --unused-grants"
    RETVAL=1
    ;;
  --empty-password)

# Empty the table before start
$MYSQL $DB_HOST $DATABASE -e " truncate table $TABLE;"

$MYSQL $SOURCE_DB_HOST $SOURCE_DB -e "select server,port from $SOURCE_DB_TABLE;" -BN | while read server port
do

# The following IPs are whitelisted as they are proxies and we cannot remove haproxy or set a password for it see: T199061#4426646

	$MYSQL $server:$port -e "select User,Host from mysql.user where password='' and plugin !='unix_socket' and user !='labsdbuser' and user !='research_role' and user !='mariadb.sys' and host NOT IN ('10.64.37.14','10.64.37.15','10.64.16.18','10.192.0.129','10.192.16.9','10.64.0.135','10.192.32.137','10.64.16.14','10.64.48.42','10.64.37.27','10.64.48.43', '10.64.32.180', '10.64.0.134','10.64.16.19','10.64.32.179','10.192.48.47','10.64.0.15','10.64.32.10');" -BN | while read user host
	do
		echo "set session binlog_format=row; INSERT INTO $TABLE VALUES ('${server}','${port}','${user}','${host}',NOW()) ON DUPLICATE KEY UPDATE last_update = NOW();" | $MYSQL $DB_HOST -u $DB_USER $DATABASE
	done
done


# Check and report existing users
# Not sending any kind of username/host on email to avoid any kind hint of over email

USERS_COUNT=$($MYSQL $DB_HOST -u $DB_USER $DATABASE -e "select count(*) from nil_grants;" -BN)

if [ $USERS_COUNT != 0 ]
then
	echo "There are users with empty passwords. Please check $DATABASE.$TABLE table on $DB_HOST - this email address isn't monitored"  | mail -s "Users with empty passwords detected" sre-data-persistence@wikimedia.org -aFrom:checkusers@wikimedia.org
fi

 ;;

--unused-grants)
  echo "unused-grants report"

$MYSQL $SOURCE_DB_HOST $SOURCE_DB -e "select server,port from $SOURCE_DB_TABLE;" -BN | while read server port
do
 echo "======$server:$port======="
 $MYSQL $server:$port -e "select User,Host from mysql.user where host like '208.80.154.%' or host='208.80.152.161' or host='208.80.152.165' or user='globaldev' or user='prefetch' or user='test' or user='repl'" -BN
done

;;
esac
exit $RETVAL
