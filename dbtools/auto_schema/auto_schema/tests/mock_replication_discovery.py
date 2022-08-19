
from ..host import Host
from ..replication_discovery import ReplicationDiscovery
from .mock_config import MockConfig


class MockReplicationDiscovery(ReplicationDiscovery):
    def __init__(self) -> None:
        self.config = MockConfig()

    def get_replicas(self, host: Host, recursive=False):
        eqiad_replicas = [Host(i, host.section) for i in self.config._get_replicas_for_dc(host.section, 'eqiad')]
        codfw_replicas = [Host(i, host.section) for i in self.config._get_replicas_for_dc(host.section, 'codfw')]
        eqiad_master = Host(self.config.get_section_master_for_dc(host.section, 'eqiad'), host.section)
        codfw_master = Host(self.config.get_section_master_for_dc(host.section, 'codfw'), host.section)
        if host == eqiad_master:
            if recursive:
                return eqiad_replicas + [codfw_master] + codfw_replicas
            return eqiad_replicas
        if host == codfw_master:
            return codfw_replicas
        return []

    def has_replicas(self, host: Host):
        return self.get_replicas(host) != []
