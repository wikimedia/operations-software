import json
import retention.ignores

class LocalUserCfGrabber(object):
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

        local_ignores = retention.ignores.get_local_ignores(self.locations)
        output = json.dumps(local_ignores)
        print output
        return output
