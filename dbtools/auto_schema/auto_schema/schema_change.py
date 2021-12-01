import sys
import os

from .replica_set import ReplicaSet


class SchemaChange(object):
    def __init__(self, replicas, section, command, check,
                 all_dbs, ticket, downtime_hours, should_depool):
        self.replica_set = ReplicaSet(replicas, section)
        self.command = command
        self.ticket = ticket
        self.downtime_hours = downtime_hours
        self.should_depool = should_depool
        self.check = check
        self.all_dbs = all_dbs

    def run(self):
        if '--run' in sys.argv and not os.environ.get('STY'):
            print('Schema changes must be put in a screen, exiting.')
            sys.exit()
        if self.all_dbs:
            self.replica_set.sql_on_each_db_of_each_replica(
                self.command,
                ticket=self.ticket,
                downtime_hours=self.downtime_hours,
                should_depool=self.should_depool,
                check=self.check)
        else:
            self.replica_set.sql_on_each_replica(
                self.command,
                ticket=self.ticket,
                downtime_hours=self.downtime_hours,
                should_depool=self.should_depool,
                check=self.check)
