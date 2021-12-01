from auto_schema.replica_set import ReplicaSet

dc = 'eqiad'
section = 's5'
# Don't add set session sql_log_bin=0;
command = 'REVOKE DROP ON \\`%wik%\\`.* FROM wikiadmin@\'10.%\';'
# DO NOT FORGET to set the right port if it's not 3306
replicas = None


replica_set = ReplicaSet(replicas, section, dc)
replica_set.sql_on_each_replica(
    command, ticket=None, downtime_hours=None, should_depool=None)
