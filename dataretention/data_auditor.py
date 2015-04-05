import sys
import getopt

from retention.cli import CommandLine
from retention.remotefileauditor import RemoteFilesAuditor
from retention.remotelogauditor import RemoteLogsAuditor
from retention.remotehomeauditor import RemoteHomesAuditor
from retention.remoteexaminer import RemoteFileExaminer, RemoteDirExaminer
from retention.remoteusercfgrabber import RemoteUserCfGrabber

def usage(message=None):
    if message:
        sys.stderr.write(message + "\n")
    usage_message = """Usage: data_auditor.py --audit <audit-type> --target <hostexpr>
             [--confdir <path>] [--prettyprint] [-report] [--depth <number>] [--dirsizes]
             [--maxfiles <number>] [--sample] [--files <filelist>]
             [--ignore <filelist>] [--examine <path>]
             [--timeout <number>] [--verbose]

This script audit a directory tree, producing a list of files, displaying
for each:
    'creation time' i.e. inode change time,
    modification time
    whether the file is currently opened by a process
    whether the file is older than 90 days (without creation time this cannot
        always be determined)
    the file type
    the uid of the file owner

Alternatively it can be used to provide more limited directory info for
a single directory on a remote host. (This is used in interactive mode.)

The script requires salt to run remotely, and expects to be run
from the salt master.

Options:

    audit       (-a) -- specify the type of audit to be done, one of 'root',
                        'logs' or 'homes'; this may not be specified with
                        the 'info' option.
    confdir     (-d) -- path to dir where ignores.yaml is located
                        default: /srv/audits/retention/configs
    target      (-t) -- for local runs, this must be 'localhost' or '127.0.1'
                        for remote hosts, this should be a host expression
                        recognizable by salt, in the following format:
                           grain:<salt grain>
                           pcre:<regex>
                           list:<host1>,<host2>,...
                           <glob or string>
    prettyprint (-p) -- print results in a nice format suitable for human
                        consumption (default: print json output)
    report      (-r) -- show a summary report for the group of hosts with
                        details only for anomalies (default: false)
                        this option implies 'oldest'
    depth       (-d) -- inspect directories at this depth when checking that
                        directories don't have too many files to audit
                        (default: 0)
    dirsizes    (-D) -- don't report on files, just check the directories up to
                        the specified or default depth and report on those that
                        have more than maxfiles
    maxfiles    (-m) -- directories with more than this many files will be
                        skipped and a warning shown (default: 100, unless
                        dirsizes is specified, then 1000)
    sample      (-s) -- display the first line from each file along with the
                        regular file info, for files that are text format
                        (default: false)
    timeout     (-T) -- for audit of remote hosts, how many seconds to wait
                        for the salt command to return before giving up
                        (default: 60)
    files       (-f) -- comma-separated list of filenames (basename only and no
                        paths) and/or directories (full path must be specified)
                        which will be checked; if none is specified all files
                        in a standard list of directories will be examined
    ignore      (-i) -- comma-separated list of files and/or directories to be
                        ignored in addition to the usual ones; if the name ends
                        in '/' it is treated as a directory, else as a file,
                        in either case the full path must be specified or the
                        the element will be silently ignored.
    interactive (-I) -- after the report is completed, enter interactive mode,
                        allowing the user to inspect directories on any host
                        and/or set audit rules for them or their contents

    examine     (-e) -- instead of an audit, display information about the
                        specified directory or file; this may not be specified
                        with 'audit'.

    filecontents(-F) -- instead of an audit, display the first so many lines
                        of the specified file; this may not be specified
                        with 'audit'.
    linecount   (-l) -- number of lines of file content to be displayed
                        (efault: 1)

    userconf    (-u) -- instead of an audit, display the per user config
                        files on the given hosts; this may not be specified
                        with 'audit'.

For 'logs' audit type:

    system      (-S) -- show system logs (e.g. syslog, messages) along with
                        app logs; this relies on a hard-coded list of presumed
                        system logs (default: false)
    oldest      (-o) -- only show the oldest log in a group of rotated
                        logs (default: show all logs)
"""
    sys.stderr.write(usage_message)
    sys.exit(1)


