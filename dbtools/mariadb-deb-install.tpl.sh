#!/bin/sh

basedir="BASEDIR"

ln -sf $basedir/service /etc/init.d/mysql
ln -sf $basedir/service /etc/init.d/mariadb

ln -sf $basedir/bin/mysql /usr/local/bin/mariadb
ln -sf $basedir/bin/mysqldump /usr/local/bin/mariadbdump

ln -sf $basedir/bin/mysql /usr/local/bin/mysql
ln -sf $basedir/bin/mysqldump /usr/local/bin/mysqldump
