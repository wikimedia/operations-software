import os
import sys

from clouseau.retention.saltclientplus import LocalClientPlus
import clouseau.retention.config

class Runner(object):
    '''
    Manage running current script remotely via salt on one or more hosts
    '''

    def __init__(self, confdir, store_filepath, hosts_expr, expanded_hosts,
                 audit_type, auditor_args,
                 show_sample_content=False, to_check=None,
                 timeout=30, verbose=False):
        self.confdir = confdir
        self.store_filepath = store_filepath
        self.hosts_expr = hosts_expr
        self.expanded_hosts = expanded_hosts
        self.hosts, self.hosts_expr_type = Runner.get_hosts_expr_type(
            self.hosts_expr)
        self.audit_type = audit_type
        self.auditmodule_args = auditor_args
        self.show_sample_content = show_sample_content
        self.to_check = to_check
        self.timeout = timeout
        self.verbose = verbose
        clouseau.retention.config.set_up_conf(self.confdir)

    def get_auditfunction_name(self):
        if self.audit_type == 'root':
            return 'fileaudit_host'
        elif self.audit_type == 'logs':
            return 'logaudit_host'
        elif self.audit_type == 'homes':
            return 'homeaudit_host'
        else:
            return None

    def run_remotely(self):
        '''
        run the current script on specified remote hosts
        '''

        client = LocalClientPlus()

        if self.expanded_hosts is None:
            self.expanded_hosts = client.cmd_expandminions(
                self.hosts, "test.ping", expr_form=self.hosts_expr_type)

        # fixme instead of this we call the right salt module based on the
        # audit type and with the self.auditmodule_args which is a list

        hostbatches = [self.expanded_hosts[i: i + clouseau.retention.config.conf['batchsize']]
                       for i in range(0, len(self.expanded_hosts),
                                      clouseau.retention.config.conf['batchsize'])]

        result = {}
        for hosts in hostbatches:
            if self.verbose:
                sys.stderr.write("INFO: running on hosts\n")
                sys.stderr.write(','.join(hosts) + '\n')

            path = os.path.join(os.path.dirname(self.store_filepath),
                                "data_retention.d")
            contents = clouseau.retention.ignores.prep_good_rules_tosend(path, hosts)
            if contents:
                new_result = client.cmd_full_return(hosts, 'cp.recv', [contents, os.path.join(self.confdir, 'fromstore')],
                                                    expr_form='list')
            # step two: run the appropriate salt audit module function
            new_result = client.cmd(hosts, "retentionaudit.%s" % self.get_auditfunction_name(), self.auditmodule_args,
                                    expr_form='list', timeout=self.timeout)

            if new_result is not None:
                result.update(new_result)
            # fixme, collect and report on hosts that did
            # not respond
        return result

    @staticmethod
    def get_hosts_expr_type(hosts_expr):
        '''
        return the type of salt host expr and stash
        the converted expression as well
        '''

        if hosts_expr.startswith('grain:'):
            hosts = hosts_expr[6:]
            return hosts, 'grain'
        elif hosts_expr.startswith('pcre:'):
            hosts = hosts_expr[5:]
            return hosts, 'pcre'
        elif hosts_expr.startswith('list:'):
            hosts = hosts_expr[5:].split(',')
            return hosts, 'list'
        else:
            hosts = hosts_expr
            return hosts, 'glob'  # default
