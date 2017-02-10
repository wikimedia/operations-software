#!/bin/sh

basedir="BASEDIR"

mkdir -p /usr/local/bin
update-alternatives --install /usr/local/bin/mariadb mariadb $basedir/bin/mysql 10
update-alternatives --install /usr/local/bin/mariadbdump mariadbdump $basedir/bin/mysqldump 10

update-alternatives --install /usr/local/bin/mysql mysql $basedir/bin/mysql 10
update-alternatives --install /usr/local/bin/mysqldump mysqldump $basedir/bin/mysqldump 10

exit 0
