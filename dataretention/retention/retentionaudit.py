# salt module

from clouseau.retention.localfileaudit import LocalFilesAuditor
from clouseau.retention.locallogaudit import LocalLogsAuditor
from clouseau.retention.localhomeaudit import LocalHomesAuditor
from clouseau.retention.localexaminer import LocalFileExaminer, LocalDirExaminer
from clouseau.retention.localusercfgrabber import LocalUserCfGrabber

def fileaudit_host(confdir, show_content, dirsizes, depth,
                   to_check, ignore_also,
                   maxfiles):
    fauditor = LocalFilesAuditor('root', confdir, show_content,
                                 dirsizes, depth, to_check,
                                 ignore_also, maxfiles)
    result = fauditor.do_local_audit()
    return result

def logaudit_host(confdir, oldest, show_content, show_system_logs,
                  dirsizes, depth,
                  to_check, ignore_also,
                  maxfiles):
    lauditor = LocalLogsAuditor('logs', confdir, oldest, show_content,
                                show_system_logs,
                                dirsizes, depth, to_check,
                                ignore_also, maxfiles)
    result = lauditor.do_local_audit()
    return result

def homeaudit_host(confdir, show_content,
                   dirsizes, depth,
                   to_check, ignore_also,
                   maxfiles):
    hauditor = LocalHomesAuditor('homes', confdir, show_content,
                                 dirsizes, depth, to_check,
                                 ignore_also, maxfiles)
    result = hauditor.do_local_audit()
    return result

def examine_file(path, num_lines,
                 quiet=False):
    fexaminer = LocalFileExaminer(path, num_lines,
                                  quiet)
    result = fexaminer.run()
    return result

def examine_dir(path, batchno, batchsize,
                quiet=False):
    dexaminer = LocalDirExaminer(path, batchno,
                                 batchsize, quiet)
    result = dexaminer.run()
    return result

def retrieve_usercfs(confdir, audit_type):
    ucfsretriever = LocalUserCfGrabber(confdir, audit_type)
    result = ucfsretriever.run()
    return result
