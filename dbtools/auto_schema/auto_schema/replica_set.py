import sys

import requests

from .config import Config
from .db import Db
from .host import Host


class ReplicaSet(object):
    def __init__(self, replicas, section):
        self.config = Config()
        if replicas is None:
            replicas = self.config.get_replicas(section)
        self.replicas = replicas
        self.section = section
        self.pooled_replicas = self.config.get_replicas(section)
        self.section_masters = self.config.get_section_masters(section)
        # TODO: Add a check to avoid running schema change on master of another
        # section
        self.dbs = []

    def sql_on_each_replica(self, sql, ticket=None,
                            should_depool=True, downtime_hours=4, check=None):
        for host in self._per_replica_gen(
                ticket, should_depool, downtime_hours):
            if check:
                if check(host):
                    print('Already applied, skipping')
                    continue
            sql_for_this_host = sql
            if not host.has_replicas() or self.is_master_of_active_dc(host):
                sql_for_this_host = 'set session sql_log_bin=0; ' + sql_for_this_host

            res = host.run_sql(sql_for_this_host)

            if 'error' in res.lower():
                print('PANIC: Schema change errored. Not repooling and stopping')
                sys.exit()
            if check and not check(host) and '--run' in sys.argv:
                print('PANIC: Schema change was not applied. Not repooling and stopping')
                sys.exit()

    def sql_on_each_db_of_each_replica(
            self, sql, ticket=None, should_depool=True, downtime_hours=4, check=None):
        for host in self._per_replica_gen(
                ticket, should_depool, downtime_hours):
            sql_for_this_host = sql
            if not host.has_replicas() or self.is_master_of_active_dc(host):
                sql_for_this_host = 'set session sql_log_bin=0; ' + sql_for_this_host

            res = self.run_sql_per_db(host, sql_for_this_host, check)

            if 'error' in res.lower():
                print('PANIC: Schema change errored. Not repooling')
                sys.exit()

    def _per_replica_gen(self, ticket, should_depool, downtime_hours):
        for replica in self.replicas:
            host = Host(replica, self.section)
            replicas_to_downtime = []
            if host.has_replicas():
                if not self.is_master_of_active_dc(host):
                    replicas_to_downtime = host.get_replicas(recursive=True)
                if '--include-masters' not in sys.argv:
                    replicas_to_question = ','.join([i.host for i in replicas_to_downtime])
                    question_mark = input(
                        'This host has these hanging replicas: {}, '
                        'Are you sure you want to continue? (y or yes): '
                        .format(replicas_to_question)).lower().strip()
                    if question_mark not in ['y', 'yes', 'si', 'ja']:
                        print(
                            'Ignoring {} as it has hanging replicas'.format(
                                host.host))
                        continue
            if str(should_depool).lower() == 'auto':
                should_depool_this_host = self.detect_depool(host)
            else:
                should_depool_this_host = should_depool

            # don't depool replicas that are not pooled in the first place
            # (dbstore, backup source, etc.)
            if replica not in self.pooled_replicas:
                should_depool_this_host = False

            # never depool the master:
            if replica in self.section_masters:
                should_depool_this_host = False

            if downtime_hours:
                host.downtime(
                    ticket,
                    str(downtime_hours),
                    replicas_to_downtime)
            if should_depool_this_host:
                host.depool(ticket)

            yield host
            if should_depool_this_host:
                host.repool(ticket)

    def get_dbs(self):
        if not self.dbs:
            if self.section.startswith('s'):
                url = 'https://noc.wikimedia.org/conf/dblists/{}.dblist'.format(
                    self.section)
                wikis = [i.strip() for i in requests.get(url).text.split(
                    '\n') if not i.startswith('#') and i.strip()]
                self.dbs = wikis
            else:
                # TODO: Build a way to get dbs of es and pc, etc.
                pass

        return self.dbs

    def run_sql_per_db(self, host, sql, check):
        res = ''
        for db_name in self.get_dbs():
            db = Db(host, db_name)
            if check:
                if check(db):
                    print('Already applied, skipping')
                    continue
            res += db.run_sql(sql)
            if check and '--run' in sys.argv:
                if not check(db):
                    print('Schema change was not applied, panic')
                    res += 'Error: Schema change was not applied, panic'
        return res

    def is_master_of_active_dc(self, host):
        if self.config.active_dc() != host.dc:
            return False
        if host.host.replace(':3306', '') not in [i.replace(
                ':3306', '') for i in self.section_masters]:
            return False
        return True

    def detect_depool(self, host):
        if self.config.active_dc() != host.dc:
            return False
        if host.host not in self.pooled_replicas:
            return False
        return True
