import os
import sys
import time
import json
import readline
import traceback

from clouseau.retention.status import Status
from clouseau.retention.rule import RuleStore
import retention.remotefileauditor
from clouseau.retention.locallogaudit import LocalLogsAuditor
from clouseau.retention.fileinfo import FileInfo
from clouseau.retention.utils import JsonHelper
import clouseau.retention.config
from retention.remoteexaminer import RemoteDirExaminer, RemoteFileExaminer
import clouseau.retention.ruleutils
import clouseau.retention.cliutils
from clouseau.retention.ignores import Ignores
from retention.remoteusercfgrabber import RemoteUserCfGrabber
import clouseau.retention.ignores
from clouseau.retention.completion import Completion


class CurrentEnv(object):

    def __init__(self, host=None, hostlist=None, path=None, problems=None, skipped=None):
        self.host = host
        self.hostlist = hostlist
        self.cwdir = path
        self.problem_dirs = problems
        self.skipped_dirs = skipped

    def clear(self):
        self.host = None
        self.hostlist = None
        self.cwdir = None
        self.problem_dirs = None
        self.skipped_dirs = None

    def set_hosts(self, hostlist):
        self.hostlist = hostlist

    def set_reported_dirs(self, problems, skipped):
        self.problem_dirs = problems
        self.skipped_dirs = skipped


class CurrentDirContents(object):
    '''
    keep track of current directory contents
    '''
    def __init__(self, timeout):
        self.timeout = timeout
        self.entries = None
        self.entries_dict = None
        self.host = None
        self.path = None

    def get(self, host, path, batchno, force=False):
        '''
        via salt get the directory contents for the first N = 1000
        entries, unsorted.
        if the contents for this host and path have already been
        retrieved and not yet tossed/replaced, don't get them
        again unless 'force' is True; you may want this in case
        you expect the directory contents to have been updated
        since the last invocation
        '''

        if (host is not None and path is not None and
                host == self.host and path == self.path and
                (not force or (self.entries is not None))):
            return

        # fixme batchno? batchno should increment too
        # for now more than 1000 entries in a dir = we silently toss them
        direxamin = RemoteDirExaminer(path, host, batchno, 1000, self.timeout, prettyprint=False)
        contents = direxamin.run(True)
        if contents is None:
            return

        contents = contents.split("\n")
        self.host = host
        self.path = path

        self.entries = []
        self.entries_dict = {}

        for item in contents:
            try:
                result = json.loads(item, object_hook=JsonHelper.decode_dict)
                self.entries.append(result)
                self.entries_dict[result['path']] = result
            except:
                print "WARNING: problem getting dir contents, retrieved", item
#                exc_type, exc_value, exc_traceback = sys.exc_info()
#                sys.stderr.write(repr(traceback.format_exception(
#                    exc_type, exc_value, exc_traceback)))


    def show(self, host, path, batchno, filtertype, check_not_ignored, force=False):
        self.get(host, path, batchno, force)

        # fixme this 50 is pretty arbitrary oh well
        justify = 50

        keys = self.entries_dict.keys()
        if filtertype == 'file':
            items = (sorted(
                item for item in keys
                if self.entries_dict[item]['type'] == 'file'))
        elif filtertype == 'dir':
            items = (sorted(
                item for item in keys
                if self.entries_dict[item]['type'] == 'dir'))
        elif filtertype == 'all':
            items = sorted(
                item for item in keys
                if self.entries_dict[item]['type'] == 'dir')
            items = items + sorted(
                item for item in keys
                if self.entries_dict[item]['type'] == 'file')
        elif filtertype == 'check':
            items = sorted(
                item for item in keys
                if self.entries_dict[item]['type'] == 'dir'
                and check_not_ignored(self.entries_dict[item]['path'],
                                      self.entries_dict[item]['type']))
            items = items + sorted(
                item for item in keys
                if self.entries_dict[item]['type'] == 'file'
                and check_not_ignored(self.entries_dict[item]['path'],
                                      self.entries_dict[item]['type']))

        page = 1
        num_per_page = 50  # another arbitrary value
        num_items = len(items)
        num_in_last_page = num_items % num_per_page
        num_pages = num_items / num_per_page
        if num_in_last_page:
            num_pages += 1

        num_to_show = num_per_page
        if num_pages == 1:
            num_to_show = num_in_last_page

        while True:
            for item in items[(page - 1) * num_per_page:
                              (page - 1) * num_per_page + num_to_show]:
                if not item:
                    # fixme why do we have an empty item I wonder
                    continue
                try:
                    result = FileInfo.format_pretty_output_from_dict(
                        self.entries_dict[item], path_justify=justify)
                except:
                    print "item is", item
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    sys.stderr.write(repr(traceback.format_exception(
                        exc_type, exc_value, exc_traceback)))
                    result = None
                if result is not None:
                    print result

            if num_pages == 1:
                break

            page = clouseau.retention.cliutils.show_pager(page, num_items, num_per_page)
            if page is None:
                return
            elif page == num_pages:
                num_to_show = num_in_last_page
            else:
                num_to_show = num_per_page

    def clear(self):
        self.entries = None
        self.entries_dict = None
        self.host = None
        self.path = None


