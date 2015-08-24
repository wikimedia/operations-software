from clouseau.retention.local.localfileaudit import LocalFilesAuditor
import clouseau.retention.utils.ignores

class LocalHomesAuditor(LocalFilesAuditor):
    '''
    auditing of home directories on a set of hosts

    users may have a local '.data_retention' file in their
    home directories with a list, on entry per line, of files
    or directories (dirs must end in '/') to skip during the audit
    '''

    def __init__(self, audit_type, confdir=None,
                 show_content=False, dirsizes=False,
                 depth=2, to_check=None, ignore_also=None,
                 maxfiles=None):
        '''
        see FilesAuditor for the arguments to the constructor
        '''
        super(LocalHomesAuditor, self).__init__(audit_type, confdir,
                                                show_content, dirsizes,
                                                depth, to_check, ignore_also,
                                                maxfiles)

        # pick up user-created local configs of files/dirs in their homedirs to ignore
        local_ignore_info = clouseau.retention.utils.ignores.get_local_ignores(
            self.confdir, self.locations)
        local_ignores = clouseau.retention.utils.ignores.process_local_ignores(local_ignore_info)
        self.ignored = self.ignores.merge([self.ignored, local_ignores])
