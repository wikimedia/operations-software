#!/bin/bash
set -e
############## USER AND PASSWORD TO BE CHANGED ##############
USER=""
PASSWORD=""
#############################################################

# Host and database to grab the hosts from
TENDRIL_HOST="db1115.eqiad.wmnet"
DATABASE="tendril"

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
        mysql.py -h $TENDRIL_HOST $DATABASE -e "select host,port from servers" -BN | grep codfw | while read host port; do echo "Updating: **$host:$port**" ; mysql.py --connect-timeout=5  -h$host -P$port -e "set session sql_log_bin=0; select user,host from mysql.user where user='$USER'; update mysql.user SET Password=PASSWORD('$PASSWORD') where User='$USER'; FLUSH PRIVILEGES;";done
  fi
    ;;
  eqiad)
  read -p "Please confirm you want to change the password for: the user $USER in EQIAD [y/n]" -n 1 -r
  echo
  if [[ "$REPLY" = y ]]
  then
	echo "Changing password for $USER in EQIAD"
        mysql.py -h $TENDRIL_HOST $DATABASE -e "select host,port from servers" -BN | grep eqiad | while read host port; do echo "Updating: **$host:$port**" ; mysql.py --connect-timeout=5  -h$host -P$port -e "set session sql_log_bin=0; select user,host from mysql.user where user='$USER'; update mysql.user SET Password=PASSWORD('$PASSWORD') where User='$USER'; FLUSH PRIVILEGES;";done
  fi
    ;;
esac
