from auto_schema.replication_discovery import HostReplicationDiscovery
from .config import Config
from .host import Host
from .logger import Logger


class ReplicaSet(object):
    def __init__(self, replicas, section, skip=None, args=None, replication_discovery=None, config=None):
        self.config = config or Config()
        if args and args.section:
            section = args.section
        self.section = section
        self.args = args
        self.pooled_replicas = self.config.get_replicas(section)
        self.section_masters = self.config.get_section_masters(section)
        self.dbs = []
        self.avoid_replicated_changes = []
        self.replication_discovery = replication_discovery or HostReplicationDiscovery()
        self._init_replicas(replicas, skip)

    def _init_replicas(self, replicas, skip):
        if not skip:
            skip = []
        if self.args.dc_masters:
            self.replicas = [Host(i, self.section) for i in self.config.get_section_masters(self.section)]
            return
        if replicas is None:
            replicas = []
            dc_masters = self.config.get_section_masters(self.section)
            for master in dc_masters:
                replicas += self.replication_discovery.get_replicas(Host(master, self.section))
            for replica in replicas:
                if replica in dc_masters:
                    replicas.remove(replica)
        else:
            replicas = [Host(i, self.section) for i in replicas]

        # We don't have to skip anything, life is good
        if not skip:
            self.replicas = replicas
            return

        final_list = []
        skip = [i.replace(':3306', '') for i in skip]
        for replica in replicas:
            if replica in skip:
                continue
            complex = False
            replica_replicas = self.replication_discovery.get_replicas(replica)
            for i in skip:
                if i in replica_replicas:
                    complex = True
            if not complex:
                final_list.append(replica)
                continue
            self.avoid_replicated_changes.append(replica)
            final_list.append(replica)
            final_list += [i for i in replica_replicas if i not in skip]
        self.replicas = final_list

    def _per_replica_gen(self, ticket, downtime_hours):
        logger = Logger(ticket)
        for host in self.replicas:
            replicas_to_downtime = self.check_host_for_replicas(host)
            if replicas_to_downtime is False:
                logger.log_file('Skipping {} as requested'.format(host.host))
                continue
            should_depool_this_host = self.detect_depool(host)

            # never depool the master:
            if host.host in self.section_masters:
                should_depool_this_host = False

            if downtime_hours:
                logger.log_file('Downtiming {} for {} hours'.format(host.host, downtime_hours))
                host.downtime(str(downtime_hours), replicas_to_downtime)
            if should_depool_this_host:
                logger.log_file('Depooling {}'.format(host.host))
                depooled = host.depool(ticket)
                if not depooled:
                    logger.log_file('Draining failed for {}'.format(host.host))
                    continue

            yield host
            if should_depool_this_host:
                logger.log_file('Start repooling {}'.format(host.host))
                host.repool(ticket)
                logger.log_file('End the repool of {}'.format(host.host))

    def get_dbs(self):
        if not self.dbs:
            self.dbs = self.config.get_dbs(self.section)
        return self.dbs

    def check_host_for_replicas(self, host: Host):
        if not self.replication_discovery.has_replicas(host):
            return []

        replicas_to_downtime = []
        if not self.is_master_of_a_dc(host):
            replicas_to_downtime = self.replication_discovery.get_replicas(host, True)
        if not self.args.include_masters:
            replicas_to_question = ','.join([i.host for i in replicas_to_downtime])
            question_mark = input(
                'This host has these hanging replicas: {}, '
                'Are you sure you want to continue? (y or yes): '
                .format(replicas_to_question)).lower().strip()
            if question_mark not in ['y', 'yes', 'si', 'ja']:
                print(
                    'Ignoring {} as it has hanging replicas'.format(
                        host.host))
                return False
        return replicas_to_downtime

    def is_master_of_a_dc(self, host):
        if host.host.replace(':3306', '') not in [i.replace(
                ':3306', '') for i in self.section_masters]:
            return False
        return True

    def detect_depool(self, host):
        if host.host.replace(':3306', '') not in [i.replace(
                ':3306', '') for i in self.pooled_replicas]:
            return False
        return True

    def change_without_replication(self, host: Host):
        if host in self.avoid_replicated_changes:
            return True
        if self.is_master_of_a_dc(host):
            return True
        if self.replication_discovery.has_replicas(host):
            return False
        return True
