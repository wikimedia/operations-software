#!/bin/bash
# zarcillo host
HOST="db1215"

if [ -z "$1" ]; then
  echo "Usage: $0 <query>"
  exit 1
fi

query="$1"

hosts_and_ports=$(db-mysql $HOST -A zarcillo -e "select name,port from instances" -BN)

echo "$hosts_and_ports" | while read -r host port; do
  echo "Processing host: $host"
  db-mysql "$host" -e "$query"
done
