import sys
import json
import salt.client

sys.path.append('/srv/audits/retention/scripts/')

import retention.remotefileauditor
from retention.localhomeaudit import LocalHomesAuditor
import retention.utils
from retention.utils import JsonHelper
import retention.fileutils
import retention.ruleutils

class RemoteUserCfRetriever(object):
    '''
    retrieval and display dirs / files listed as to
    be ignored in per-user lists on remote host
    '''
    def __init__(self, host, timeout, audit_type):
        self.host = host
        self.timeout = timeout
        self.audit_type = audit_type
        self.locations = audit_type + "_locations"

    def run(self, quiet=False):
        '''
        do all the work

        note that 'quiet' applies only to remotely
        run, and the same is true for returning the contents.
        maybe we want to fix that
        '''

        local_ignores = {}

        client = salt.client.LocalClient()
        module_args = [self.timeout, self.audit_type]

        result = client.cmd([self.host], "retentionaudit.retrieve_usercfs",
                            module_args, expr_form='list',
                            timeout=self.timeout)

        if self.host in result:
            input = result[self.host]
            try:
                local_ignores = json.loads(
                    input, object_hook=JsonHelper.decode_dict)
            except:
                print "WARNING: failed to get local ignores on host",
                print self.host,
                print "got this:", input
                local_ignores = {}

        if not quiet:
            print local_ignores

        return local_ignores

class LocalUserCfRetriever(object):
    '''
    retrieval and display dirs / files listed as to
    be ignored in per-user lists on local host
    '''
    def __init__(self, timeout, audit_type='homes'):
        self.timeout = timeout
        self.audit_type = audit_type
        self.locations = audit_type + "_locations"

    def run(self, quiet=False):
        '''
        do all the work

        note that 'quiet' applies only to remotely
        run, and the same is true for returning the contents.
        maybe we want to fix that
        '''

        local_ignores = {}

        local_ignores = LocalHomesAuditor.get_local_ignores(self.locations)
        output = json.dumps(local_ignores)
        print output
        return output
