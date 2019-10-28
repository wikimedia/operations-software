#!/bin/sh

basedir="BASEDIR"

update-alternatives --remove mariadb $basedir/bin/mysql
update-alternatives --remove mariadbdump $basedir/bin/mysqldump

update-alternatives --remove mysql $basedir/bin/mysql
update-alternatives --remove mysqldump $basedir/bin/mysqldump

update-alternatives --remove mysqlbinlog $basedir/bin/mysqlbinlog
update-alternatives --remove mysql_upgrade $basedir/bin/mysql_upgrade
update-alternatives --remove mysqlcheck $basedir/bin/mysqlcheck

update-alternatives --remove xtrabackup $basedir/bin/mariabackup

# Handled automatically
# rmdir --ignore-fail-on-non-empty /usr/local/bin

INITRM

exit 0
