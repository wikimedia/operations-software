# salt module
import sys
import logging

sys.path.append('/srv/audits/retention/scripts/')

from retention.localfileaudit import LocalFilesAuditor

def fileaudit_host(show_content, dirsizes, depth,
                   to_check, ignore_also, timeout,
                   maxfiles):
    fauditor = LocalFilesAuditor('root', show_content,
                                 dirsizes, depth, to_check,
                                 ignore_also, timeout,
                                 maxfiles)
    result = fauditor.do_local_audit()
    return result
