import os
import sys

sys.path.append('/srv/audits/retention/scripts/')

import retention.utils
import retention.magic
from retention.config import Config
from retention.localfileaudit import LocalFilesAuditor

class LocalHomesAuditor(LocalFilesAuditor):
    '''
    auditing of home directories on a set of hosts

    users may have a local '.data_retention' file in their
    home directories with a list, on entry per line, of files
    or directories (dirs must end in '/') to skip during the audit
    '''

    def __init__(self, audit_type,
                 show_content=False, dirsizes=False,
                 depth=2, to_check=None, ignore_also=None, timeout=60,
                 maxfiles=None):
        '''
        see FilesAuditor for the arguments to the constructor
        '''
        super(LocalHomesAuditor, self).__init__(audit_type,
                                                show_content, dirsizes,
                                                depth, to_check, ignore_also,
                                                timeout, maxfiles)
        self.homes_owners = {}

        # FIXME where are these ever used???
        local_ignores = LocalHomesAuditor.get_local_ignores(self.locations)
        local_ignored_dirs, local_ignored_files = LocalHomesAuditor.process_local_ignores(
            local_ignores, self.ignored)

    @staticmethod
    def process_local_ignores(local_ignores, ignored):
        '''
        files or dirs listed in data retention conf in homedir
        are considered 'good' and added to ignore list

        non-absolute paths will be taken as relative to the
        home dir of the data retention config they were
        read from
        '''

        local_ignored_dirs = []
        local_ignored_files = []
        for basedir in local_ignores:
            for path in local_ignores[basedir]:
                if not path.startswith('/'):
                    path = os.path.join(basedir, path)

                if path.endswith('/'):
                    if 'dirs' not in ignored:
                        ignored['dirs'] = {}
                    if '/' not in ignored['dirs']:
                        ignored['dirs']['/'] = []

                    ignored['dirs']['/'].append(path[:-1])
                    local_ignored_dirs.append(path[:-1])
                else:
                    if 'files' not in ignored:
                        ignored['files'] = {}
                    if '/' not in ignored['files']:
                        ignored['files']['/'] = []

                    ignored['files']['/'].append(path)
                    local_ignored_files.append(path)
        return local_ignored_dirs, local_ignored_files

    @staticmethod
    def get_home_dirs(locations):
        '''
        get a list of home directories where the root location(s) for home are
        specified in the Config class (see 'home_locations'), by reading
        these root location dirs and grabbing all subdirectory names from them
        '''
        home_dirs = []

        for location in Config.cf[locations]:
            if not os.path.isdir(location):
                continue
            home_dirs.extend([os.path.join(location, d)
                              for d in os.listdir(location)
                              if os.path.isdir(os.path.join(location, d))])
        return home_dirs

    @staticmethod
    def get_local_ignores(locations):
        '''
        read a list of absolute paths from /home/blah/.data_retention
        for all blah.  Dirs are specified by op sep at the end ('/')
        and files without.
        '''
        local_ignores = {}
        home_dirs = LocalHomesAuditor.get_home_dirs(locations)
        for hdir in home_dirs:
            local_ignores[hdir] = []
            if os.path.exists(os.path.join(hdir, ".data_retention")):
                try:
                    filep = open(os.path.join(hdir, ".data_retention"))
                    entries = filep.read().split("\n")
                    filep.close()
                except:
                    pass
                entries = filter(None, [e.strip() for e in entries])
                # fixme should sanity check these? ???
                # what happens if people put wildcards in the wrong
                # component, or put utter garbage in there, or...?
                local_ignores[hdir].extend(entries)

        return local_ignores
