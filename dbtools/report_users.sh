#!/bin/bash

# Set the environment variables
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RETEVAL=0
# Database configurations
DATABASE="zarcillo"
TABLE="nil_grants"
DB_HOST="db1215.eqiad.wmnet"
DB_USER="cumin2024"

SOURCE_DB_HOST="db1215.eqiad.wmnet"
SOURCE_DB="zarcillo"
SOURCE_DB_TABLE="instances"
DB_TIMEOUT=5

MYSQL="`which db-mysql`"

# IPs to be whitelisted
WHITELISTED_IPS=(
    '10.64.32.180'
    '10.64.32.179'
    '10.192.48.47'
    '10.64.0.15'
    '10.64.32.10'
    '10.64.16.7'
    '10.64.48.33'
    '10.64.130.15'
    '10.64.134.16'
    '10.64.151.2'
    '10.64.150.4'
    '10.64.16.113'
    '10.64.32.70'
    '10.192.23.11'
    '10.192.21.11'
    '10.192.32.105'
    '10.192.48.31'
)
# Check if db-mysql is available
if ! command -v "$MYSQL" &> /dev/null; then
    echo "Command 'db-mysql' not found or not executable."
    exit 1
fi

# Handle script arguments
case "$1" in
  "")
    echo "Usage: $0 --empty-password --unused-grants"
    RETVAL=1
    ;;
  --empty-password)
    # Clear the table before starting
    $MYSQL $DB_HOST $DATABASE -e "truncate table $TABLE;"

    # Fetch servers and ports, check for empty passwords
    $MYSQL $SOURCE_DB_HOST $SOURCE_DB -e "select server,port from $SOURCE_DB_TABLE;" -BN | while read server port
    do
        # Construct the query for users with empty passwords, excluding whitelisted IPs
        exclude_hosts=""
        for ip in "${WHITELISTED_IPS[@]}"
        do
            exclude_hosts+="and host !='$ip' "
        done

        $MYSQL $server:$port -e "select User,Host from mysql.user where password='' and plugin !='unix_socket' and user !='labsdbuser' and user !='research_role' and user !='mariadb.sys' $exclude_hosts" -BN | while read user host
        do
            echo "set session binlog_format=row; INSERT INTO $TABLE VALUES ('${server}','${port}','${user}','${host}',NOW()) ON DUPLICATE KEY UPDATE last_update = NOW();" | $MYSQL $DB_HOST -u $DB_USER $DATABASE
        done
    done

    # Check and report existing users with empty passwords
    USERS_COUNT=$($MYSQL $DB_HOST -u $DB_USER $DATABASE -e "select count(*) from nil_grants;" -BN)

    if [ "${USERS_COUNT:-0}" != "0" ]; then
        echo "There are users with empty passwords. Please check $DATABASE.$TABLE table on $DB_HOST - this email address isn't monitored" | mail -s "Users with empty passwords detected" sre-data-persistence@wikimedia.org -aFrom:checkusers@wikimedia.org
    fi
    ;;
  --unused-grants)
    echo "unused-grants report"

    # Fetch servers and ports, check for unused grants
    $MYSQL $SOURCE_DB_HOST $SOURCE_DB -e "select server,port from $SOURCE_DB_TABLE;" -BN | while read server port
    do
        echo "======$server:$port======="
        $MYSQL $server:$port -e "select User,Host from mysql.user where host like '208.80.154.%' or host='208.80.152.161' or host='208.80.152.165' or user='globaldev' or user='prefetch' or user='test' or user='repl'" -BN
    done
    ;;
esac

exit $RETVAL
