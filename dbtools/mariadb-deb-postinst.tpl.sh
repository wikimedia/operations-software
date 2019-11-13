#!/bin/sh

basedir="BASEDIR"

mkdir -p /usr/local/bin
update-alternatives --install /usr/local/bin/mariadb mariadb $basedir/bin/mysql 1
update-alternatives --install /usr/local/bin/mariadbdump mariadbdump $basedir/bin/mysqldump 1

update-alternatives --install /usr/local/bin/mysql mysql $basedir/bin/mysql 1
update-alternatives --install /usr/local/bin/mysqldump mysqldump $basedir/bin/mysqldump 1

update-alternatives --install /usr/local/bin/mysqlbinlog mysqlbinlog $basedir/bin/mysqlbinlog 1
update-alternatives --install /usr/local/bin/mysql_upgrade mysql_upgrade $basedir/bin/mysql_upgrade 1
update-alternatives --install /usr/local/bin/mysqlcheck mysqlcheck $basedir/bin/mysqlcheck 1

update-alternatives --install /usr/local/bin/xtrabackup xtrabackup $basedir/bin/mariabackup 1

INITINSTALL

exit 0
