# show, delete, add, replace audit rules in the rulestore
# you can do a lot of damage with this if you don't know
# what you are doing. you have been warned.

import os
import sys
import getopt

sys.path.append('/srv/audits/retention/scripts/')

from retention.saltclientplus import LocalClientPlus
import retention.utils
from retention.rule import Rule, RuleStore
from retention.status import Status

def usage(message=None):
    if message:
        sys.stderr.write(message + "\n")
    usage_message = """Usage: rulestore.py --host <hostname>
             --action <action> [--path <path>] [--status <status>]
             [--rulestore <rulestore-path>]
             [--dryrun] [--help]

             where action is one of:
                show, add, delete

             status is one of:
                G -- entry is good, passed audit
                P -- entry is a problem
                R -- entry needs to be rechecked
                U -- entry is unreivewed (perhaps skipped due to size)

             path is the full path of a file or a directory;
             if path is a directory, it must end in '/'

    if --dryrun is specified, print what would be done but don't
             actually do it

    if --help is specified, this help message is displayed

    All options may also be specified in their short form
    i.e. -a instead of --action, by using the first letter
    of the option.
"""
    sys.stderr.write(usage_message)
    sys.exit(1)

def check_args(host, action, status):
    if host is None:
        usage("Mandatory 'host' argument not specified")

    if action is None:
        usage("Mandatory 'action' argument not specified")

    if action not in ['show', 'delete', 'add']:
        usage('unknown action %s specified' % action)

    if status is not None:
        status = Status.status_to_text(status)
        if status is None:
            usage('unknown status %s specified' % status)

def do_action(cdb, action, hosts, status, path, dryrun):
    if action == 'show':
        if path and path[-1] == os.path.sep:
            path = path[:-1]
        for host in hosts:
            Rule.show_rules(cdb, host, status, prefix=path)

    elif action == 'delete':
        if path and path[-1] == os.path.sep:
            path = path[:-1]

        if path:
            if dryrun:
                print "would remove rule for %s in %s" % (path, hosts)
            else:
                for host in hosts:
                    Rule.do_remove_rule(cdb, path, host)
        elif status:
            if dryrun:
                print "would remove rules for status %s in %s" % (status, hosts)
            else:
                for host in hosts:
                    Rule.do_remove_rules(cdb, status, host)

    elif action == 'add':
        if status is None:
            usage('status must be specified to add a rule')
        if path is None:
            usage('path must be specified to add a rule')

        if path[-1] == os.path.sep:
            rtype = Rule.text_to_entrytype('dir')
            path = path[:-1]
        else:
            rtype = Rule.text_to_entrytype('file')

        if dryrun:
            print "would add rule for %s in %s with status %s of type %s" % (
                hosts, path, status, rtype)

        for host in hosts:
            Rule.do_add_rule(cdb, path, rtype, status, host)

def main():
    host = None
    action = None
    path = None
    status = None
    dryrun = False
    store_filepath = "/etc/data_retention/dataretention_rules.sq3"

    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "h:a:p:s:r:dh",
            ["host=", "action=", "path=",
             "status=", "dryrun", "help"])

    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))

    for (opt, val) in options:
        if opt in ["-h", "--host"]:
            host = val
        elif opt in ["-a", "--action"]:
            action = val
        elif opt in ["-p", "--path"]:
            path = val
        elif opt in ["-s", "--status"]:
            status = val
        elif opt in ["-r", "--rulestore"]:
            store_filepath = val
        elif opt in ["-d", "--dryrun"]:
            dryrun = True
        elif opt in ["-h", "--help"]:
            usage()
        else:
            usage("Unknown option specified: %s" % opt)

    if len(remainder) > 0:
        usage("Unknown option specified: <%s>" % remainder[0])

    check_args(host, action, status)

    if not os.path.exists(store_filepath):
        usage('no such rulestore at %s' % store_filepath)

    cdb = RuleStore(store_filepath)
    cdb.store_db_init(None)

    hosts, htype = retention.utils.get_hosts_expr_type(host)
    
    # if we are given one host, check that the host has a table or whine
    if htype == 'glob' and '*' not in hosts:
        if not Rule.check_host_table_exists(cdb, host):
            usage('no such host in rule store, %s' % host)
    elif htype == 'grain':
        client = LocalClientPlus()
        hosts = client.cmd_expandminions(hosts, "test.ping", expr_form=htype)
    do_action(cdb, action, hosts, status, path, dryrun)

if __name__ == '__main__':
    main()