class CommandLine(object):
    '''
    prompt user at the command line for actions to take on a given
    directory or file, show results
    '''
    # todo: down and up should check you really are (descending,
    # ascending path)

    def __init__(self, confdir, store_filepath, timeout, audit_type, hosts_expr=None):
        self.confdir = confdir
        self.cdb = RuleStore(store_filepath)
        self.cdb.store_db_init(None)
        self.timeout = timeout
        self.audit_type = audit_type
        self.locations = audit_type + "_locations"
        self.hosts_expr = hosts_expr

        self.host = None
        self.today = time.strftime("%Y%m%d", time.gmtime())
        self.basedir = None
        self.prompt = None
        clouseau.retention.cliutils.init_readline_hist()
        # this is arbitrary, can tweak it later
        # how many levels down we keep in our list of
        # top-level dirs from which the user can start
        # their interactive session
        self.max_depth_top_level = 3

        self.filtertype = 'all'

        # fixme completely wrong
        self.batchno = 1

        self.ignored = None
        self.local_ignores = None

        self.ignores = Ignores(self.confdir, self.cdb)
        self.ignores.get_ignores_from_rules_for_hosts()
        self.dircontents = CurrentDirContents(self.timeout)
        self.cenv = CurrentEnv()
        self.cmpl = Completion(self.dircontents, self.cenv, self.max_depth_top_level)
        clouseau.retention.config.set_up_conf(self.confdir)

    def do_one_host(self, host, report):
        self.set_host(host)
        self.ignores.get_ignores_from_rules_for_hosts([host])

        if host not in report:
            dirs_problem = None
            dirs_skipped = None
        else:
            dirs_problem, dirs_skipped = retention.remotefileauditor.get_dirs_toexamine(report[host])
        self.cenv.set_reported_dirs(dirs_problem, dirs_skipped)
        if self.cenv.problem_dirs is None and self.cenv.skipped_dirs is None:
            print "No report available from this host"
        elif len(self.cenv.problem_dirs) == 0 and len(self.cenv.skipped_dirs) == 0:
            print "No problem dirs and no skipped dirs on this host"
        else:
            dirs_problem_to_depth = [clouseau.retention.cliutils.get_path_prefix(
                d, self.max_depth_top_level)
                                     for d in dirs_problem]
            dirs_skipped = [s for s in dirs_skipped
                            if s not in dirs_problem_to_depth]
            relevant_dirs = (sorted(list(set(dirs_problem_to_depth)))
                             + sorted(list(set(dirs_skipped))))
            while True:
                dir_todo = self.cmpl.prompt_for_dir()
                if dir_todo is None:
                    print "Done with this host"
                    break
                elif dir_todo not in relevant_dirs:
                    print "Please choose one of the following directories:"
                    # fixme another arbitrary setting
                    clouseau.retention.cliutils.print_columns(relevant_dirs, 5)
                else:
                    self.basedir = None
                    self.cenv.cwdir = None
                    self.do_one_directory(dir_todo)

    def run(self, report, ignored):
        '''
        call with full report output (not summary) across
        hosts, this will permit the user to examine
        directories and files of specified hosts and
        add/update rules for those dirs and files
        '''
        self.ignored = ignored

        self.cenv.set_hosts(report.keys())
        while True:
            host_todo = self.cmpl.prompt_for_host()
            if host_todo is None:
                print "exiting at user request"
                break
            else:
                local_ign = RemoteUserCfGrabber(host_todo, self.timeout, self.audit_type, self.confdir)
                self.local_ignores = local_ign.run(True)
                local_ignored_dirs, local_ignored_files = clouseau.retention.ignores.process_local_ignores(
                    self.local_ignores, self.ignored)
                self.do_one_host(host_todo, report)

    def set_host(self, host):
        self.cenv.host = host

    def do_one_directory(self, path):
        '''
        given a list which contains absolute paths for the
        subdirectories / files of a given directory, (we don't
        go more than one level down, it's likely to be too much),
        ask the user what status to give this directory, and
        show the user information for each contained dir/file if
        desired, as well as info about the directory
        '''
        while True:
            todo = self.get_do_command(path)
            if todo is None:
                break

    def get_do_command(self, path):
        command = self.show_menu(path, 'top')
        return self.do_command(command, 'top', path)

    def get_menu_entry(self, choices, default, text):
        self.cmpl.set_choices_completion(choices, default)
        command = raw_input(text + " [%s]: " % default)
        command = command.strip()
        if command == "":
            command = default
        return command

    def show_menu(self, path, level):
        if level == 'top':
            text = ("S(set status)/E(examine directory)/"
                    "Filter directory listings/"
                    "I(ignore)/R(manage rules)/Q(quit menu)")
            command = self.get_menu_entry(['S', 'E', 'I', 'F', 'R', 'Q'], 'S', text)
        elif level == 'status':
            text = Status.get_statuses_prompt(", ") + ", Q(quit status menu)"
            command = self.get_menu_entry(Status.STATUSES + ['Q'], text, Status.text_to_status('good'))
            if command == 'Q' or command == 'q':
                level = 'top'
        elif level == 'examine':
            text = ("D(down a level)/U(up a level)/E(show entries)/"
                    "C(show contents of file)/R(show rules)/"
                    "F(filter directory listings/"
                    "M(mark file(s))/Q(quit examine menu)")
            command = self.get_menu_entry(['D', 'U', 'E', 'F', 'C', 'R', 'M', 'Q'], 'E', text)
            if command == 'Q' or command == 'q':
                level = 'top'
        elif level == 'rule':
            text = ("S(show all rules of type)/D(show rules covering dir)/"
                    "C(show rules covering dir contents)/"
                    "A(add rule to rules store)/"
                    "R(remove rule from rules store/"
                    "E(export rules from store to file)/"
                    "I(import rules from file to store)/Q(quit rule menu)")
            command = self.get_menu_entry(['S', 'C', 'A', 'R', 'E', 'I', 'Q'], 'D', text)
            if command == 'Q' or command == 'q':
                level = 'top'
        else:
            command = None
        return command

    def get_file_contents(self, path):
        # get 20 lines and hope that's enough for the user to evaluate
        # fixme the number of lines should be configurable
        fileexamin = RemoteFileExaminer(path, self.cenv.host, 20, self.timeout, quiet=True)
        contents = fileexamin.run()
        return contents

    def get_basedir_from_path(self, path):
        for location in clouseau.retention.config.cf[self.locations]:
            if path == location or path.startswith(location + os.path.sep):
                return location
        # fixme is this really the right fallback? check it
        return '/'

    def entry_is_not_ignored(self, path, entrytype):
        basedir = self.get_basedir_from_path(path)
        if self.audit_type == 'logs' and entrytype == 'file':
            path = LocalLogsAuditor.normalize(path)

        if entrytype == 'file':
            if clouseau.retention.ignores.file_is_ignored(path, basedir, self.ignored):
                return False

            # check perhost file
            if self.cenv.host in self.ignores.perhost_ignores:
                if clouseau.retention.ignores.file_is_ignored(
                        path, basedir,
                        self.ignores.perhost_ignores[self.cenv.host]):
                    return False

            # check perhost rules
            if self.cenv.host in self.ignores.perhost_ignores_from_rules:
                if clouseau.retention.ignores.file_is_ignored(
                        path, basedir,
                        self.ignores.perhost_ignores_from_rules[self.cenv.host]):
                    return False

        elif entrytype == 'dir':
            if clouseau.retention.ignores.dir_is_ignored(path, self.ignored):
                return False

            # check perhost file
            if self.cenv.host in self.ignores.perhost_ignores:
                if clouseau.retention.ignores.dir_is_ignored(
                        path, self.ignores.perhost_ignores[self.cenv.host]):
                    return False

            # check perhost rules
            if self.cenv.host in self.ignores.perhost_ignores_from_rules:
                if clouseau.retention.ignores.dir_is_ignored(
                        path, self.ignores.perhost_ignores_from_rules[self.cenv.host]):
                    return False
        else:
            # unknown type, I guess we skip it then
            return False

        return True

    # fixme use this (also make it have first + last, more helpful prolly)
    def set_prompt(self):
        if self.cenv.cwdir is None:
            self.prompt = "> "
        elif len(self.cenv.cwdir) < 10:
            self.prompt = self.cenv.cwdir + ">"
        else:
            self.prompt = "..." + self.cenv.cwdir[-7:] + ">"

    def get_entries_from_wildcard(self, file_expr):
        '''
        get entries from cwdir that match the
        expression
        '''
        # fixme that dang batchno, what a bad idea it was
        self.dircontents.get(self.cenv.host, self.cenv.cwdir, 1)
        # one wildcard only, them's the breaks
        if '*' in file_expr:
            start, end = file_expr.split('*', 1)
            return [c for c in self.dircontents.entries_dict
                    if (c.startswith(start) and
                        c.endswith(end) and
                        len(c) >= len(start) + len(end))]
        elif file_expr in self.dircontents.entries_dict:
            return [file_expr]
        else:
            return []

    def do_mark(self):
        readline.set_completer(self.cmpl.dir_entries_completion)
        file_expr = raw_input("file or dirname expression (empty to quit): ")
        file_expr = file_expr.strip()
        if file_expr == '':
            return True
        if file_expr[-1] == os.path.sep:
            file_expr = file_expr[:-1]
        if '*' in file_expr:
            entries_todo = self.get_entries_from_wildcard(file_expr)
        else:
            entries_todo = [file_expr]
            self.dircontents.get(self.cenv.host, self.cenv.cwdir, self.batchno)
            if not self.dircontents.entries:
                print 'failed to get directory contents for', self.cenv.cwdir
                print 'marking dirs/files regardless'
        for entry in entries_todo:
            if entry not in self.dircontents.entries_dict:
                print 'skipping %s, not in current dir listing' % entry
                print self.dircontents.entries_dict
                continue
            filetype = clouseau.retention.ruleutils.entrytype_to_text(
                self.dircontents.entries_dict[entry]['type'])
            if filetype == 'link':
                print 'No need to mark', file_expr, 'links are always skipped'
                continue
            elif filetype != 'dir' and filetype != 'file':
                print 'Not a dir or regular file, no need to mark, skipping'
                continue
            status = Status.text_to_status('good')
            clouseau.retention.ruleutils.do_add_rule(self.cdb, file_expr, filetype, status, self.cenv.host)
        return True

    def do_rule(self, command):
        if command == 'A' or command == 'a':
            # fixme need different completer here I think, that
            # completes relative to self.cwdir
            readline.set_completer(None)
            path = raw_input("path or wildcard expr in rule (empty to quit): ")
            path = path.strip()
            if path == '':
                return True
            default = Status.text_to_status('good')
            self.cmpl.set_choices_completion(Status.STATUSES + ['Q'], default)
            while True:
                statuses_text = Status.get_statuses_prompt(", ")
                status = raw_input(statuses_text + " Q(quit)) [%s]: " %
                                   default)
                status = status.strip()
                if status == "":
                    status = default
                if status[0].upper() in Status.STATUSES:
                    status = status[0].upper()
                    break
                elif status == 'q' or status == 'Q':
                    return None
                else:
                    print "Unknown status type"
                    continue

            # fixme should check that any wildcard is only one and only
            # in the last component... someday

            if path[0] != os.path.sep:
                path = os.path.join(self.cenv.cwdir, path)
            if path[-1] == os.path.sep:
                path = path[:-1]
                filetype = clouseau.retention.ruleutils.text_to_entrytype('dir')
            else:
                filetype = clouseau.retention.ruleutils.text_to_entrytype('file')

            clouseau.retention.ruleutils.do_add_rule(self.cdb, path, filetype, status, self.cenv.host)
            # update the ignores list since we have a new rule
            self.ignores.perhost_ignores_from_rules = {}
            self.ignores.get_ignores_from_rules_for_hosts([self.cenv.host])
            return True
        elif command == 'S' or command == 's':
            default = Status.text_to_status('problem')
            self.cmpl.set_choices_completion(['A'] + Status.STATUSES + ['Q'], default)
            while True:
                statuses_text = Status.get_statuses_prompt(", ")
                status = raw_input("status type A(all), " + statuses_text +
                                   ", Q(quit)) [%s]: " % default)
                status = status.strip()
                if status == "":
                    status = default

                if status == 'q' or status == 'Q':
                    return None
                elif status[0].upper() not in ['A'] + Status.STATUSES:
                    print "Unknown status type"
                    continue

                readline.set_completer(None)
                prefix = raw_input("starting with prefix? [/]: ")
                prefix = prefix.strip()
                if prefix == "":
                    prefix = "/"
                if status == 'a' or status == 'A':
                    clouseau.retention.ruleutils.show_rules(self.cdb, self.cenv.host, prefix=prefix)
                    return True
                elif status[0].upper() in Status.STATUSES:
                    clouseau.retention.ruleutils.show_rules(self.cdb, self.cenv.host, status[0].upper(),
                                                   prefix=prefix)
                    return True
        elif command == 'D' or command == 'd':
            self.dircontents.get(self.cenv.host, self.cenv.cwdir, self.batchno)
            clouseau.retention.ruleutils.get_rules_for_path(self.cdb, self.cenv.cwdir, self.cenv.host)
            return True
        elif command == 'C' or command == 'c':
            self.dircontents.get(self.cenv.host, self.cenv.cwdir, self.batchno)
            clouseau.retention.ruleutils.get_rules_for_entries(self.cdb, self.cenv.cwdir,
                                                      self.dircontents.entries_dict,
                                                      self.cenv.host)
            return True
        elif command == 'R' or command == 'r':
            # fixme need different completer here I think, that
            # completes relative to self.cwdir
            readline.set_completer(None)
            path = raw_input("path or wildcard expr in rule (empty to quit): ")
            path = path.strip()
            if path == '':
                return True
            elif path[0] != os.path.sep:
                path = os.path.join(self.cenv.cwdir, path)
            if path[-1] == os.path.sep:
                path = path[:-1]
            clouseau.retention.ruleutils.do_remove_rule(self.cdb, path, self.cenv.host)
            # update the ignores list since we removed a rule
            self.ignores.perhost_ignores_from_rules = {}
            self.ignores.get_ignores_from_rules_for_hosts([self.cenv.host])
            return True
        elif command == 'I' or command == 'i':
            readline.set_completer(None)
            rules_path = raw_input("full path to rules file (empty to quit): ")
            rules_path = rules_path.strip()
            if rules_path == '':
                return True
            if not clouseau.retention.cliutils.check_rules_path(rules_path):
                print "bad rules file path specified, aborting"
            else:
                clouseau.retention.ruleutils.import_rules(self.cdb, rules_path, self.cenv.host)
            return True
        elif command == 'E' or command == 'e':
            readline.set_completer(None)
            rules_path = raw_input("full path to rules file (empty to quit): ")
            rules_path = rules_path.strip()
            if rules_path == '':
                return True
            if not clouseau.retention.cliutils.check_rules_path(rules_path):
                print "bad rules file path specified, aborting"
            else:
                clouseau.retention.ruleutils.export_rules(self.cdb, rules_path, self.cenv.host)
            return True
        elif command == 'Q' or command == 'q':
            print "quitting this level"
            return None
        else:
            clouseau.retention.cliutils.show_help('rule')
            return True

    def do_file_contents(self):
        # fixme need a different completer here... meh
        readline.set_completer(None)
        filename = raw_input("filename (empty to quit): ")
        filename = filename.strip()
        if filename == '':
            return
        if filename[0] != os.path.sep:
            filename = os.path.join(self.cenv.cwdir, filename)
        contents = self.get_file_contents(filename)
        if contents is not None:
            print contents
        else:
            print "failed to get contents of file"

    def do_filter(self):
        default = 'C'
        self.cmpl.set_choices_completion(['A', 'D', 'F', 'C', 'Q'], default)
        while True:
            filtertype = raw_input("filter A(all), D(directories only),"
                                   " F(files only),"
                                   " C(Entries checked (not ignored),"
                                   " Q(quit)) [?]: ")
            filtertype = filtertype.strip()
            if filtertype == "":
                filtertype = default
            if filtertype == 'a' or filtertype == 'A':
                self.filtertype = 'all'
                return True
            elif filtertype == 'D' or filtertype == 'd':
                self.filtertype = 'dir'
                return True
            elif filtertype == 'F' or filtertype == 'f':
                self.filtertype = 'file'
                return True
            elif filtertype == 'C' or filtertype == 'c':
                self.filtertype = 'check'
                return True
            elif filtertype == 'q' or filtertype == 'Q':
                return None
            else:
                print "Unknown filter type"
                continue

    def do_examine(self, command):
        if command == 'D' or command == 'd':
            while True:
                # prompt user for dir to descend
                readline.set_completer(self.cmpl.dir_completion)
                directory = raw_input("directory name (empty to quit): ")
                directory = directory.strip()
                if directory == '':
                    return command
                if directory[-1] == os.path.sep:
                    directory = directory[:-1]
                if (directory[0] == '/' and
                        not directory.startswith(self.cenv.cwdir +
                                                 os.path.sep)):
                    print 'New directory is not a subdirectory of',
                    print self.cenv.cwdir, "skipping"
                else:
                    self.cenv.cwdir = os.path.join(self.cenv.cwdir,
                                                   directory)
                    self.dircontents.clear()
                    self.set_prompt()
                    print 'Now at', self.cenv.cwdir
                    return True
        elif command == 'U' or command == 'u':
            if self.cenv.cwdir != self.basedir:
                self.cenv.cwdir = os.path.dirname(self.cenv.cwdir)
                self.dircontents.clear()
                self.set_prompt()
                print 'Now at', self.cenv.cwdir
            else:
                print 'Already at top', self.cenv.cwdir
            return True
        elif command == 'E' or command == 'e':
            self.dircontents.show(self.cenv.host, self.cenv.cwdir, 1, self.filtertype, self.entry_is_not_ignored)
            return True
        elif command == 'C' or command == 'c':
            self.do_file_contents()
            return True
        elif command == 'F' or command == 'f':
            self.do_filter()
            return True
        elif command == 'R' or command == 'r':
            continuing = True
            while continuing:
                command = self.show_menu(self.cenv.cwdir, 'rule')
                continuing = self.do_command(command, 'rule', self.cenv.cwdir)
            return True
        elif command == 'M' or command == 'm':
            return self.do_mark()
        elif command == 'Q' or command == 'q' or command == '':
            print "quitting this level"
            return None
        else:
            clouseau.retention.cliutils.show_help('examine')
            return True

    def do_top(self, command, dir_path):
        if command == 'S' or command == 's':
            continuing = True
            while continuing:
                command = self.show_menu(dir_path, 'status')
                continuing = self.do_command(command, 'status', dir_path)
            return True
        elif command == 'E' or command == 'e':
            self.dircontents.show(self.cenv.host, self.cenv.cwdir, 1, self.filtertype, self.entry_is_not_ignored)
            continuing = True
            while continuing:
                # fixme this should let the user page through batches,
                # not use '1' every time
                command = self.show_menu(self.cenv.cwdir, 'examine')
                continuing = self.do_command(command, 'examine',
                                             self.cenv.cwdir)
            return True
        elif command == 'F' or command == 'f':
            self.do_filter()
            return True
        elif command == 'I' or command == 'i':
            # do nothing
            return command
        elif command == 'R' or command == 'r':
            continuing = True
            while continuing:
                command = self.show_menu(self.cenv.cwdir, 'rule')
                continuing = self.do_command(command, 'rule', self.cenv.cwdir)
            return True
        elif command == 'Q' or command == 'q':
            return None
        else:
            clouseau.retention.cliutils.show_help('top')
            return True

    def do_command(self, command, level, dir_path):
        if self.basedir is None:
            self.basedir = dir_path
        if self.cenv.cwdir is None:
            self.cenv.cwdir = dir_path

        if command is None:
            return

        if level == 'top':
            return self.do_top(command, dir_path)
        elif level == 'status':
            if command in Status.STATUSES:
                # this option is invoked on a directory so
                # type is dir every time
                clouseau.retention.ruleutils.do_add_rule(self.cdb, dir_path,
                                                clouseau.retention.ruleutils.text_to_entrytype('dir'),
                                                command, self.cenv.host)
                return None
            elif command == 'Q' or command == 'q':
                return None
            else:
                clouseau.retention.cliutils.show_help(level)
                return True
        elif level == 'examine':
            return self.do_examine(command)
        elif level == 'rule':
            return self.do_rule(command)
        else:
            return None
