# salt module
import logging

log = logging.getLogger(__name__)

from retention.localfileaudit import LocalFilesAuditor
from retention.locallogaudit import LocalLogsAuditor
from retention.localhomeaudit import LocalHomesAuditor
from retention.localexaminer import LocalFileExaminer, LocalDirExaminer
from retention.localusercfgrabber import LocalUserCfGrabber

def fileaudit_host(confdir,show_content, dirsizes, depth,
                   to_check, ignore_also, timeout,
                   maxfiles):
    fauditor = LocalFilesAuditor('root', confdir, show_content,
                                 dirsizes, depth, to_check,
                                 ignore_also, timeout,
                                 maxfiles)
    result = fauditor.do_local_audit()
    return result

def logaudit_host(confdir, oldest, show_content, show_system_logs,
                  dirsizes, depth,
                  to_check, ignore_also, timeout,
                  maxfiles):
    lauditor = LocalLogsAuditor('logs', confdir, oldest, show_content,
                                show_system_logs,
                                dirsizes, depth, to_check,
                                ignore_also, timeout,
                                maxfiles)
    result = lauditor.do_local_audit()
    return result

def homeaudit_host(confdir, show_content,
                   dirsizes, depth,
                   to_check, ignore_also, timeout,
                   maxfiles):
    hauditor = LocalHomesAuditor('homes', confdir, show_content,
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

def retrieve_usercfs(timeout, audit_type):
    ucfsretriever = LocalUserCfGrabber(timeout, audit_type)
    result = ucfsretriever.run()
    return result
