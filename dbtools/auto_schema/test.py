from auto_schema.config import Config
from auto_schema.host import Host
from auto_schema.replica_set import ReplicaSet

dc = 'eqiad'
section = 's4'
replica = None


config = Config()
if not replica:
    replicas = config.get_replicas(section) + ['db1138:3306'] + ['db1138']
else:
    replicas = [replica]
for replica in replicas:
    db = Host(replica, section)

replica_set = ReplicaSet(replicas, section)
for host in replica_set._per_replica_gen(None, 'auto'):
    print(replica_set.detect_depool(host))
