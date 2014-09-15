#!/usr/bin/env python
# Manage container synchronization between two swift clusters
# See also:
# http://docs.openstack.org/developer/swift/overview_container_sync.html

import argparse
import logging
import os
import sys

import swiftclient

log = logging.getLogger(__name__)
SYNC_DISABLE = 0
SYNC_ENABLE = 1


def _setup_source(connection, container, sync_key, sync_to):
    return _setup_container(connection, container,
            {'X-Container-Sync-Key': sync_key,
             'X-Container-Sync-To': sync_to})


def _setup_destination(connection, container, sync_key):
    return _setup_container(connection, container,
            {'X-Container-Sync-Key': sync_key})


def _setup_container(connection, container, headers):
    response_dict = {}
    connection.post_container(container, headers=headers,
            response_dict=response_dict)
    return response_dict


def _setup_sync(action, source_connection, destination_connection, container,
        realm_key=None, sync_to=None, ignore_notfound=False):
    try:
        _setup_source(source_connection, container, realm_key, sync_to)
    except swiftclient.exceptions.ClientException as err:
        if err.http_status == 404 and ignore_notfound:
            log.warn('container %s not found at source, skipping', container)
            return
        else:
            raise

    try:
        _setup_destination(destination_connection, container, realm_key)
    except swiftclient.exceptions.ClientException as err:
        if action == SYNC_ENABLE and err.http_status == 404:
            log.info('creating container %s', container)
            destination_connection.put_container(container)
            _setup_destination(destination_connection, container, realm_key)
        elif action == SYNC_DISABLE and err.http_status == 404 \
                and ignore_notfound:
            log.warn('container %s not found at destination, skipping',
                    container)
            return
        else:
            raise


def show_sync(source_connection, destination_connection, containers):
    for container in containers:
        headers = destination_connection.head_container(container)
        sync_to = headers.get('x-container-sync-to', None)
        sync_key = headers.get('x-container-sync-key', None)
        if sync_to and sync_key:
            log.info('container %s sync: enabled %s' % (container, sync_to))
        else:
            log.info('container %s sync: disabled' % container)


def enable_sync(source_connection, destination_connection,
        realm_name, realm_key, realm_cluster, containers, account_name=None,
        ignore_notfound=False):
    if account_name is None:
        storage_url, _ = destination_connection.get_auth()
        account_name = storage_url.rsplit('/', 1)[-1]

    for container in containers:
        log.info('enabling sync for %s', container)
        sync_to = '//%s' % '/'.join([realm_name, realm_cluster, account_name,
                container])
        _setup_sync(SYNC_ENABLE, source_connection, destination_connection,
                container, realm_key, sync_to, ignore_notfound)


# XXX check if setting to empty value is enough to disable sync
def disable_sync(source_connection, destination_connection, containers,
        ignore_notfound=False):
    for container in containers:
        log.info('disabling sync for %s', container)
        _setup_sync(SYNC_DISABLE, source_connection, destination_connection,
                container, '', '', ignore_notfound)


def main():
    parser = argparse.ArgumentParser(
        description="Setup swift container synchronization")
    parser.add_argument('-A', '--auth', dest='auth',
        default=os.environ.get('ST_AUTH', None),
        help='URL for obtaining an auth token')
    parser.add_argument('-U', '--user', dest='user',
        default=os.environ.get('ST_USER', None),
        help='User name for obtaining an auth token')
    parser.add_argument('-K', '--key', dest='key',
        default=os.environ.get('ST_KEY', None),
        help='Key for obtaining an auth token')

    parser.add_argument('--dest-auth', dest='dest_auth',
        default=None,
        help='Set --auth for destination cluster')
    parser.add_argument('--dest-user', dest='dest_user',
        default=os.environ.get('DEST_ST_USER',
                               os.environ.get('ST_USER', None)),
        help='Set --user for destination cluster')
    parser.add_argument('--dest-key', dest='dest_key',
        default=os.environ.get('DEST_ST_KEY', os.environ.get('ST_KEY', None)),
        help='Set --key for destination cluster')

    parser.add_argument('--realm', dest='realm_name',
        help='Realm name to use')
    parser.add_argument('--realm-key', dest='realm_key',
        help='Realm key to use on the destination')
    parser.add_argument('--realm-cluster', dest='realm_cluster',
        help='Realm cluster to use on the destination')

    parser.add_argument('--debug', dest='debug', default=False,
        action='store_true', help='Turn on debug')

    parser.add_argument('action', type=str,
            choices=['enable', 'disable', 'show'],
        help='What action to perform')

    parser.add_argument('containers', nargs='+', type=str,
        help='What containers to operate on')
    args = parser.parse_args()

    if None in (args.auth, args.user, args.key,
                args.dest_auth, args.dest_user, args.dest_key):
        parser.error("Please provide auth, user and key for source and"
                     "destination clusters")
        return 1

    if None in (args.realm_name, args.realm_key, args.realm_cluster):
        parser.error("Please provide realm name, key and cluster name")
        return 1

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    source_connection = swiftclient.Connection(args.auth, args.user, args.key,
            retry_on_ratelimit=True)
    destination_connection = swiftclient.Connection(args.dest_auth,
            args.dest_user, args.dest_key, retry_on_ratelimit=True)

    if args.action == 'disable':
        disable_sync(source_connection, destination_connection,
                args.containers)
    elif args.action == 'enable':
        enable_sync(source_connection, destination_connection, args.realm_name,
                args.realm_key, args.realm_cluster, args.containers)
    elif args.action == 'show':
        show_sync(source_connection, destination_connection, args.containers)


if __name__ == '__main__':
    sys.exit(main())
