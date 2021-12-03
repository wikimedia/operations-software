import re
import sys
import time

from .bash import run


# NOTE: Hosts here are the same sense of instance.
# Meaning an actual host can have multiple of them
# Do not shutdown or general actions using this class on a
# multiinstance host
class Host(object):
    def __init__(self, host, section):
        self.host = host
        self.section = section
        if re.findall(r'\w1\d{3}', host):
            self.dc = 'eqiad'
        else:
            self.dc = 'codfw'
        self.fqn = '{}.{}.wmnet'.format(host.split(':')[0], self.dc)
        self.dbs = []

    def run_sql(self, sql):
        args = '-h{} -P{}'.format(self.host.split(':')[0], self.host.split(':')[
                                  1]) if ':' in self.host else '-h' + self.host
        if '"' in sql:
            sql = sql.replace('"', '\\"')
        if '`' in sql:
            sql = sql.replace('`', '\\`')
        if '\n' in sql:
            sql = sql.replace('\n', ' ')
        if not sql.strip().endswith(';'):
            sql += ';'
        return run('mysql.py {} -e "{}"'.format(args, sql))

    def run_on_host(self, command):
        if '"' in command:
            command = command.replace('"', '\\"')
        return run('cumin {} "{}"'.format(self.fqn, command))

    def depool(self, ticket):
        # TODO: check if it's depoolable
        run('dbctl instance {} depool'.format(self.host))
        run('dbctl config commit -b -m "Depooling {} ({})"'.format(self.host, ticket))
        while True:
            if self.has_traffic() and '--run' in sys.argv:
                print('Sleeping for the traffic to drain')
                time.sleep(60)
            else:
                break

    def has_traffic(self):
        # TODO: Make the users check more strict and include root
        result = self.run_sql(
            'SELECT * FROM information_schema.processlist WHERE User like \'%wiki%\';')
        return bool(result)

    def get_replag(self):
        query_res = self.run_sql("""
        SELECT greatest(0, TIMESTAMPDIFF(MICROSECOND, max(ts), UTC_TIMESTAMP(6)) - 500000)/1000000 AS lag
        FROM heartbeat.heartbeat
        WHERE datacenter='{}'
        GROUP BY shard
        HAVING shard = '{}';
        """.replace('\n', '').format(self.dc, self.section))
        replag = None
        if not query_res:
            return 1000 if '--run' in sys.argv else 0
        for line in query_res.split('\n'):
            if not line.strip():
                continue
            count = line.strip()
            if count == 'lag':
                continue
            try:
                count = float(count)
            except BaseException:
                continue
            replag = count
        return replag

    def repool(self, ticket):
        replag = 1000
        while replag > 1:
            replag = self.get_replag()
            if ((replag is None) or (replag > 1)) and '--run' in sys.argv:
                print('Waiting for replag to catch up')
                time.sleep(60)

        for percent in [10, 25, 75, 100]:
            run('dbctl instance {} pool -p {}'.format(self.host, percent))
            comment = 'Repooling after maintenance {}'.format(self.host)
            # Only comment in the ticket for first and last repool
            if percent in [10, 100]:
                comment += ' ({})'.format(ticket)
            run('dbctl config commit -b -m "{}"'.format(comment))
            if '--run' in sys.argv and percent != 100:
                print('Waiting for the next round')
                time.sleep(900)

    def downtime(self, ticket, hours, more_to_downtime=[]):
        more_to_downtime.append(self)
        hosts = ','.join([i.fqn for i in more_to_downtime])
        run('cookbook sre.hosts.downtime --hours {} -r "Maintenance {}" {}'.format(hours, ticket, hosts))

    def has_replicas(self):
        return self.run_sql('show slave hosts;').strip() != ''

    def get_replicas(self, recursive=False):
        res = self.run_sql('show slave hosts;')
        hosts = [
            Host('{}:{}'.format(i[0], i[1]), self.section)
            for i in re.findall(r'(\S+)\.(?:eqiad|codfw)\.wmnet\s*(\d+)', res)
        ]
        if not recursive:
            return hosts
        replicas_to_check = hosts.copy()
        while replicas_to_check:
            replica_replicas = replicas_to_check.pop().get_replicas(False)
            hosts += replica_replicas.copy()
            replicas_to_check += replica_replicas.copy()

        return hosts
