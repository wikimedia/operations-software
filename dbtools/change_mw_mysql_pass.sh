#!/bin/bash
set -e
############## USER AND PASSWORD TO BE CHANGED ##############
USER=""
PASSWORD=""
#############################################################

# Host and database to grab the hosts from
TENDRIL_HOST="db1215.eqiad.wmnet"
DATABASE="tendril" # Tendril is gone, this needs changing to zarcillo database and the query needs to be re-done to grab the list of hosts from there https://phabricator.wikimedia.org/T297605

if [ -z "$USER" ] || [ -z "$PASSWORD" ]
then
	echo "USER and PASSWORD variables cannot be empty, please edit this script to set the user/password you want to change"
	exit 1
fi

case "$1" in
  "")
    echo "Usage: $0 [codfw,eqiad]"
    RETVAL=1
    ;;
  codfw)
  read -p "Please confirm you want to change the password for: the user $USER in CODFW [y/n]" -n 1 -r
  echo
  if [[ "$REPLY" = y ]]
  then
	echo "Changing password for $USER in CODFW"
        db-mysql $TENDRIL_HOST $DATABASE -e "select host,port from servers" -BN | grep codfw | while read host port; do echo "Updating: **$host:$port**" ; db-mysql $host:$port --connect-timeout=5 -e "set session sql_log_bin=0; select user,host from mysql.user where user='$USER'; update mysql.user SET Password=PASSWORD('$PASSWORD') where User='$USER'; FLUSH PRIVILEGES;";done
  fi
    ;;
  eqiad)
  read -p "Please confirm you want to change the password for: the user $USER in EQIAD [y/n]" -n 1 -r
  echo
  if [[ "$REPLY" = y ]]
  then
	echo "Changing password for $USER in EQIAD"
        db-mysql $TENDRIL_HOST $DATABASE -e "select host,port from servers" -BN | grep eqiad | while read host port; do echo "Updating: **$host:$port**" ; db-mysql $host:$port --connect-timeout=5 -e "set session sql_log_bin=0; select user,host from mysql.user where user='$USER'; update mysql.user SET Password=PASSWORD('$PASSWORD') where User='$USER'; FLUSH PRIVILEGES;";done
  fi
    ;;
esac
