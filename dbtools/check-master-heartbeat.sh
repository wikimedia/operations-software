#!/bin/bash

# Simple script to check if the section master in DEST_DC is correctly
# receiving heartbeat updates from the section master in SRC_DC.

set -euo pipefail

ZARCILLO_HOST=db1115

if [ $# -ne 3 ]; then
    echo "Usage:"
    echo "    ${0##*/} SECTION SRC_DC DEST_DC"
    exit 0
fi

section="${1:?}"; shift
src_dc="${1:?}"; shift
dest_dc="${1:?}"; shift

src_master=$(sudo db-mysql $ZARCILLO_HOST -BN -A zarcillo -e "select instance from masters where section='$section' and dc='$src_dc'")
[ -n "$src_master" ] || { echo "ERROR: no master found for section $section in DC $src_dc"; exit 1; }

src_master_fqdn=$(sudo db-mysql $ZARCILLO_HOST -BN -A zarcillo -e "select server from instances where name='$src_master'")
[ -n "$src_master_fqdn" ] || { echo "ERROR: unable to find fqdn for $src_master"; exit 1; }

src_master_ip=$(getent hosts $src_master_fqdn | cut -f1 -d' ') || { echo "ERROR: unable to get IP of $src_master_fqdn"; exit 1; }
echo Source: $src_master_fqdn $src_master_ip

dest_master=$(sudo db-mysql $ZARCILLO_HOST -BN -A zarcillo -e "select instance from masters where section='$section' and dc='$dest_dc'")
[ -n "$dest_master" ] || { echo "ERROR: no master found for section $section in DC $dest_dc"; exit 1; }
echo Dest: $dest_master

sudo db-mysql $dest_master -A heartbeat -e "select * from heartbeat where server_id=inet_aton('$src_master_ip') order by ts desc limit 1"
