#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <hostname>"
  exit 1
fi

HOST="$1"

# check screen
if [ -z "$STY" ]; then
  echo "This script must be run inside a 'screen' session."
  exit 1
fi

sudo cookbook sre.hosts.downtime --hours 1 -r "Maintenance" "${HOST}"*

sudo dbctl instance "$HOST" depool
sudo dbctl config commit -b -m "Depool $HOST for upgrade"
if [ $? -ne 0 ]; then
  echo "dbctl commit failed. Aborting."
  exit 1
fi

sudo cumin --force "${HOST}"* 'systemctl stop mariadb; apt full-upgrade -y'

sudo cookbook sre.hosts.reboot-single "$HOST"*

sudo cumin --force "${HOST}"* 'systemctl start mariadb; mysql_upgrade --force'

sudo /home/marostegui/git/software/dbtools/repool "$HOST" 10 25 50 75 100
