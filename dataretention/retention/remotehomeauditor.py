import os

from retention.remotefileauditor import RemoteFilesAuditor


class RemoteHomesAuditor(RemoteFilesAuditor):
    '''
    auditing of home directories on a set of hosts

    users may have a local '.data_retention' file in their
    home directories with a list, on entry per line, of files
    or directories (dirs must end in '/') to skip during the audit
    '''

    def __init__(self, hosts_expr, audit_type, confdir=None, prettyprint=False,
                 show_content=False, dirsizes=False, summary_report=False,
                 depth=2, to_check=None, ignore_also=None, timeout=60,
                 maxfiles=None, store_filepath=None, verbose=False):
        '''
        see FilesAuditor for the arguments to the constructor
        '''
        super(RemoteHomesAuditor, self).__init__(hosts_expr, audit_type,
                                                 confdir, prettyprint,
                                                 show_content, dirsizes,
                                                 summary_report, depth,
                                                 to_check, ignore_also, timeout,
                                                 maxfiles, store_filepath, verbose)
        self.homes_owners = {}

    def get_audit_args(self):
        audit_args = [self.confdir,
                      self.show_sample_content,
                      self.dirsizes,
                      self.depth - 1,
                      self.to_check,
                      ",".join(self.ignore_also) if self.ignore_also is not None else None,
                      self.timeout,
                      self.MAX_FILES]
        return audit_args

    def display_host_summary(self):
        '''
        instead of a detailed report with oe entry per file
        that may be problematic, display a summary for each homedir
        on a host
        '''
        if self.summary is not None:
            paths = sorted(self.summary.keys())
            for path in paths:
                for group in self.summary[path]:
                    if (self.summary[path][group]['old'] > 0 or
                            self.summary[path][group]['maybe_old'] > 0 or
                            self.summary[path][group]['odd_owner'] > 0):
                        print ("in directory %s, (%s), %d old,"
                               " %d maybe old, %d with odd owner"
                               % (path, group,
                                  self.summary[path][group]['old'],
                                  self.summary[path][group]['maybe_old'],
                                  self.summary[path][group]['odd_owner']))

    def add_stats(self, item, summary):
        '''
        gather stats on how many files/dirs
        may be problematic; summary is where the results
        are collected, item is the item to include in
        the summary if needed
        '''
        dirname = os.path.dirname(item['path'])

        if dirname not in summary:
            summary[dirname] = {
                'binary': {'old': 0, 'maybe_old': 0, 'odd_owner': 0},
                'text': {'old': 0, 'maybe_old': 0, 'odd_owner': 0}
            }
        if item['binary'] is True:
            group = 'binary'
        else:
            group = 'text'

        if item['old'] == 'T':
            summary[dirname][group]['old'] += 1
        elif item['old'] == '-':
            summary[dirname][group]['maybe_old'] += 1

        if not item['path'].startswith('/home/'):
            return

        _, home, user, _ = item['path'].split(os.path.sep, 3)
        home_dir = os.path.join(os.path.sep, home, user)
        if home_dir not in self.homes_owners:
            try:
                dirstat = os.stat(home_dir)
            except:
                return
            self.homes_owners[home_dir] = str(dirstat.st_uid)

        if item['owner'] != self.homes_owners[home_dir]:
            summary[dirname][group]['odd_owner'] += 1
