from ..replica_set import ReplicaSet
from ..host import Host
from .mock_config import MockConfig
from .mock_replication_discovery import MockReplicationDiscovery
from argparse import Namespace


def test_eqiad_master_without_skip():
    args = Namespace(primary_master=False, section=None)
    replica_set = ReplicaSet(None, 's3', replication_discovery=MockReplicationDiscovery(),
                             config=MockConfig(), args=args)
    assert replica_set.replicas == [
        'db1112',
        'db1123',
        'db1166',
        'db1175',
        'db1179',
        'db2109',
        'db2127',
        'db2149',
        'db2156'
    ]


def test_eqiad_master_with_skip():
    args = Namespace(primary_master=False, section=None)
    replica_set = ReplicaSet(
        None,
        's3',
        replication_discovery=MockReplicationDiscovery(),
        config=MockConfig(),
        args=args,
        skip=['db2127'])
    assert replica_set.replicas == [
        'db1112',
        'db1123',
        'db1166',
        'db1175',
        'db1179',
        'db2109',
        'db2149',
        'db2156'
    ]


def test_codfw_master_without_skip():
    replication_discovery = MockReplicationDiscovery()
    assert replication_discovery.get_replicas(Host('db2105', 's3')) == [
        Host('db2109', 's3'),
        Host('db2127', 's3'),
        Host('db2149', 's3'),
        Host('db2156', 's3')
    ]


def test_explicit_replicas():
    args = Namespace(primary_master=False, section=None)
    replica_set = ReplicaSet(['db1175', 'db1179'], 's3',
                             replication_discovery=MockReplicationDiscovery(), config=MockConfig(), args=args)
    assert replica_set.replicas == [
        'db1175',
        'db1179',
    ]


def test_explicit_replicas_with_skip():
    args = Namespace(primary_master=False, section=None)
    replica_set = ReplicaSet(['db1175', 'db1179'], 's3', replication_discovery=MockReplicationDiscovery(
    ), config=MockConfig(), args=args, skip=['db1179'])
    assert replica_set.replicas == [
        'db1175',
    ]
