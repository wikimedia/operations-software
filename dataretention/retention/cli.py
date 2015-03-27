import os
import sys
import time
import json
import runpy
import readline
import atexit
import traceback

sys.path.append('/srv/audits/retention/scripts/')

from retention.status import Status
from retention.rule import RuleStore
import retention.remotefileauditor
from retention.localhomeaudit import LocalHomesAuditor
from retention.locallogaudit import LocalLogsAuditor
from retention.fileinfo import FileInfo
import retention.utils
from retention.utils import JsonHelper
from retention.config import Config
from retention.examiner import RemoteDirExaminer, RemoteFileExaminer
import retention.fileutils
import retention.ruleutils
from retention.userconfretriever import RemoteUserCfRetriever


class CommandLine(object):
    '''
    prompt user at the command line for actions to take on a given
    directory or file, show results
    '''

    # todo: down and up should check you really are (descending,
    # ascending path)

    def __init__(self, store_filepath, timeout, audit_type, hosts_expr=None):
        self.cdb = RuleStore(store_filepath)
        self.cdb.store_db_init(None)
        self.timeout = timeout
        self.audit_type = audit_type
        self.locations = audit_type + "_locations"
        self.hosts_expr = hosts_expr

        self.host = None
        self.today = time.strftime("%Y%m%d", time.gmtime())
        self.basedir = None
        self.current_dir = None
        self.prompt = None
        CommandLine.init_readline_hist()
        self.hostlist = None
        self.dirs_problem = None
        self.dirs_skipped = None
        self.current_dir_contents_list = None
        self.current_dir_contents_dict = None
        # this is arbitrary, can tweak it later
        # how many levels down we keep in our list of
        # top-level dirs from which the user can start
        # their interactive session
        self.max_depth_top_level = 3

        self.choices = None
        self.choice_default = None

        self.filtertype = 'all'

        # fixme completely wrong
        self.batchno = 1

        self.ignored = None
        self.local_ignores = None

        self.perhost_ignores = {}
        self.perhost_rules_from_file = None
        self.get_perhostcf_from_file()
        self.perhost_ignores_from_rules = {}
        self.get_perhost_ignores_from_rules()

    def get_perhost_ignores_from_rules(self, hosts=None):
        if hosts is None:
            hosts = self.cdb.store_db_list_all_hosts()
        for host in hosts:
            self.perhost_rules_from_store = retention.ruleutils.get_rules(
                self.cdb, host, Status.text_to_status('good'))

            if self.perhost_rules_from_store is not None:
                if host not in self.perhost_ignores_from_rules:
                    self.perhost_ignores_from_rules[host] = {}
                    self.perhost_ignores_from_rules[host]['dirs'] = {}
                    self.perhost_ignores_from_rules[host]['dirs']['/'] = []
                    self.perhost_ignores_from_rules[host]['files'] = {}
                    self.perhost_ignores_from_rules[host]['files']['/'] = []

                if (self.perhost_rules_from_file is not None and
                        'ignored_dirs' in self.perhost_rules_from_file and
                        host in self.perhost_rules_from_file['ignored_dirs']):
                    for path in self.perhost_rules_from_file['ignored_dirs'][host]:
                        if (path.startswith('/') and
                                path not in self.perhost_ignores_from_rules[host][
                                    'dirs']['/']):
                            if path[-1] == '/':
                                path = path[:-1]
                            self.perhost_ignores_from_rules[host][
                                'dirs']['/'].append(path)
                if (self.perhost_rules_from_file is not None and
                        'ignored_files' in self.perhost_rules_from_file and
                        host in self.perhost_rules_from_file['ignored_files']):
                    for path in self.perhost_rules_from_file['ignored_files'][host]:
                        if (path.startswith('/') and
                                path not in self.perhost_ignores_from_rules[
                                    host]['files']['/']):
                            self.perhost_ignores_from_rules[host]['files']['/'].append(path)

    def get_perhostcf_from_file(self):
        if os.path.exists('audit_files_perhost_config.py'):
            try:
                self.perhost_rules_from_file = runpy.run_path(
                    'audit_files_perhost_config.py')['perhostcf']
            except:
                self.perhost_rules_from_file = None

        if self.perhost_rules_from_file is not None:
            if 'ignored_dirs' in self.perhost_rules_from_file:
                for host in self.perhost_rules_from_file['ignored_dirs']:
                    if host not in self.perhost_ignores:
                        self.perhost_ignores[host] = {}
                    self.perhost_ignores[host]['dirs'] = {}
                    self.perhost_ignores[host]['dirs']['/'] = [
                        (lambda path: path[:-1] if path[-1] == '/'
                         else path)(p)
                        for p in self.perhost_rules_from_file[
                            'ignored_dirs'][host]]
            if 'ignored_files' in self.perhost_rules_from_file:
                for host in self.perhost_rules_from_file['ignored_files']:
                    if host not in self.perhost_ignores:
                        self.perhost_ignores[host] = {}
                    self.perhost_ignores[host]['files'] = {}
                    self.perhost_ignores[host]['files']['/'] = (
                        self.perhost_rules_from_file['ignored_files'][host])

    @staticmethod
    def init_readline_hist():
        readline.parse_and_bind("tab: complete")
        histfile = os.path.join(os.path.expanduser("~"), ".audit_hist")
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        atexit.register(readline.write_history_file, histfile)
        # also fix up delims so we don't have annoying dir elt behavior
        delims = readline.get_completer_delims()
        delims = delims.replace("/", "")
        readline.set_completer_delims(delims)

    def save_history(self, histfile):
        readline.write_history_file(histfile)

    def host_completion(self, text, state):
        if text == "":
            matches = self.hostlist
        else:
            matches = [h for h in self.hostlist
                       if h.startswith(text)]
        if len(matches) > 1 and state == 0:
            for m in matches:
                print m,
            print

        try:
            return matches[state]
        except IndexError:
            return None

    def prompt_for_host(self):
        '''
        prompt user for host in self.hostlist,
        with tab completion
        '''
        readline.set_completer(self.host_completion)
        while True:
            host_todo = raw_input(
                "Host on which to examine dirs/files (blank to exit): ")
            host_todo = host_todo.strip()
            if host_todo == "":
                return None
            if host_todo in self.hostlist:
                return host_todo
            else:
                print "Please choose one of the following hosts:"
                CommandLine.print_columns(self.hostlist, 4)

    def dir_completion(self, text, state):
        if self.current_dir is None:
            dirs_problem_to_depth = [CommandLine.get_path_prefix(
                d, self.max_depth_top_level) for d in self.dirs_problem]
            dirs_skipped = [s for s in self.dirs_skipped
                            if s not in dirs_problem_to_depth]
            relevant_dirs = (sorted(list(set(dirs_problem_to_depth)))
                             + sorted(list(set(dirs_skipped))))
        else:
            if self.current_dir_contents_list is None:
                self.get_dir_contents(self.current_dir, self.batchno)
            relevant_dirs = sorted([s for s in self.current_dir_contents_dict
                                    if self.current_dir_contents_dict[s]['type'] == 'dir'])
        if text == "":
            matches = relevant_dirs
        else:
            depth = text.count(os.path.sep)
            # how many path elts do we have in the text, show
            # matches for basedir of it plus next elt
            matches = ([d for d in relevant_dirs
                        if d.startswith(text) and
                        d.count(os.path.sep) == depth])
        try:
            return matches[state]
        except IndexError:
            return None

    def dir_entries_completion(self, text, state):
        if not self.current_dir_contents_list:
            self.get_dir_contents(self.current_dir, self.batchno)
        entries = sorted([s for s in self.current_dir_contents_dict
                          if (self.current_dir_contents_dict[s]['type'] == 'file' or
                              self.current_dir_contents_dict[s]['type'] == 'dir')])
        if text == "":
            matches = entries
        else:
            depth = text.count(os.path.sep)
            # how many path elts do we have in the text, show
            # matches for basedir of it plus next elt
            matches = ([d for d in entries
                        if d.startswith(text) and
                        d.count(os.path.sep) == depth])
        try:
            return matches[state]
        except IndexError:
            return None

    def prompt_for_dir(self):
        '''
        prompt user for host in self.hostlist,
        with tab completion
        '''

        readline.set_completer(self.dir_completion)
        dir_todo = raw_input("Directory (blank to exit): ")
        dir_todo = dir_todo.strip()
        if dir_todo == "":
            return None
        else:
            return dir_todo

    def choices_completion(self, text, state):
        matches = self.choices
        if text == "":
            matches = [self.choice_default]
        try:
            return matches[state]
        except IndexError:
            return None

    @staticmethod
    def get_path_prefix(path, depth):
        if path is None:
            return path
        if path.count(os.path.sep) < depth:
            return path
        fields = path.split(os.path.sep)
        return os.path.sep.join(fields[:depth + 1])

    @staticmethod
    def print_columns(items, cols):
        num_rows = len(items) / cols
        extra = len(items) % cols
        if extra:
            num_rows = num_rows + 1

        max_len = {}
        for col in range(0, cols):
            max_len[col] = 0

        for row in range(0, num_rows):
            for col in range(0, cols):
                try:
                    text = items[row + num_rows * col]
                except IndexError:
                    continue
                try:
                    count = len(unicode(text, 'utf-8'))
                except:
                    count = len(text)
                if len(text) > max_len[col]:
                    max_len[col] = len(text)

        for row in range(0, num_rows):
            for col in range(0, cols):
                try:
                    # fixme ljust probably gets this wrong for
                    # text that's really multibyte chars
                    print items[row + num_rows * col].ljust(max_len[col]),
                except IndexError:
                    pass
            print

    def do_one_host(self, host, report):
        self.set_host(host)
        if not retention.utils.running_locally(self.host):
            self.get_perhost_ignores_from_rules([host])

        if retention.utils.running_locally(self.host):
            self.dirs_problem, self.dirs_skipped = retention.remotefileauditor.get_dirs_toexamine(report)
        else:
            if host not in report:
                self.dirs_problem = None
                self.dirs_skipped = None
            else:
                self.dirs_problem, self.dirs_skipped = retention.remotefileauditor.get_dirs_toexamine(report[host])
        if self.dirs_problem is None and self.dirs_skipped is None:
            print "No report available from this host"
        elif len(self.dirs_problem) == 0 and len(self.dirs_skipped) == 0:
            print "No problem dirs and no skipped dirs on this host"
        else:
            dirs_problem_to_depth = [CommandLine.get_path_prefix(
                d, self.max_depth_top_level)
                                     for d in self.dirs_problem]
            dirs_skipped = [s for s in self.dirs_skipped
                            if s not in dirs_problem_to_depth]
            relevant_dirs = (sorted(list(set(dirs_problem_to_depth)))
                             + sorted(list(set(dirs_skipped))))
            while True:
                dir_todo = self.prompt_for_dir()
                if dir_todo is None:
                    print "Done with this host"
                    break
                elif dir_todo not in relevant_dirs:
                    print "Please choose one of the following directories:"
                    # fixme another arbitrary setting
                    CommandLine.print_columns(relevant_dirs, 5)
                else:
                    self.basedir = None
                    self.current_dir = None
                    self.do_one_directory(dir_todo)

    def run(self, report, ignored):
        '''
        call with full report output (not summary) across
        hosts, this will permit the user to examine
        directories and files of specified hosts and
        add/update rules for those dirs and files
        '''
        self.ignored = ignored
        if retention.utils.running_locally(self.hosts_expr):
            host_todo = "localhost"
            self.do_one_host(host_todo, report)
            return

        self.hostlist = report.keys()
        while True:
            host_todo = self.prompt_for_host()
            if host_todo is None:
                print "exiting at user request"
                break
            else:
                local_ign = RemoteUserCfRetriever(host_todo, self.timeout, self.audit_type)
                self.local_ignores = local_ign.run(True)
                local_ignored_dirs, local_ignored_files = LocalHomesAuditor.process_local_ignores(
                    self.local_ignores, self.ignored)
                self.do_one_host(host_todo, report)

    def set_host(self, host):
        self.host = host

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

    def show_menu(self, path, level):
        if level == 'top':
            self.choices = ['S', 'E', 'I', 'F', 'R', 'Q']
            self.choice_default = 'S'
            readline.set_completer(self.choices_completion)
            command = raw_input("S(set status)/E(examine directory)/"
                                "Filter directory listings/"
                                "I(ignore)/R(manage rules)/Q(quit menu) [S]: ")
            command = command.strip()
            if command == "":
                command = self.choice_default
        elif level == 'status':
            self.choices = Status.STATUSES + ['Q']
            self.choice_default = Status.text_to_status('good')
            readline.set_completer(self.choices_completion)
            statuses_text = Status.get_statuses_prompt(", ")
            command = raw_input(statuses_text + ", Q(quit status menu) [%s]: "
                                % self.choice_default)
            command = command.strip()
            if command == "":
                command = self.choice_default
            elif command == 'Q' or command == 'q':
                level = 'top'
        elif level == 'examine':
            self.choices = ['D', 'U', 'E', 'F', 'C', 'R', 'M', 'Q']
            self.choice_default = 'E'
            readline.set_completer(self.choices_completion)
            command = raw_input("D(down a level)/U(up a level)/E(show entries)/"
                                "C(show contents of file)/R(show rules)/"
                                "F(filter directory listings/"
                                "M(mark file(s))/Q(quit examine menu) [E]: ")
            command = command.strip()
            if command == "":
                command = self.choice_default
            elif command == 'Q' or command == 'q':
                level = 'top'
        elif level == 'rule':
            self.choices = ['S', 'C', 'A', 'R', 'E', 'I', 'Q']
            self.choice_default = 'D'
            readline.set_completer(self.choices_completion)
            command = raw_input("S(show all rules of type)/D(show rules covering dir)/"
                                "C(show rules covering dir contents)/"
                                "A(add rule to rules store)/"
                                "R(remove rule from rules store/"
                                "E(export rules from store to file)/"
                                "I(import rules from file to store)/Q(quit rule menu) [D]: ")
            command = command.strip()
            if command == "":
                command = self.choice_default
            elif command == 'Q' or command == 'q':
                level = 'top'
        else:
            command = None
        return command

    @staticmethod
    def show_help(level):
        if level == 'status':
            print """Status must be one of the following:
            P  (the directory or file may contain sensitive information)
            G  (the directory or file is known to be ok and should remain so)
            R  (the directory or file is known to be ok but entries
                must be rechecked on next run)
            U  (the file or directory has not been checked, status unknown)
            Q  (quit this level of the menu)"""
        elif level == 'top':
            print """Command must be one of the following:
            S  set the status for the directory
            E  examine the directory
            F set filter for listing directory contents
            I  ignore this directory or file for now
            R  show rules for all dirs/files
            Q  quit the menu"""
        elif level == 'examine':
            print """Command must be one of the following:
            D descend the directory tree one level (user will be prompted for subdir)
            U ascend the directory tree one level (not higher than base of tree)
            E show information on entries in directory
            F set filter for listing directory contents
            C show first few lines of contents of file in directory
            R  show rules covering current directory
            M  mark file(s) as ok (user will be prompted for filename expr)
            Q  quit the menu"""
        elif level == 'rule':
            print """Command must be one of the following:
            S show all rules for this host
            D show all rules covering the current directory
            C show all rules covering current directory contents
            A add rule to rules store
            R remove rule from rules store
            I import rules from file (overrides dups, won't remove other rules)
            E export rules to file
            Q quit the menu"""
        else:
            print "unknown help level requested,", level

    def get_dir_contents(self, path, batchno):
        # via salt get the directory contents for the first N = 1000
        # entries, unsorted.

        # fixme batchno? batchno should increment too
        # for now more than 1000 entries in a dir = we silently toss them
        direxamin = RemoteDirExaminer(path, self.host, batchno, 1000, self.timeout, prettyprint=False)
        contents = direxamin.run(True)
        if contents is not None:
            contents = contents.split("\n")

        self.current_dir_contents_list = []
        self.current_dir_contents_dict = {}

        if contents is None:
            return

        for item in contents:
            try:
                result = json.loads(item, object_hook=JsonHelper.decode_dict)
                self.current_dir_contents_list.append(result)
                self.current_dir_contents_dict[result['path']] = result
            except:
                print "WARNING: problem getting dir contents, retrieved", item
