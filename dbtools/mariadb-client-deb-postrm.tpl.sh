#!/bin/sh

basedir="BASEDIR"

update-alternatives --remove mariadb $basedir/bin/mysql
update-alternatives --remove mariadbdump $basedir/bin/mysqldump

update-alternatives --remove mysql $basedir/bin/mysql
update-alternatives --remove mysqldump $basedir/bin/mysqldump

# Handled automatically
# rmdir --ignore-fail-on-non-empty /usr/local/bin

exit 0
