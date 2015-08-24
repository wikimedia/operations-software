import os
import sys
import json
import readline
import traceback

from clouseau.retention.utils.status import Status
from clouseau.retention.utils.rule import RuleStore
import clouseau.retention.remote.remotefileauditor
from clouseau.retention.local.locallogaudit import LocalLogsAuditor
import clouseau.retention.utils.fileinfo
from clouseau.retention.utils.utils import JsonHelper
import clouseau.retention.utils.config
from clouseau.retention.remote.remoteexaminer import RemoteDirExaminer, RemoteFileExaminer
import clouseau.retention.utils.ruleutils
import clouseau.retention.utils.cliutils
from clouseau.retention.utils.ignores import Ignores
from clouseau.retention.remote.remoteusercfgrabber import RemoteUserCfGrabber
import clouseau.retention.utils.ignores
from clouseau.retention.utils.completion import Completion


class CurrentEnv(object):

    def __init__(self, host=None, hostlist=None, path=None, problems=None, skipped=None):
        self.host = host
        self.hostlist = hostlist
        self.cwdir = path
        self.problem_dirs = problems
        self.skipped_dirs = skipped
        self.prompt = ''

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

    def set_prompt(self):
        if self.cwdir is None:
            self.prompt = "> "
        elif len(self.cwdir) < 15:
            self.prompt = self.cwdir + ">"
        else:
            self.prompt = "..." + self.cwdir[-12:] + ">"


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

    def filter_items(self, filtertype, check_not_ignored):
        keys = self.entries_dict.keys()
        if filtertype == 'file':
            types = ['file']
        elif filtertype == 'dir':
            types = ['dir']
        else:
            types = ['dir', 'file']
        items = []
        for ftype in types:
            items = items + (sorted(
                item for item in keys
                if (self.entries_dict[item]['type'] == ftype and
                    check_not_ignored(self.entries_dict[item]['path'],
                                      self.entries_dict[item]['type'], ftype))))
        return items

    def show(self, host, path, batchno, filtertype, check_not_ignored, force=False):
        self.get(host, path, batchno, force)

        # fixme this 50 is pretty arbitrary oh well
        justify = 50

        items = self.filter_items(filtertype, check_not_ignored)

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
                    result = clouseau.retention.utils.fileinfo.format_pretty_output_from_dict(
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

            page = clouseau.retention.utils.cliutils.show_pager(page, num_items, num_per_page)
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

    def __init__(self, confdir, store_filepath, timeout, audit_type, ignore_also=None, hosts_expr=None):
        self.confdir = confdir

        self.cdb = RuleStore(store_filepath)
        self.cdb.store_db_init(None)

        self.timeout = timeout
        self.audit_type = audit_type
        self.locations = audit_type + "_locations"
        self.hosts_expr = hosts_expr

        self.basedir = None

        clouseau.retention.utils.cliutils.init_readline_hist()
        # this is arbitrary, can tweak it later
        # how many levels down we keep in our list of
        # top-level dirs from which the user can start
        # their interactive session
        self.max_depth_top_level = 3

        self.filtertype = 'all'

        # fixme completely wrong
        self.batchno = 1

        clouseau.retention.utils.config.set_up_conf(self.confdir)

        # duplicate all the ignores except for the uh
        # ones specific to a host. those will be done
        # at host choice time
        # this includes rules, we will do those at host choice time too
        # we want: global, perhost, ignore_also (if there were any)

        self.local_ignored = None
        self.ignores = Ignores(self.confdir)
        self.ignored_from_rulestore = {}
        self.ignored_also = clouseau.retention.utils.ignores.convert_ignore_also_to_ignores(ignore_also)

        self.dircontents = CurrentDirContents(self.timeout)
        self.cenv = CurrentEnv()
        self.cmpl = Completion(self.dircontents, self.cenv, self.max_depth_top_level)

    def do_one_host(self, host, report):
        self.set_host(host)
        results = clouseau.retention.utils.ignores.get_ignored_from_rulestore(self.cdb, [host])
        if host in results:
            self.ignored_from_rulestore[host] = results[host]

        if host not in report:
            dirs_problem = None
            dirs_skipped = None
        else:
            dirs_problem, dirs_skipped = clouseau.retention.remote.remotefileauditor.get_dirs_toexamine(report[host])
        self.cenv.set_reported_dirs(dirs_problem, dirs_skipped)
        if self.cenv.problem_dirs is None and self.cenv.skipped_dirs is None:
            print "No report available from this host"
        elif len(self.cenv.problem_dirs) == 0 and len(self.cenv.skipped_dirs) == 0:
            print "No problem dirs and no skipped dirs on this host"
        else:
            dirs_problem_to_depth = [clouseau.retention.utils.cliutils.get_path_prefix(
                d, self.max_depth_top_level) for d in dirs_problem]
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
                    clouseau.retention.utils.cliutils.print_columns(relevant_dirs, 5)
                else:
                    self.basedir = None
                    self.cenv.cwdir = None
                    self.do_one_directory(dir_todo)

    def run(self, report):
        '''
        call with full report output (not summary) across
        hosts, this will permit the user to examine
        directories and files of specified hosts and
        add/update rules for those dirs and files
        '''
        self.cenv.set_hosts(report.keys())
        while True:
            host_todo = self.cmpl.prompt_for_host()
            if host_todo is None:
                print "exiting at user request"
                break
            else:
                usercfgrab = RemoteUserCfGrabber(host_todo, self.timeout, self.audit_type, self.confdir)
                to_convert = usercfgrab.run(True)
                self.local_ignored = clouseau.retention.utils.ignores.process_local_ignores(to_convert)

                results = clouseau.retention.utils.ignores.get_ignored_from_rulestore(self.cdb, [host_todo])
                if host_todo in results:
                    self.ignored_from_rulestore[host_todo] = results[host_todo]

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
        command = self.show_menu('top')
        return self.do_command(command, 'top', path)

    def get_menu_entry(self, choices, default, text):
        self.cmpl.set_choices_completion(choices, default)
        self.cenv.set_prompt()
        command = raw_input(self.cenv.prompt + ' ' + text + " [%s]: " % default)
        command = command.strip()
        if command == "":
            command = default
        return command

    def show_menu(self, level):
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
        for location in clouseau.retention.utils.config.conf[self.locations]:
            if path == location or path.startswith(location + os.path.sep):
                return location
        # fixme is this really the right fallback? check it
        return '/'

    def entry_is_not_ignored(self, path, entrytype, do_check):
        '''
        see if the given entry is in NOT in the ingored lists and return
        True if so, False otherwise
        we only do this check if the do_check argment is set to 'check';
        otherwise we default to True
        '''
        if do_check != 'check':
            return True

        basedir = self.get_basedir_from_path(path)
        if self.audit_type == 'logs' and entrytype == 'file':
            path = LocalLogsAuditor.normalize(path)

        if entrytype == 'file':
            checker = clouseau.retention.utils.ignores.file_is_ignored
            dirs = False
        else:
            checker = clouseau.retention.utils.ignores.dir_is_ignored
            dirs = True
            for ignored in [self.ignores.global_ignored,
                            self.ignored_also]:
                if dirs:
                    result = checker(path, ignored)
                else:
                    result = checker(path, basedir, ignored)
                if result:
                    return False

            for ignored in [self.ignores.perhost_ignored,
                            self.ignored_from_rulestore]:
                if self.cenv.host in ignored:
                    if dirs:
                        result = checker(path, ignored[self.cenv.host])
                    else:
                        result = checker(path, basedir, ignored[self.cenv.host])
                    if result:
                        return False

        return True

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
            filetype = clouseau.retention.utils.ruleutils.entrytype_to_text(
                self.dircontents.entries_dict[entry]['type'])
            if filetype == 'link':
                print 'No need to mark', file_expr, 'links are always skipped'
                continue
            elif filetype != 'dir' and filetype != 'file':
                print 'Not a dir or regular file, no need to mark, skipping'
                continue
            status = Status.text_to_status('good')
            clouseau.retention.utils.ruleutils.do_add_rule(self.cdb, file_expr, filetype, status, self.cenv.host)
        return True

    def do_add_rule(self):
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
            filetype = clouseau.retention.utils.ruleutils.text_to_entrytype('dir')
        else:
            filetype = clouseau.retention.utils.ruleutils.text_to_entrytype('file')

        clouseau.retention.utils.ruleutils.do_add_rule(self.cdb, path, filetype, status, self.cenv.host)
        # update the ignores list since we have a new rule
        results = clouseau.retention.utils.ignores.get_ignored_from_rulestore(self.cdb, [self.cenv.host])
        if self.cenv.host in results:
            self.ignored_from_rulestore[self.cenv.host] = results[self.cenv.host]
        return True

    def do_show_rules_with_status(self):
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
                clouseau.retention.utils.ruleutils.show_rules(self.cdb, self.cenv.host, prefix=prefix)
                return True
            elif status[0].upper() in Status.STATUSES:
                clouseau.retention.utils.ruleutils.show_rules(self.cdb, self.cenv.host, status[0].upper(),
                                                        prefix=prefix)
                return True

    def do_remove_rule(self):
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
        clouseau.retention.utils.ruleutils.do_remove_rule(self.cdb, path, self.cenv.host)
        # update the ignores list since we removed a rule
        results = clouseau.retention.utils.ignores.get_ignored_from_rulestore(self.cdb, [self.cenv.host])
        if self.cenv.host in results:
            self.ignored_from_rulestore[self.cenv.host] = results[self.cenv.host]
        return True

    def get_rules_path(self):
        readline.set_completer(None)
        rules_path = raw_input("full path to rules file (empty to quit): ")
        rules_path = rules_path.strip()
        if rules_path == '':
            return rules_path
        if not clouseau.retention.utils.cliutils.check_rules_path(rules_path):
            print "bad rules file path specified, aborting"
            return ''
        return rules_path

    def do_rule(self, command):
        if command == 'A' or command == 'a':
            result = self.do_add_rule()
        elif command == 'S' or command == 's':
            result = self.do_show_rules_with_status()
        elif command == 'D' or command == 'd':
            self.dircontents.get(self.cenv.host, self.cenv.cwdir, self.batchno)
            clouseau.retention.utils.ruleutils.get_rules_for_path(self.cdb, self.cenv.cwdir, self.cenv.host)
            result = True
        elif command == 'C' or command == 'c':
            self.dircontents.get(self.cenv.host, self.cenv.cwdir, self.batchno)
            clouseau.retention.utils.ruleutils.get_rules_for_entries(self.cdb, self.cenv.cwdir,
                                                               self.dircontents.entries_dict,
                                                               self.cenv.host)
            result = True
        elif command == 'R' or command == 'r':
            result = self.do_remove_rule()
        elif command == 'I' or command == 'i':
            rules_path = self.get_rules_path()
            if rules_path != '':
                clouseau.retention.utils.ruleutils.import_rules(self.cdb, rules_path, self.cenv.host)
            result = True
        elif command == 'E' or command == 'e':
            rules_path = self.get_rules_path()
            if rules_path != '':
                clouseau.retention.utils.ruleutils.export_rules(self.cdb, rules_path, self.cenv.host)
            result = True
        elif command == 'Q' or command == 'q':
            print "quitting this level"
            result = None
        else:
            clouseau.retention.utils.cliutils.show_help('rule')
            result = True
        return result

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

    def do_dir_descend(self, command):
        while True:
            # prompt user for dir to descend
            readline.set_completer(self.cmpl.dir_completion)
            self.cenv.set_prompt()
            directory = raw_input(self.cenv.prompt + ' ' + "directory name (empty to quit): ")
            directory = directory.strip()
            if directory == '':
                return command
            if directory[-1] == os.path.sep:
                directory = directory[:-1]
            if (directory[0] == '/' and
                    not directory.startswith(self.cenv.cwdir + os.path.sep)):
                print 'New directory is not a subdirectory of',
                print self.cenv.cwdir, "skipping"
            else:
                self.cenv.cwdir = os.path.join(self.cenv.cwdir,
                                               directory)
                self.dircontents.clear()
                self.cenv.set_prompt()
                print 'Now at', self.cenv.cwdir
                return True

    def do_examine(self, command):
        if command == 'D' or command == 'd':
            return self.do_dir_descend(command)
        elif command == 'U' or command == 'u':
            if self.cenv.cwdir != self.basedir:
                self.cenv.cwdir = os.path.dirname(self.cenv.cwdir)
                self.dircontents.clear()
                self.cenv.set_prompt()
                print 'Now at', self.cenv.cwdir
            else:
                print 'Already at top', self.cenv.cwdir
            result = True
        elif command == 'E' or command == 'e':
            self.dircontents.show(self.cenv.host, self.cenv.cwdir, 1, self.filtertype, self.entry_is_not_ignored)
            result = True
        elif command == 'C' or command == 'c':
            self.do_file_contents()
            result = True
        elif command == 'F' or command == 'f':
            self.do_filter()
            result = True
        elif command == 'R' or command == 'r':
            continuing = True
            while continuing:
                command = self.show_menu('rule')
                continuing = self.do_command(command, 'rule', self.cenv.cwdir)
            result = True
        elif command == 'M' or command == 'm':
            result = self.do_mark()
        elif command == 'Q' or command == 'q' or command == '':
            print "quitting this level"
            result = None
        else:
            clouseau.retention.utils.cliutils.show_help('examine')
            result = True
        return result

    def do_top(self, command, dir_path):
        result = True
        if command == 'S' or command == 's':
            continuing = True
            while continuing:
                command = self.show_menu('status')
                continuing = self.do_command(command, 'status', dir_path)
        elif command == 'E' or command == 'e':
            self.dircontents.show(self.cenv.host, self.cenv.cwdir, 1, self.filtertype, self.entry_is_not_ignored)
            continuing = True
            while continuing:
                # fixme this should let the user page through batches,
                # not use '1' every time
                command = self.show_menu('examine')
                continuing = self.do_command(command, 'examine',
                                             self.cenv.cwdir)
        elif command == 'F' or command == 'f':
            self.do_filter()
        elif command == 'I' or command == 'i':
            # do nothing
            result = command
        elif command == 'R' or command == 'r':
            continuing = True
            while continuing:
                command = self.show_menu('rule')
                continuing = self.do_command(command, 'rule', self.cenv.cwdir)
        elif command == 'Q' or command == 'q':
            result = None
        else:
            clouseau.retention.utils.cliutils.show_help('top')
        return result

    def do_command(self, command, level, dir_path):
        result = None
        if self.basedir is None:
            self.basedir = dir_path
        if self.cenv.cwdir is None:
            self.cenv.cwdir = dir_path

        if command is None:
            return None

        if level == 'top':
            result = self.do_top(command, dir_path)
        elif level == 'status':
            if command in Status.STATUSES:
                # this option is invoked on a directory so
                # type is dir every time
                clouseau.retention.utils.ruleutils.do_add_rule(self.cdb, dir_path,
                                                         clouseau.retention.utils.ruleutils.text_to_entrytype('dir'),
                                                         command, self.cenv.host)
                return None
            elif command == 'Q' or command == 'q':
                return None
            else:
                clouseau.retention.utils.cliutils.show_help(level)
                result = True
        elif level == 'examine':
            result = self.do_examine(command)
        elif level == 'rule':
            result = self.do_rule(command)
        return result