#                exc_type, exc_value, exc_traceback = sys.exc_info()
#                sys.stderr.write(repr(traceback.format_exception(
#                    exc_type, exc_value, exc_traceback)))

    def get_file_contents(self, path):
        # get 20 lines and hope that's enough for the user to evaluate
        # fixme the number of lines should be configurable
        fileexamin = RemoteFileExaminer(path, self.host, 20, self.timeout, quiet=True)
        contents = fileexamin.run()
        return contents

    @staticmethod
    def show_pager(current_page, num_items, num_per_page):
        readline.set_completer(None)
        while True:
            to_show = raw_input("P(prev)/N(next)/F(first)/"
                                "L(last)/<num>(go to page num)/Q(quit) [N]: ")
            to_show = to_show.strip()
            if to_show == "":
                to_show = 'N'

            if to_show == 'P' or to_show == 'p':
                # prev page
                if current_page > 1:
                    return current_page - 1
                else:
                    return current_page

            elif to_show == 'N' or to_show == 'n':
                # next page
                num_pages = num_items / num_per_page
                if num_items % num_per_page:
                    num_pages += 1
                if current_page < num_pages:
                    return current_page + 1
                else:
                    return current_page

            elif to_show == 'F' or to_show == 'f':
                # first page
                return 1

            elif to_show == 'L' or 'to_show' == 'l':
                # last page
                num_pages = num_items / num_per_page
                if num_items % num_per_page:
                    num_pages += 1
                return num_pages

            elif to_show.isdigit():
                desired_page = int(to_show)
                num_pages = num_items / num_per_page
                if num_items % num_per_page:
                    num_pages += 1

                if desired_page < 1:
                    return 1
                elif desired_page > num_pages:
                    return num_pages
                else:
                    return desired_page

            elif to_show == 'Q' or to_show == 'q':
                return None
            else:
                print "unknown option"

    def get_basedir_from_path(self, path):
        for location in Config.cf[self.locations]:
            if path == location or path.startswith(location + os.path.sep):
                return location
        # fixme is this really the right fallback? check it
        return '/'

    def entry_is_not_ignored(self, path, entrytype):
        basedir = self.get_basedir_from_path(path)
        if self.audit_type == 'logs' and entrytype == 'file':
            path = LocalLogsAuditor.normalize(path)

        if entrytype == 'file':
            if retention.fileutils.file_is_ignored(path, basedir, self.ignored):
                return False

            # check perhost file
            if self.host in self.perhost_ignores:
                if retention.fileutils.file_is_ignored(
                        path, basedir,
                        self.perhost_ignores[self.host]):
                    return False

            # check perhost rules
            if self.host in self.perhost_ignores_from_rules:
                if retention.fileutils.file_is_ignored(
                        path, basedir,
                        self.perhost_ignores_from_rules[self.host]):
                    return False

        elif entrytype == 'dir':
            if retention.fileutils.dir_is_ignored(path, self.ignored):
                return False

            # check perhost file
            if self.host in self.perhost_ignores:
                if retention.fileutils.dir_is_ignored(
                        path, self.perhost_ignores[self.host]):
                    return False

            # check perhost rules
            if self.host in self.perhost_ignores_from_rules:
                if retention.fileutils.dir_is_ignored(
                        path, self.perhost_ignores_from_rules[self.host]):
                    return False
        else:
            # unknown type, I guess we skip it then
            return False

        return True

    def show_dir_contents(self, path, batchno):
        self.get_dir_contents(path, batchno)

        # fixme this 50 is pretty arbitrary oh well
        justify = 50

        keys = self.current_dir_contents_dict.keys()
        if self.filtertype == 'file':
            items = (sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'file'))
        elif self.filtertype == 'dir':
            items = (sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'dir'))
        elif self.filtertype == 'all':
            items = sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'dir')
            items = items + sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'file')
        elif self.filtertype == 'check':
            items = sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'dir'
                and self.entry_is_not_ignored(
                    self.current_dir_contents_dict[item]['path'],
                    self.current_dir_contents_dict[item]['type']))
            items = items + sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'file'
                and self.entry_is_not_ignored(
                    self.current_dir_contents_dict[item]['path'],
                    self.current_dir_contents_dict[item]['type']))

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
                        self.current_dir_contents_dict[item], path_justify=justify)
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

            page = CommandLine.show_pager(page, num_items, num_per_page)
            if page is None:
                return
            elif page == num_pages:
                num_to_show = num_in_last_page
            else:
                num_to_show = num_per_page

    # fixme use this (also make it have first + last, more helpful prolly)
    def set_prompt(self):
        if self.current_dir is None:
            self.prompt = "> "
        elif len(self.current_dir) < 10:
            self.prompt = self.current_dir + ">"
        else:
            self.prompt = "..." + self.current_dir[-7:] + ">"

    def get_entries_from_wildcard(self, file_expr):
        '''
        get entries from current_dir that match the
        expression
        '''
        # fixme that dang batchno, what a bad idea it was
        if self.current_dir_contents_list is None:
            self.get_dir_contents(self.current_dir, 1)
        # one wildcard only, them's the breaks
        if '*' in file_expr:
            start, end = file_expr.split('*', 1)
            return [c for c in self.current_dir_contents_dict
                    if (c.startswith(start) and
                        c.endswith(end) and
                        len(c) >= len(start) + len(end))]
        elif file_expr in self.current_dir_contents_dict:
            return [file_expr]
        else:
            return []

    def do_mark(self):
        readline.set_completer(self.dir_entries_completion)
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
        if not self.current_dir_contents_list:
            self.get_dir_contents(self.current_dir, self.batchno)
            if not self.current_dir_contents_list:
                print 'failed to get directory contents for', self.current_dir
                print 'marking dirs/files regardless'
        for entry in entries_todo:
            if entry not in self.current_dir_contents_dict:
                print 'skipping %s, not in current dir listing' % entry
                print self.current_dir_contents_dict
                continue
            filetype = retention.ruleutils.entrytype_to_text(
                self.current_dir_contents_dict[entry]['type'])
            if filetype == 'link':
                print 'No need to mark', file_expr, 'links are always skipped'
                continue
            elif filetype != 'dir' and filetype != 'file':
                print 'Not a dir or regular file, no need to mark, skipping'
                continue
            status = Status.text_to_status('good')
            retention.ruleutils.do_add_rule(self.cdb, file_expr, filetype, status, self.host)
        return True

    def check_rules_path(self, rules_path):
        # sanity check on the path, let's not read/write
        # into/from anything in the world

        # fixme write this
        return True

    def do_rule(self, command):
        if command == 'A' or command == 'a':
            # fixme need different completer here I think, that
            # completes relative to self.current_dir
            readline.set_completer(None)
            path = raw_input("path or wildcard expr in rule (empty to quit): ")
            path = path.strip()
            if path == '':
                return True
            self.choices = Status.STATUSES + ['Q']
            self.choice_default = Status.text_to_status('good')
            readline.set_completer(self.choices_completion)
            while True:
                statuses_text = Status.get_statuses_prompt(", ")
                status = raw_input(statuses_text + " Q(quit)) [%s]: " %
                                   self.choice_default)
                status = status.strip()
                if status == "":
                    status = self.choice_default
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
                path = os.path.join(self.current_dir, path)
            if path[-1] == os.path.sep:
                path = path[:-1]
                filetype = retention.ruleutils.text_to_entrytype('dir')
            else:
                filetype = retention.ruleutils.text_to_entrytype('file')

            retention.ruleutils.do_add_rule(self.cdb, path, filetype, status, self.host)
            # update the ignores list since we have a new rule
            self.perhost_ignores_from_rules = {}
            self.get_perhost_ignores_from_rules([self.host])
            return True
        elif command == 'S' or command == 's':
            self.choices = ['A'] + Status.STATUSES + ['Q']
            self.choice_default = Status.text_to_status('problem')
            readline.set_completer(self.choices_completion)
            while True:
                statuses_text = Status.get_statuses_prompt(", ")
                status = raw_input("status type A(all), " + statuses_text +
                                   ", Q(quit)) [%s]: " % self.choice_default)
                status = status.strip()
                if status == "":
                    status = self.choice_default

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
                    retention.ruleutils.show_rules(self.cdb, self.host, prefix=prefix)
                    return True
                elif status[0].upper() in Status.STATUSES:
                    retention.ruleutils.show_rules(self.cdb, self.host, status[0].upper(),
                                                   prefix=prefix)
                    return True
        elif command == 'D' or command == 'd':
            if not self.current_dir_contents_list:
                self.get_dir_contents(self.current_dir, self.batchno)
            retention.ruleutils.get_rules_for_path(self.cdb, self.current_dir, self.host)
            return True
        elif command == 'C' or command == 'c':
            if not self.current_dir_contents_list:
                self.get_dir_contents(self.current_dir, self.batchno)
            retention.ruleutils.get_rules_for_entries(self.cdb, self.current_dir,
                                                      self.current_dir_contents_dict,
                                                      self.host)
            return True
        elif command == 'R' or command == 'r':
            # fixme need different completer here I think, that
            # completes relative to self.current_dir
            readline.set_completer(None)
            path = raw_input("path or wildcard expr in rule (empty to quit): ")
            path = path.strip()
            if path == '':
                return True
            elif path[0] != os.path.sep:
                path = os.path.join(self.current_dir, path)
            if path[-1] == os.path.sep:
                path = path[:-1]
            retention.ruleutils.do_remove_rule(self.cdb, path, self.host)
            # update the ignores list since we removed a rule
            self.perhost_ignores_from_rules = {}
            self.get_perhost_ignores_from_rules([self.host])
            return True
        elif command == 'I' or command == 'i':
            readline.set_completer(None)
            rules_path = raw_input("full path to rules file (empty to quit): ")
            rules_path = rules_path.strip()
            if rules_path == '':
                return True
            if not self.check_rules_path(rules_path):
                print "bad rules file path specified, aborting"
            else:
                retention.ruleutils.import_rules(self.cdb, rules_path, self.host)
            return True
        elif command == 'E' or command == 'e':
            readline.set_completer(None)
            rules_path = raw_input("full path to rules file (empty to quit): ")
            rules_path = rules_path.strip()
            if rules_path == '':
                return True
            if not self.check_rules_path(rules_path):
                print "bad rules file path specified, aborting"
            else:
                retention.ruleutils.export_rules(self.cdb, rules_path, self.host)
            return True
        elif command == 'Q' or command == 'q':
            print "quitting this level"
            return None
        else:
            CommandLine.show_help('rule')
            return True

    def do_file_contents(self):
        # fixme need a different completer here... meh
        readline.set_completer(None)
        filename = raw_input("filename (empty to quit): ")
        filename = filename.strip()
        if filename == '':
            return
        if filename[0] != os.path.sep:
            filename = os.path.join(self.current_dir, filename)
        contents = self.get_file_contents(filename)
        if contents is not None:
            print contents
        else:
            print "failed to get contents of file"

    def do_filter(self):
        self.choices = ['A', 'D', 'F', 'C', 'Q']
        self.choice_default = 'C'
        readline.set_completer(self.choices_completion)
        while True:
            filtertype = raw_input("filter A(all), D(directories only),"
                                   " F(files only),"
                                   " C(Entries checked (not ignored),"
                                   " Q(quit)) [?]: ")
            filtertype = filtertype.strip()
            if filtertype == "":
                filtertype = self.choice_default
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
                readline.set_completer(self.dir_completion)
                directory = raw_input("directory name (empty to quit): ")
                directory = directory.strip()
                if directory == '':
                    return command
                if directory[-1] == os.path.sep:
                    directory = directory[:-1]
                if (directory[0] == '/' and
                        not directory.startswith(self.current_dir +
                                                 os.path.sep)):
                    print 'New directory is not a subdirectory of',
                    print self.current_dir, "skipping"
                else:
                    self.current_dir = os.path.join(self.current_dir,
                                                    directory)
                    self.current_dir_contents_list = None
                    self.current_dir_contents_dict = None
                    self.set_prompt()
                    print 'Now at', self.current_dir
                    return True
        elif command == 'U' or command == 'u':
            if self.current_dir != self.basedir:
                self.current_dir = os.path.dirname(self.current_dir)
                self.current_dir_contents_list = None
                self.current_dir_contents_dict = None
                self.set_prompt()
                print 'Now at', self.current_dir
            else:
                print 'Already at top', self.current_dir
            return True
        elif command == 'E' or command == 'e':
            self.show_dir_contents(self.current_dir, 1)
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
                command = self.show_menu(self.current_dir, 'rule')
                continuing = self.do_command(command, 'rule', self.current_dir)
            return True
        elif command == 'M' or command == 'm':
            return self.do_mark()
        elif command == 'Q' or command == 'q' or command == '':
            print "quitting this level"
            return None
        else:
            CommandLine.show_help('examine')
            return True

    def do_top(self, command, dir_path):
        if command == 'S' or command == 's':
            continuing = True
            while continuing:
                command = self.show_menu(dir_path, 'status')
                continuing = self.do_command(command, 'status', dir_path)
            return True
        elif command == 'E' or command == 'e':
            self.show_dir_contents(self.current_dir, 1)
            continuing = True
            while continuing:
                # fixme this should let the user page through batches,
                # not use '1' every time
                command = self.show_menu(self.current_dir, 'examine')
                continuing = self.do_command(command, 'examine',
                                             self.current_dir)
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
                command = self.show_menu(self.current_dir, 'rule')
                continuing = self.do_command(command, 'rule', self.current_dir)
            return True
        elif command == 'Q' or command == 'q':
            return None
        else:
            CommandLine.show_help('top')
            return True

    def do_command(self, command, level, dir_path):
        if self.basedir is None:
            self.basedir = dir_path
        if self.current_dir is None:
            self.current_dir = dir_path

        if command is None:
            return

        if level == 'top':
            return self.do_top(command, dir_path)
        elif level == 'status':
            if command in Status.STATUSES:
                # this option is invoked on a directory so
                # type is dir every time
                retention.ruleutils.do_add_rule(self.cdb, dir_path,
                                                retention.ruleutils.text_to_entrytype('dir'),
                                                command, self.host)
                return None
            elif command == 'Q' or command == 'q':
                return None
            else:
                CommandLine.show_help(level)
                return True
        elif level == 'examine':
            return self.do_examine(command)
        elif level == 'rule':
            return self.do_rule(command)
        else:
            return None
