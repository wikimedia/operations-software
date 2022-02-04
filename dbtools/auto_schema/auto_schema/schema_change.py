import os
import sys

from .db import Db
from .logger import Logger
from .replica_set import ReplicaSet


class SchemaChange(object):
    def __init__(self, replicas, section, command, check,
                 all_dbs, ticket, downtime_hours):
        self.replica_set = ReplicaSet(replicas, section)
        self.command = command
        self.ticket = ticket
        self.downtime_hours = downtime_hours
        self.check = check
        self.all_dbs = all_dbs
        self.logger = Logger(ticket)

    def run(self):
        if '--run' in sys.argv and not os.environ.get('STY'):
            self.logger.log_file('Schema changes must be put in a screen, exiting.')
            sys.exit()
        self.logger.log_file('Starting schema change on {}'.format(
            ','.join([i.host for i in self.replica_set.replicas])))
        self.logger.log_file('SQL of schema change: ' + self.command)
        if self.all_dbs:
            self.sql_on_each_db_of_each_replica(
                self.command,
                ticket=self.ticket,
                downtime_hours=self.downtime_hours,
                check=self.check)
        else:
            self.sql_on_each_replica(
                self.command,
                ticket=self.ticket,
                downtime_hours=self.downtime_hours,
                check=self.check)
        self.logger.log_file('End of schema change on {}'.format(
            ','.join([i.host for i in self.replica_set.replicas])))

    def sql_on_each_replica(self, sql, ticket=None,
                            downtime_hours=4, check=None):
        for host in self.replica_set._per_replica_gen(
                ticket, downtime_hours):
            if check:
                if check(host):
                    self.logger.log_file('Already applied on {}, skipping'.format(host.host))
                    continue
            self.logger.log_file('Start of schema change sql on {}'.format(host.host))
            sql_for_this_host = sql
            host.run_sql('stop slave;')
            if not host.has_replicas() or self.replica_set.is_master_of_active_dc(host):
                sql_for_this_host = 'set session sql_log_bin=0; ' + sql_for_this_host

            res = host.run_sql(sql_for_this_host)
            self.logger.log_file('End of schema change sql on {}'.format(host.host))
            host.run_sql('start slave;')

            if 'error' in res.lower():
                self.logger.log_file('PANIC: Schema change errored. Not repooling and stopping')
                sys.exit()
            if check and not check(host) and '--run' in sys.argv:
                self.logger.log_file('PANIC: Schema change was not applied. Not repooling and stopping')
                sys.exit()

    def sql_on_each_db_of_each_replica(
            self, sql, ticket=None, downtime_hours=4, check=None):
        for host in self.replica_set._per_replica_gen(
                ticket, downtime_hours):
            sql_for_this_host = sql
            if not host.has_replicas() or self.replica_set.is_master_of_active_dc(host):
                sql_for_this_host = 'set session sql_log_bin=0; ' + sql_for_this_host

            self.logger.log_file('Start of schema change sql on {}'.format(host.host))
            res = self.run_sql_per_db(host, sql_for_this_host, check)
            self.logger.log_file('End of schema change sql on {}'.format(host.host))

            if 'error' in res.lower():
                self.logger.log_file('PANIC: Schema change errored. Not repooling')
                sys.exit()

    def run_sql_per_db(self, host, sql, check):
        res = ''
        host.run_sql('stop slave;')
        for db_name in self.replica_set.get_dbs():
            db = Db(host, db_name)
            if check:
                if check(db):
                    self.logger.log_file('Already applied on {} in {}, skipping'.format(db_name, host.host))
                    continue
            res += db.run_sql(sql)
            if check and '--run' in sys.argv:
                if not check(db):
                    self.logger.log_file('Schema change was not applied on {} in {}'.format(db_name, host.host))
                    res += 'Error: Schema change was not applied'
                else:
                    self.logger.log_file('Schema change finished on {} in {}'.format(db_name, host.host))
        host.run_sql('start slave;')
        return res
