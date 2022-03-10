import json
import sys
from collections import defaultdict

from wmflib.exceptions import WmflibError
from wmflib.interactive import ensure_shell_is_durable

from .db import Db
from .logger import Logger
from .replica_set import ReplicaSet


class SchemaChange(object):
    def __init__(self, replicas, section, command, check,
                 all_dbs, ticket, downtime_hours, skip=None):
        self.replica_set = ReplicaSet(replicas, section, skip)
        self.command = command
        self.check = check
        self.all_dbs = all_dbs
        self.check_only = '--check' in sys.argv
        self.logger = Logger(ticket)
        self.cases = defaultdict(list)
        if self.check_only:
            self.gen = self.replica_set.replicas
        else:
            self.gen = self.replica_set._per_replica_gen(
                ticket, downtime_hours)

    def run(self):
        if '--run' in sys.argv and not self.check_only:
            try:
                ensure_shell_is_durable()
            except WmflibError:
                self.logger.log_file('Schema changes must be done in screen/tmux/etc, exiting.')
                sys.exit(1)
        self.logger.log_file('Starting schema change on {}'.format(
            ','.join([i.host for i in self.replica_set.replicas])))
        self.logger.log_file('SQL of schema change: ' + self.command)
        if self.all_dbs:
            self.sql_on_each_db_of_each_replica(
                self.command,
                check=self.check)
        else:
            self.sql_on_each_replica(
                self.command,
                check=self.check)
        self.logger.log_file('End of schema change on {}'.format(
            ','.join([i.host for i in self.replica_set.replicas])))
        self.logger.log_file('Result: ' + json.dumps(self.cases))

    def sql_on_each_replica(self, sql, check=None):
        for host in self.gen:
            if check:
                if check(host):
                    self.logger.log_file('Already applied on {}, skipping'.format(host.host))
                    self.cases['already done'].append(host.host)
                    continue

            if self.check_only:
                self.cases['not done'].append(host.host)
                continue
            self.logger.log_file('Start of schema change sql on {}'.format(host.host))
            sql_for_this_host = sql
            host.run_sql('stop slave;')
            if self.replica_set.change_without_replication(host):
                sql_for_this_host = 'set session sql_log_bin=0; ' + sql_for_this_host

            res = host.run_sql(sql_for_this_host)
            self.logger.log_file('End of schema change sql on {}'.format(host.host))
            host.run_sql('start slave;')

            if 'error' in res.lower():
                self.cases['errored'].append(host.host)
                self.logger.log_file('PANIC: Schema change errored. Not repooling and stopping')
                break
            if check and not check(host) and '--run' in sys.argv:
                self.cases['errored'].append(host.host)
                self.logger.log_file('PANIC: Schema change was not applied. Not repooling and stopping')
                break

    def sql_on_each_db_of_each_replica(self, sql, check=None):
        for host in self.gen:
            sql_for_this_host = sql
            if self.replica_set.change_without_replication(host):
                sql_for_this_host = 'set session sql_log_bin=0; ' + sql_for_this_host

            self.logger.log_file('Start of schema change sql on {}'.format(host.host))
            res = self.run_sql_per_db(host, sql_for_this_host, check)
            self.logger.log_file('End of schema change sql on {}'.format(host.host))

            if 'error' in res.lower():
                self.cases['errored'].append(host.host)
                self.logger.log_file('PANIC: Schema change errored. Not repooling')
                break

    def run_sql_per_db(self, host, sql, check):
        res = ''
        if not self.check_only:
            host.run_sql('stop slave;')
        needed = False
        for db_name in self.replica_set.get_dbs():
            db = Db(host, db_name)
            if check:
                if check(db):
                    self.logger.log_file('Already applied on {} in {}, skipping'.format(db_name, host.host))
                    continue
            needed = True
            if self.check_only:
                continue
            res += db.run_sql(sql)
            if check and '--run' in sys.argv:
                if not check(db):
                    self.logger.log_file('Schema change was not applied on {} in {}'.format(db_name, host.host))
                    res += 'Error: Schema change was not applied'
                else:
                    self.logger.log_file('Schema change finished on {} in {}'.format(db_name, host.host))
        if not needed:
            self.cases['already done in all dbs'].append(host.host)
        else:
            self.cases['needed in some dbs'].append(host.host)
        if not self.check_only:
            host.run_sql('start slave;')
        return res
