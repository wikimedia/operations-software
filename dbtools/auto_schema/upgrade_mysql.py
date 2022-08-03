
from auto_schema.replica_set import ReplicaSet
from auto_schema.bash import run
from auto_schema.replication_discovery import HostReplicationDiscovery

section = 's4'
ticket = 'T296143'
replicas = None
replication_discovery = HostReplicationDiscovery()
replica_set = ReplicaSet(replicas, section)
for db in replica_set._per_replica_gen(ticket, 24):
    sqldata_paths = db.run_on_host('ls /srv/')
    if 'sqldata.' in sqldata_paths:
        # TODO: Handle multiinstance
        print('multiinstance, skipping')
        continue
    if replication_discovery.has_replicas(db):
        print('This host {} has replicas, skipping '.format(db.host))
        continue
    run('cookbook sre.mysql.upgrade {}'.format(db.fqn))
