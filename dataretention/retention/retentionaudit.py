# salt module
import sys
import logging

sys.path.append('/srv/audits/retention/scripts/')

from retention.localfileaudit import LocalFilesAuditor
from retention.locallogaudit import LocalLogsAuditor
from retention.localhomeaudit import LocalHomesAuditor
from retention.examiner import LocalFileExaminer, LocalDirExaminer

log = logging.getLogger(__name__)

def fileaudit_host(show_content, dirsizes, depth,
                   to_check, ignore_also, timeout,
                   maxfiles):
    fauditor = LocalFilesAuditor('root', show_content,
                                 dirsizes, depth, to_check,
                                 ignore_also, timeout,
                                 maxfiles)
    result = fauditor.do_local_audit()
    return result

def logaudit_host(oldest, show_content, show_system_logs,
                  dirsizes, depth,
                  to_check, ignore_also, timeout,
                  maxfiles):
    lauditor = LocalLogsAuditor('logs', oldest, show_content,
                                show_system_logs,
                                dirsizes, depth, to_check,
                                ignore_also, timeout,
                                maxfiles)
    result = lauditor.do_local_audit()
    return result

def homeaudit_host(show_content,
                   dirsizes, depth,
                   to_check, ignore_also, timeout,
                   maxfiles):
    hauditor = LocalHomesAuditor('homes', show_content,
                                 dirsizes, depth, to_check,
                                 ignore_also, timeout,
                                 maxfiles)
    result = hauditor.do_local_audit()
    return result

def examine_file(path, num_lines,
                 timeout, quiet=False):
    fexaminer = LocalFileExaminer(path, num_lines,
                                  timeout, quiet)
    result = fexaminer.run()
    return result

def examine_dir(path, batchno, batchsize,
                timeout, quiet=False):
    dexaminer = LocalDirExaminer(path, batchno,
                                 batchsize, timeout, quiet)
    result = dexaminer.run()
    return result

