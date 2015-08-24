import json
import clouseau.retention.utils.ignores

class LocalUserCfGrabber(object):
    '''
    retrieval and display dirs / files listed as to
    be ignored in per-user lists on local host
    '''
    def __init__(self, confdir, audit_type='homes'):
        self.confdir = confdir
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

        local_ignores = clouseau.retention.utils.ignores.get_local_ignores(self.confdir, self.locations)
        output = json.dumps(local_ignores)
        if not quiet:
            print output
        return output
