#!/bin/bash

# Simple script to check if the section master in DEST_DC is correctly
# receiving heartbeat updates from the section master in SRC_DC.

set -euo pipefail

ZARCILLO_HOST=db1115

if [ $# -eq 0 ]; then
	echo "Usage:"
	echo "    ${0##*/} SECTION SRC_DC DEST_DC"
	exit 0
fi

section="${1:?}"; shift
src_dc="${1:?}"; shift
dest_dc="${1:?}"; shift

src_master=$(sudo -H mysql.py -A -BN -h $ZARCILLO_HOST zarcillo -e "select instance from masters where section='$section' and dc='$src_dc'")
#echo $src_master
src_master_fqdn=$(sudo -H mysql.py -A -BN -h $ZARCILLO_HOST zarcillo -e "select server from instances where name='$src_master'")
src_master_ip=$(getent hosts $src_master_fqdn | cut -f1 -d' ')
echo Source: $src_master_fqdn $src_master_ip

dest_master=$(sudo -H mysql.py -A -BN -h $ZARCILLO_HOST zarcillo -e "select instance from masters where section='$section' and dc='$dest_dc'")
echo Dest: $dest_master

sudo -H mysql.py -A -h $dest_master heartbeat -e "select * from heartbeat where server_id=inet_aton('$src_master_ip') order by ts desc limit 1"