def main():
    hosts_expr = None
    audit_type = None
    confdir = '/srv/audits/retention/configs'
    files_to_check = None
    prettyprint = False
    show_sample_content = False
    summary_report = False
    verbose = False
    ignore_also = None
    dir_info = None
    getuserconfs = False
    batchno = 1
    file_info = None
    linecount = 1
    maxfiles = None
    timeout = 60
    depth = 0
    dirsizes = False
    show_system_logs = False
    oldest_only = False
    interactive = False
    store_filepath = "/etc/data_retention/dataretention_rules.sq3"

    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "a:b:c:d:Df:F:l:i:Ie:m:oprsSt:T:uvh",
            ["audit=", "confdir=", "files=",
             "filecontents=", "linecount=",
             "ignore=",
             "interactive",
             "depth=", "maxfiles=",
             "oldest", "prettyprint", "report",
             "dirsizes", "examine", "batchno",
             "sample", "system",
             "target=", "timeout=",
             "userconf", "verbose", "help"])

    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))

    for (opt, val) in options:
        if opt in ["-t", "--target"]:
            hosts_expr = val
        elif opt in ["-a", "--audit"]:
            audit_type = val
        elif opt in ["-c", "--confir"]:
            confdir = val
        elif opt in ["-d", "--depth"]:
            if not val.isdigit():
                usage("depth must be a number")
            depth = int(val)
        elif opt in ["-f", "--files"]:
            files_to_check = val
        elif opt in ["-F", "--filecontents"]:
            file_info = val
        elif opt in ["-l", "--linecount"]:
            if not val.isdigit():
                usage("linecount must be a number (starting from 1)")
            linecount = int(val)
        elif opt in ["-i", "--ignore"]:
            ignore_also = val
        elif opt in ["-I", "--interactive"]:
            interactive = True
        elif opt in ["-e", "--examine"]:
            dir_info = val
        elif opt in ["-b", "--batchno"]:
            if not val.isdigit():
                usage("batcho must be a number (starting from 1)")
            batchno = int(val)
        elif opt in ["-m", "--maxfiles"]:
            if not val.isdigit():
                usage("maxfiles must be a number")
            maxfiles = int(val)
        elif opt in ["-o", "--oldest"]:
            oldest_only = True
        elif opt in ["-p", "--prettyprint"]:
            prettyprint = True
        elif opt in ["-r", "--report"]:
            summary_report = True
        elif opt in ["-D", "--dirsizes"]:
            dirsizes = True
        elif opt in ["-s", "--sample"]:
            show_sample_content = True
        elif opt in ["-S", "--system"]:
            show_system_logs = True
        elif opt in ["-T", "--timeout"]:
            if not val.isdigit():
                usage("timeout must be a number")
            timeout = int(val)
        elif opt in ["-u", "--userconf"]:
            getuserconfs = True
        elif opt in ["-h", "--help"]:
            usage()
        elif opt in ["-v", "--verbose"]:
            verbose = True
        else:
            usage("Unknown option specified: %s" % opt)

    if len(remainder) > 0:
        usage("Unknown option specified: <%s>" % remainder[0])

    if hosts_expr is None:
        usage("Mandatory target argument not specified")

    count = len(filter(None, [audit_type, dir_info, file_info, getuserconfs]))
    if count == 0:
        usage("One of 'audit', 'examine', 'userconf' "
              "or 'filecontents' must be specified")
    elif count > 1:
        usage("Only one of 'audit', 'examine' 'userconf' "
              "or 'filecontents' may be specified")

    if dir_info is not None:
        # for now more than 1000 entries in a dir = we silently toss them
        direxam = RemoteDirExaminer(dir_info, hosts_expr, batchno, 1000, timeout)
        direxam.run()
        sys.exit(0)
    elif file_info is not None:
        fileexam = RemoteFileExaminer(file_info, hosts_expr, linecount, timeout)
        fileexam.run()
        sys.exit(0)
    elif getuserconfs:
        getconfs = RemoteUserCfGrabber(hosts_expr, timeout, 'homes')
        getconfs.run()
        sys.exit(0)

    if audit_type not in ['root', 'logs', 'homes']:
        usage("audit type must be one of 'root', 'logs', 'homes'")

    if show_system_logs and not audit_type == 'logs':
        usage("'system' argument may only be used with logs audit")

    if oldest_only and not audit_type == 'logs':
        usage("'oldest' argument may only be used with logs audit")

    if audit_type == 'logs':
        logsaudit = RemoteLogsAuditor(hosts_expr, audit_type, confdir,
                                      prettyprint,
                                      oldest_only, show_sample_content, dirsizes,
                                      show_system_logs,
                                      summary_report, depth, files_to_check, ignore_also,
                                      timeout, maxfiles, store_filepath, verbose)
        report, ignored = logsaudit.audit_hosts()
        if interactive:
            cmdline = CommandLine(confdir, store_filepath, timeout, audit_type, hosts_expr)
            cmdline.run(report, ignored)

    elif audit_type == 'root':
        filesaudit = RemoteFilesAuditor(hosts_expr, audit_type, confdir,
                                        prettyprint,
                                        show_sample_content, dirsizes,
                                        summary_report,
                                        depth, files_to_check, ignore_also,
                                        timeout, maxfiles, store_filepath, verbose)
        report, ignored = filesaudit.audit_hosts()
        if interactive:
            cmdline = CommandLine(confdir, store_filepath, timeout, audit_type, hosts_expr)
            cmdline.run(report, ignored)

    elif audit_type == 'homes':
        homesaudit = RemoteHomesAuditor(hosts_expr, audit_type, confdir,
                                        prettyprint,
                                        show_sample_content, dirsizes,
                                        summary_report,
                                        depth, files_to_check, ignore_also,
                                        timeout, maxfiles, store_filepath, verbose)
        report, ignored = homesaudit.audit_hosts()
        if interactive:
            cmdline = CommandLine(confdir, store_filepath, timeout, audit_type, hosts_expr)
            cmdline.run(report, ignored)

if __name__ == '__main__':
    main()
