#!/bin/sh

/usr/sbin/useradd --home-dir /var/lib/proxysql --system --no-create-home --user-group proxysql || true
/bin/chown proxysql /var/lib/proxysql
/bin/chown proxysql /run/proxysql

INITINSTALL

exit 0
