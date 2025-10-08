#!/bin/bash

# Check if a hostname was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <hostname> (e.g. db2157)"
  exit 1
fi

HOST="$1"

# Check if we're inside a screen session
if [ -z "$STY" ]; then
  echo "This script must be run inside a 'screen' session."
  exit 1
fi


read -p "Was the Puppet change merged before this operation? (yes/y to continue): " CONFIRM
if [[ "$CONFIRM" != "yes" && "$CONFIRM" != "y" ]]; then
  echo "Please merge the Puppet change before proceeding."
  exit 1
fi

# downtime
sudo cookbook sre.hosts.downtime --hours 1 -r "Maintenance" "${HOST}"*

# Depool the host
sudo dbctl instance "$HOST" depool
sudo dbctl config commit -b -m "Depool $HOST for migration to mariadb 10.11"

# Stop mariadb, remove old version, run puppet, restart mariadb, and re-enable replication
sudo cumin --force "${HOST}"* 'systemctl stop mariadb; apt-get remove --purge wmf-mariadb106 -y ; run-puppet-agent ; systemctl start mariadb ; mysql_upgrade ; mysql -e "start slave"'

# Wait for 5 minutes for replag
sleep 300

# Gradually repool the host
sudo /home/marostegui/git/software/dbtools/repool "$HOST" 10 25 50 75 100
