import sys

sys.path.append('/srv/audits/retention/scripts/')

from retention.saltclientplus import LocalClientPlus
from retention.config import Config

class Runner(object):
    '''
    Manage running current script remotely via salt on one or more hosts
    '''

    def __init__(self, hosts_expr, expanded_hosts,
                 audit_type, generate_executor,
                 show_sample_content=False, to_check=None,
                 timeout=30, verbose=False):
        self.hosts_expr = hosts_expr
        self.expanded_hosts = expanded_hosts
        self.hosts, self.hosts_expr_type = Runner.get_hosts_expr_type(
            self.hosts_expr)
        self.audit_type = audit_type
        self.generate_executor = generate_executor
        self.show_sample_content = show_sample_content
        self.to_check = to_check
        self.timeout = timeout
        self.verbose = verbose

    @staticmethod
    def running_locally(hosts_expr):
        '''
        determine whether this script is to run on the local
        host or on one or more remote hosts
        '''
        if hosts_expr == "127.0.0.1" or hosts_expr == "localhost":
            return True
        else:
            return False

    def run_remotely(self):
        '''
        run the current script on specified remote hosts
        '''

        client = LocalClientPlus()

        if self.expanded_hosts is None:
            self.expanded_hosts = client.cmd_expandminions(
                self.hosts, "test.ping", expr_form=self.hosts_expr_type)
        code = "# -*- coding: utf-8 -*-\n"
        code += self.generate_executor()
        with open(__file__, 'r') as fp_:
            code += fp_.read()

        hostbatches = [self.expanded_hosts[i: i + Config.cf['batchsize']]
                       for i in range(0, len(self.expanded_hosts),
                                      Config.cf['batchsize'])]

        result = {}
        for hosts in hostbatches:
            if self.verbose:
                sys.stderr.write("INFO: running on hosts\n")
                sys.stderr.write(','.join(hosts) + '\n')

            # try to work around a likely race condition in zmq/salt
            # time.sleep(5)
            new_result = client.cmd(hosts, "cmd.exec_code", ["python2", code],
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
