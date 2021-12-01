

import sys
import time

from auto_schema.config import Config
from auto_schema.host import Host

dc = 'eqiad'
section = 's4'
ticket = 'T296143'
replicas = []

config = Config(dc)
if not replicas:
    replicas = config.get_replicas(section)

for replica in replicas:
    # TODO: Handle multiinstance
    db = Host(replica, section)
    db.downtime(ticket, 24)
    db.depool(ticket)
    db.run_sql('stop slave; SET GLOBAL innodb_buffer_pool_dump_at_shutdown = OFF;')
    db.run_on_host('systemctl stop mariadb')
    db.run_on_host('apt full-upgrade -y')
    db.run_on_host('umount /srv')
    db.run_on_host('swapoff -a')
    db.run_on_host('reboot')
    if '--run' in sys.argv:
        time.sleep(900)
    db.run_on_host(
        'systemctl set-environment MYSQLD_OPTS="--skip-slave-start"')
    db.run_on_host('systemctl start mariadb')
    db.run_on_host('mysql_upgrade')
    db.run_sql('start slave;')
    db.repool(ticket)
