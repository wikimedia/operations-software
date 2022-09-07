import re
from .host import Host


class ReplicationDiscovery(object):
    def get_replicas(self, host: Host, recursive=False):
        raise NotImplementedError

    def has_replicas(self, host: Host):
        raise NotImplementedError


class HostReplicationDiscovery(ReplicationDiscovery):
    def get_replicas(self, host: Host, recursive=False):
        res = host.run_sql('show slave hosts;')
        hosts = [
            Host('{}:{}'.format(i[0], i[1]), host.section)
            for i in sorted(re.findall(r'(\S+)\.(?:eqiad|codfw)\.wmnet\s*(\d+)', res))
        ]
        if not recursive:
            return hosts
        replicas_to_check = hosts.copy()
        while replicas_to_check:
            replica_replicas = self.get_replicas(replicas_to_check.pop())
            hosts += replica_replicas.copy()
            replicas_to_check += replica_replicas.copy()

        return hosts

    def has_replicas(self, host: Host):
        return host.run_sql('show slave hosts;').strip() != ''
