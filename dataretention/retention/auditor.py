import os
import sys
import time
import re
import glob
import json
import socket
import runpy
import stat
import locale
import zlib
import base64

sys.path.append('/srv/audits/retention/scripts/')

import retention.utils
import retention.magic
from retention.status import Status
from retention.saltclientplus import LocalClientPlus
from retention.rule import Rule, RuleStore
from retention.config import Config
from retention.fileinfo import FileInfo, LogInfo, LogUtils
from retention.utils import JsonHelper
from retention.runner import Runner

global_keys = [key for key, value_unused in
               sys.modules[__name__].__dict__.items()]

def get_dirs_toexamine(host_report):
    '''
    given full report output from host (list of
    json entries), return the list
    of directories with at least one possibly old file
    and the list of directories skipped due to too
    many entries
    '''
    dirs_problem = set()
    dirs_skipped = set()
    lines = host_report.split("\n")
    for json_entry in lines:
        if json_entry == "":
            continue

        if json_entry.startswith("WARNING:"):
            bad_dir = FilesAuditor.get_dirname_from_warning(json_entry)
            if bad_dir is not None:
                dirs_skipped.add(bad_dir)
                continue

        if (json_entry.startswith("WARNING:") or
                json_entry.startswith("INFO:")):
            print json_entry
            continue

        try:
            entry = json.loads(json_entry,
                               object_hook=JsonHelper.decode_dict)
        except:
            print "WARNING: failed to load json for", json_entry
            continue
        if 'empty' in entry:
            empty = FileInfo.string_to_bool(entry['empty'])
            if empty:
                continue
        if 'old' in entry:
            old = FileInfo.string_to_bool(entry['old'])
            if old is None or old:
                if os.path.dirname(entry['path']) not in dirs_problem:
                    dirs_problem.add(os.path.dirname(entry['path']))
    return sorted(list(dirs_problem)), sorted(list(dirs_skipped))


class FilesAuditor(object):
    '''
    audit files locally or across a set of remote hosts,
    in a specified set of directories
    '''
    def __init__(self, hosts_expr, audit_type, prettyprint=False,
                 show_content=False, dirsizes=False, summary_report=False,
                 depth=2, to_check=None, ignore_also=None,
                 timeout=60, maxfiles=None,
                 store_filepath=None,
                 verbose=False):
        '''
        hosts_expr:   list or grain-based or wildcard expr for hosts
                      to be audited
        audit_type:   type of audit e.g. 'logs', 'homes'
        prettyprint:  nicely format the output display
        show_content: show the first line or so from problematic files
        dirsizes:     show only directories which have too many files to
                      audit properly, don't report on files at all
        summary_report: do a summary of results instead of detailed
                        this means different thiings depending on the audit
                        type
        depth:        the auditor will give up if a directory has too any files
                      it (saves it form dying on someone's 25gb homedir).
                      this option tells it how far down the tree to go from
                      the top dir of the audit, before starting to count.
                      e.g. do we count in /home/ariel or separately in
                      /home/ariel/* or in /home/ariel/*/*, etc.
        to_check:     comma-separated list of dirs (must end in '/') and/or
                      files that will be checked; if this is None then
                      all dirs/files will be checked
        ignore_also:  comma-separated list of dirs (must end in '/') and/or
                      files that will be skipped in addition to the ones
                      in the config, rules, etc.
        timeout:      salt timeout for running remote commands
        maxfiles:     how many files in a directory tree is too many to audit
                      (at which point we warn about that and move on)
        store_filepath: full path to rule store (sqlite3 db)
        verbose:      show informative messages during processing
        '''

        global rules

        self.hosts_expr = hosts_expr
        self.audit_type = audit_type
        self.locations = audit_type + "_locations"
        self.prettyprint = prettyprint
        self.show_sample_content = show_content
        self.dirsizes = dirsizes
        self.show_summary = summary_report
        self.depth = depth + 1  # actually count of path separators in dirname
        self.to_check = to_check
        self.set_up_to_check()

        self.ignore_also = ignore_also
        if self.ignore_also is not None:
            self.ignore_also = self.ignore_also.split(',')
        self.timeout = timeout
        self.store_filepath = store_filepath
        self.verbose = verbose

        self.set_up_ignored()

        # need this for locally running jobs
        self.hostname = socket.getfqdn()

        self.cutoff = Config.cf['cutoff']

        if not retention.utils.running_locally(self.hosts_expr):
            client = LocalClientPlus()
            hosts, expr_type = Runner.get_hosts_expr_type(self.hosts_expr)
            self.expanded_hosts = client.cmd_expandminions(
                hosts, "test.ping", expr_form=expr_type)
        else:
            self.expanded_hosts = None

        self.runner = Runner(hosts_expr,
                             self.expanded_hosts,
                             self.audit_type,
                             self.generate_executor,
                             self.show_sample_content,
                             self.to_check,
                             self.timeout,
                             self.verbose)

        if 'PerHostConfig' in global_keys:
            self.perhost_rules_from_file = PerHostConfig.perhostcf
        else:
            self.perhost_rules_from_file = None
        self.perhost_raw = None
        if self.perhost_rules_from_file is None:
            if not retention.utils.running_locally(self.hosts_expr):
                if os.path.exists('/srv/audits/retention/scripts/audit_files_perhost_config.py'):
                    try:
                        self.perhost_rules_from_file = runpy.run_path(
                            '/srv/audits/retention/scripts/audit_files_perhost_config.py')['perhostcf']
                        self.perhost_raw = open(
                            '/srv/audits/retention/scripts/audit_files_perhost_config.py').read()
                    except:
                        pass

        if retention.utils.running_locally(self.hosts_expr):
            self.set_up_perhost_rules()

        if not retention.utils.running_locally(self.hosts_expr):
            self.cdb = RuleStore(self.store_filepath)
            self.cdb.store_db_init(self.expanded_hosts)
            self.set_up_and_export_rule_store()
        else:
            self.cdb = None

        self.show_ignored(Config.cf[self.locations])

        self.today = time.time()
        self.magic = retention.magic.magic_open(retention.magic.MAGIC_NONE)
        self.magic.load()
        self.summary = None
        self.display_from_dict = FileInfo.display_from_dict
        self.set_up_max_files(maxfiles)

    def set_up_max_files(self, maxfiles):
        '''
        more than this many files in a subdir we won't process,
        we'll just try to name top offenders

        if we've been asked only to report dir trees that are
        too large in this manner, we can set defaults mich
        higher, since we don't stat files, open them to guess
        their filetype, etc; processing then goes much quicker
        '''

        if maxfiles is None:
            if self.dirsizes:
                self.MAX_FILES = 1000
            else:
                self.MAX_FILES = 100
        else:
            self.MAX_FILES = maxfiles

    def set_up_and_export_rule_store(self):
        hosts = self.cdb.store_db_list_all_hosts()
        where_to_put = os.path.join(os.path.dirname(self.store_filepath),
                                    "data_retention.d")
        if not os.path.isdir(where_to_put):
            os.makedirs(where_to_put, 0755)
        for host in hosts:
            nicepath = os.path.join(where_to_put, host + ".conf")
            Rule.export_rules(self.cdb, nicepath, host)

    def set_up_to_check(self):
        '''
        turn the to_check arg into lists of dirs and files to check
        '''
        if self.to_check is not None:
            check_list = self.to_check.split(',')
            self.filenames_to_check = [fname for fname in check_list
                                       if not fname.startswith(os.sep)]
            if not len(self.filenames_to_check):
                self.filenames_to_check = None
            self.dirs_to_check = [d.rstrip(os.path.sep) for d in check_list
                                  if d.startswith(os.sep)]
        else:
            self.filenames_to_check = None
            self.dirs_to_check = None

    def set_up_perhost_rules(self):
        self.perhost_rules_from_store = runpy.run_path(
            '/srv/audits/retention/configs/%s_store.cf' % self.hostname)['rules']
        self.perhost_rules_from_file = runpy.run_path(
            '/srv/audits/retention/configs/allhosts_file.cf')['perhostcf']

        if self.perhost_rules_from_store is not None:
            self.add_perhost_rules_to_ignored()

            if self.verbose:
                print "INFO: rules received from remote: ",
                print self.perhost_rules_from_store

        if (self.perhost_rules_from_file is not None and
            'ignored_dirs' in self.perhost_rules_from_file):
            if '/' not in self.ignored['dirs']:
                self.ignored['dirs']['/'] = []
            if self.hostname in self.perhost_rules_from_file['ignored_dirs']:
                for path in self.perhost_rules_from_file[
                        'ignored_dirs'][self.hostname]:
                    if path.startswith('/'):
                        self.ignored['dirs']['/'].append(path)
            if '*' in self.perhost_rules_from_file['ignored_dirs']:
                for path in self.perhost_rules_from_file[
                        'ignored_dirs'][self.hostname]:
                    if path.startswith('/'):
                        self.ignored['dirs']['/'].append(path)

    def set_up_ignored(self):
        '''
        collect up initial list of files/dirs to skip during audit
        '''
        self.ignored = {}
        self.ignored['files'] = Config.cf['ignored_files']
        self.ignored['dirs'] = Config.cf['ignored_dirs']
        self.ignored['prefixes'] = Config.cf['ignored_prefixes']
        self.ignored['extensions'] = Config.cf['ignored_extensions']

        if self.ignore_also is not None:
            # silently skip paths that are not absolute
            for path in self.ignore_also:
                if path.startswith('/'):
                    if path.endswith('/'):
                        if '/' not in self.ignored['dirs']:
                            self.ignored['dirs']['/'] = []
                        self.ignored['dirs']['/'].append(path[:-1])
                    else:
                        if '/' not in self.ignored['files']:
                            self.ignored['files']['/'] = []
                        self.ignored['files']['/'].append(path)

    def add_perhost_rules_to_ignored(self):
        '''
        add dirs/files to be skipped during audit based
        on rules in the rule store db
        '''
        if '/' not in self.ignored['dirs']:
            self.ignored['dirs']['/'] = []
        if '/' not in self.ignored['files']:
            self.ignored['files']['/'] = []
        for host in self.perhost_rules_from_store:
            if host == self.hostname:
                for rule in self.perhost_rules_from_store[host]:
                    path = os.path.join(rule['basedir'], rule['name'])
                    if rule['status'] == 'good':
                        if Rule.entrytype_to_text(rule['type']) == 'dir':
                            if path not in self.ignored['dirs']['/']:
                                self.ignored['dirs']['/'].append(path)
                        elif Rule.entrytype_to_text(rule['type']) == 'file':
                            if path not in self.ignored['files']['/']:
                                self.ignored['files']['/'].append(path)
                        else:
                            # some other random type, don't care
                            continue
                break

    def get_perhost_rules_as_json(self):
        '''
        this reads from the data_retention.d directory files for the minions
        on which the audit will be run, converts each host's rules to json
        strings, and returns a hash of rules where keys are the hostname and
        values are the list of rules on that host
        '''
        where_to_get = os.path.join(os.path.dirname(self.store_filepath),
                                    "data_retention.d")
        if not os.path.isdir(where_to_get):
            os.mkdir(where_to_get, 0755)
        # really? or just read each file and be done with it?
        # also I would like to check the syntax cause paranoid.
        rules = {}
        self.cdb = RuleStore(self.store_filepath)
        self.cdb.store_db_init(self.expanded_hosts)
        for host in self.expanded_hosts:
            rules[host] = []
            nicepath = os.path.join(where_to_get, host + ".conf")
            if os.path.exists(nicepath):
                dir_rules = None
                try:
                    text = open(nicepath)
                    exec(text)
                except:
                    continue
                if dir_rules is not None:
                    for status in Status.status_cf:
                        if status in dir_rules:
                            for entry in dir_rules[status]:
                                if entry[0] != os.path.sep:
                                    print ("WARNING: relative path in rule,"
                                           "skipping:", entry)
                                    continue
                                if entry[-1] == os.path.sep:
                                    entry = entry[:-1]
                                    entry_type = Rule.text_to_entrytype('dir')
                                else:
                                    entry_type = Rule.text_to_entrytype('file')
                                rule = Rule.get_rule_as_json(
                                    entry, entry_type, status)
                                rules[host].append(rule)
        return rules

    def write_perhost_rules_normal_code(self, indent):
        rules = self.get_perhost_rules_as_json()

        for host in rules:
            rulescode = "rules = {}\n\n"
            rulescode += "rules['%s'] = [\n" % host
            rulescode += (indent +
                     (",\n%s" % (indent + indent)).join(rules[host]) + "\n")
            rulescode += "]\n"

            with open("/srv/salt/audits/retention/configs/%s_store.py" % host, "w+") as fp:
                fp.write(rulescode)
                fp.close()

    def write_rules_for_minion(self):
        indent = "    "
        self.write_perhost_rules_normal_code(indent)
        if self.perhost_raw is not None:
            with open("/srv/salt/audits/retention/configs/allhosts_file.py", "w+") as fp:
                fp.write(self.perhost_raw)
                fp.close()

    def generate_executor(self):
        code = ("""
def executor():
    fa = FilesAuditor('localhost', '%s', False, %s, %s,
                      False, %d, %s, %s, %d, %d, False)
    fa.audit_hosts()
""" %
                (self.audit_type,
                 self.show_sample_content,
                 self.dirsizes,
                 self.depth - 1,
                 ('"%s"' % self.to_check
                  if self.to_check is not None else "None"),
                 ('"%s"' % ",".join(self.ignore_also)
                  if self.ignore_also is not None else "None"),
                 self.timeout,
                 self.MAX_FILES))

        self.write_rules_for_minion()

        return code

    def show_ignored(self, basedirs):
        if self.verbose:
            if not retention.utils.running_locally(self.hosts_expr):
                sys.stderr.write(
                    "INFO: The below does not include per-host rules\n")
                sys.stderr.write(
                    "INFO: or rules derived from the directory status entries.\n")

            sys.stderr.write("INFO: Ignoring the following directories:\n")

            for basedir in self.ignored['dirs']:
                if basedir in basedirs or basedir == '*' or basedir == '/':
                    sys.stderr.write(
                        "INFO: " + ','.join(self.ignored['dirs'][basedir])
                        + " in " + basedir + '\n')

            sys.stderr.write("INFO: Ignoring the following files:\n")
            for basedir in self.ignored['files']:
                if basedir in basedirs or basedir == '*' or basedir == '/':
                    sys.stderr.write(
                        "INFO: " + ','.join(self.ignored['files'][basedir])
                        + " in " + basedir + '\n')

            sys.stderr.write(
                "INFO: Ignoring files starting with the following:\n")
            sys.stderr.write(
                "INFO: " + ','.join(self.ignored['prefixes']) + '\n')

            sys.stderr.write(
                "INFO: Ignoring files ending with the following:\n")
            for basedir in self.ignored['extensions']:
                if basedir in basedirs or basedir == '*':
                    sys.stderr.write("INFO: " + ','.join(
                        self.ignored['extensions'][basedir])
                        + " in " + basedir + '\n')

    @staticmethod
    def startswith(string_arg, list_arg):
        '''
        check if the string arg starts with any elt in
        the list_arg
        '''
        for elt in list_arg:
            if string_arg.startswith(elt):
                return True
        return False

    def contains(self, string_arg, list_arg):
        '''
        check if the string arg cotains any elt in
        the list_arg
        '''
        for elt in list_arg:
            if elt in string_arg:
                return True
        return False

    @staticmethod
    def endswith(string_arg, list_arg):
        '''
        check if the string arg ends with any elt in
        the list_arg
        '''
        for elt in list_arg:
            if string_arg.endswith(elt):
                return True
        return False

    @staticmethod
    def startswithpath(string_arg, list_arg):
        '''
        check if the string arg starts with any elt in
        the list_arg and the next character, if any,
        is the os dir separator
        '''

        for elt in list_arg:
            if string_arg == elt or string_arg.startswith(elt + "/"):
                return True
        return False

    @staticmethod
    def subdir_check(dirname, directories):
        '''
        check if one of the directories listed is the
        specified dirname or the dirname is somewhere in
        a subtree of one of the listed directories,
        returning True if so and fFalse otherwise
        '''

        # fixme test this
        # also see if this needs to replace dirtree_checkeverywhere or not
        for dname in directories:
            if dname == dirname or dirname.startswith(dname + "/"):
                return True
        return False

    @staticmethod
    def dirtree_check(dirname, directories):
        '''
        check if the dirname is either a directory at or above one of
        the the directories specified in the tree or vice versa, returning
        True if so and fFalse otherwise
        '''

        for dname in directories:
            if dirname == dname or dirname.startswith(dname + "/"):
                return True
            if dname.startswith(dirname + "/"):
                return True
        return False

    @staticmethod
    def expand_ignored_dirs(basedir, ignored):
        '''
        find dirs to ignore relative to the specified
        basedir, in Config entry.  Fall back to wildcard spec
        if there is not entry for the basedir.  Dirs in
        Config entry may have one * in the path, this
        will be treated as a wildcard for the purposes
        of checking directories against the entry.

        args: absolute path of basedir being crawled
              hash of ignored dirs, file, etc
        returns: list of absolute paths of dirs to ignore,
        plus separate list of abslute paths containing '*',
        also to ignore, or the empty list if there are none
        '''

        dirs = []
        wildcard_dirs = []

        to_expand = []
        if 'dirs' in ignored:
            if '*' in ignored['dirs']:
                to_expand.extend(ignored['dirs']['*'])

            if '/' in ignored['dirs']:
                to_expand.extend(ignored['dirs']['/'])

            if basedir in ignored['dirs']:
                to_expand.extend(ignored['dirs'][basedir])

            for dname in to_expand:
                if '*' in dname:
                    wildcard_dirs.append(os.path.join(basedir, dname))
                else:
                    dirs.append(os.path.join(basedir, dname))

        return dirs, wildcard_dirs

    @staticmethod
    def wildcard_matches(dirname, wildcard_dirs, exact=True):
        '''given a list of absolute paths with exactly one '*'
        in each entry, see if the passed dirname matches
        any of the list entries'''
        for dname in wildcard_dirs:
            if len(dirname) + 1 < len(dname):
                continue

            left, right = dname.split('*', 1)
            if dirname.startswith(left):
                if dirname.endswith(right):
                    return True
                elif (not exact and
                      dirname.rfind(right + "/", len(left)) != -1):
                    return True
                else:
                    continue
        return False

    def normalize(self, fname):
        '''
        subclasses may want to do something different, see
        LogsAuditor for an example
        '''
        return fname

    @staticmethod
    def file_is_ignored(fname, basedir, ignored):
        '''
        pass normalized name (abs path), basedir (location audited),
        hash of ignored files, dirs, prefixes, extensions
        get back True if the file is to be ignored and
        False otherwise
        '''

        basename = os.path.basename(fname)

        if 'prefixes' in ignored:
            if FilesAuditor.startswith(basename, ignored['prefixes']):
                return True

        if 'extensions' in ignored:
            if '*' in ignored['extensions']:
                if FilesAuditor.endswith(basename, ignored['extensions']['*']):
                    return True
            if basedir in ignored['extensions']:
                if FilesAuditor.endswith(
                        basename, ignored['extensions'][basedir]):
                    return True

        if 'files' in ignored:
            if basename in ignored['files']:
                return True
            if '*' in ignored['files']:
                if FilesAuditor.endswith(basename, ignored['files']['*']):
                    return True

            if '/' in ignored['files']:
                if fname in ignored['files']['/']:
                    return True
                if FilesAuditor.wildcard_matches(
                        fname, [w for w in ignored['files']['/'] if '*' in w]):
                    return True

            if basedir in ignored['files']:
                if FilesAuditor.endswith(basename, ignored['files'][basedir]):
                    return True
        return False

    def file_is_wanted(self, fname, basedir):
        '''
        decide if we want to audit the specific file or not
        (is it ignored, or in an ignored directory, or of a type
        we skip)
        args: fname - the abs path to the file / dir

        returns True if wanted or False if not
        '''
        fname = self.normalize(fname)

        if FilesAuditor.file_is_ignored(fname, basedir, self.ignored):
            return False

        if (self.filenames_to_check is not None and
                fname not in self.filenames_to_check):
            return False

        return True

    @staticmethod
    def dir_is_ignored(dirname, ignored):
        expanded_dirs, wildcard_dirs = FilesAuditor.expand_ignored_dirs(
            os.path.dirname(dirname), ignored)
        if dirname in expanded_dirs:
            return True
        if FilesAuditor.wildcard_matches(dirname, wildcard_dirs):
            return True
        return False

    @staticmethod
    def dir_is_wrong_type(dirname):
        try:
            dirstat = os.lstat(dirname)
        except:
            return True
        if stat.S_ISLNK(dirstat.st_mode):
            return True
        if not stat.S_ISDIR(dirstat.st_mode):
            return True
        return False

    def get_subdirs_to_do(self, dirname, dirname_depth, todo):

        locale.setlocale(locale.LC_ALL, '')
        if FilesAuditor.dir_is_ignored(dirname, self.ignored):
            return todo
        if FilesAuditor.dir_is_wrong_type(dirname):
            return todo

        if self.depth < dirname_depth:
            return todo

        if dirname_depth not in todo:
            todo[dirname_depth] = []

        if self.dirs_to_check is not None:
            if FilesAuditor.subdir_check(dirname, self.dirs_to_check):
                todo[dirname_depth].append(dirname)
        else:
            todo[dirname_depth].append(dirname)

        if self.depth == dirname_depth:
            # don't read below the depth level
            return todo

        dirs = [os.path.join(dirname, d)
                for d in os.listdir(dirname)]
        if self.dirs_to_check is not None:
            dirs = [d for d in dirs if FilesAuditor.dirtree_check(
                d, self.dirs_to_check)]

        for dname in dirs:
            todo = self.get_subdirs_to_do(dname, dirname_depth + 1, todo)
        return todo

    def get_dirs_to_do(self, dirname):
        if (self.dirs_to_check is not None and
                not FilesAuditor.dirtree_check(dirname, self.dirs_to_check)):
            if self.verbose:
                print 'WARNING: no dirs to do for', dirname
            return {}

        todo = {}
        depth_of_dirname = dirname.count(os.path.sep)
        todo = self.get_subdirs_to_do(dirname, depth_of_dirname, todo)
        return todo

    def process_files_from_path(self, location, base, files, count,
                                results, checklink=True):
        '''
        arguments:
            location: the location being checked
            base: directory containing the files to be checked
            files: files to be checked
            count: number of files in result set so far for this location
            results: the result set
        '''

        for fname, st in files:
            path = os.path.join(base, fname)
            if self.file_is_wanted(path, location):
                count += 1
                if count > self.MAX_FILES:
                    if self.dirsizes:
                        self.warn_dirsize(base)
                    else:
                        self.warn_too_many_files(base)
                    return count
                # for dirsizes option we don't collect or report files
                if not self.dirsizes:
                    results.append((path, st))
        return count

    def walk_nolinks(self, top):
        '''replaces (and is stolen from) os.walk, checks for and skips
        links, returns base, paths, files but it's guaranteed that
        files really are regular files and base/paths are not symlinks
        the files list is a list of filename, stat of that filename,
        because we have to do the stat on it anyways to ensure it's a file
        and not a dir, so the caller might as well get that info'''

        try:
            names = os.listdir(top)
        except os.error, err:
            return

        dirs, files = [], []
        for name in names:
            try:
                filestat = os.lstat(os.path.join(top, name))
            except:
                continue
            if stat.S_ISLNK(filestat.st_mode):
                continue
            if stat.S_ISDIR(filestat.st_mode):
                dirs.append(name)
            elif stat.S_ISREG(filestat.st_mode):
                files.append((name, filestat))
            else:
                continue

        yield top, dirs, files

        for name in dirs:
            new_path = os.path.join(top, name)
            for x in self.walk_nolinks(new_path):
                yield x

    def process_one_dir(self, location, subdirpath, depth, results):
        '''
        arguments:
            location: the location being checked
            subdirpath: the path to the subdirectory being checked
            depth: the depth of the directory being checked (starting at 1)
            results: the result set
        '''
        if self.dirs_to_check is not None:
            if not FilesAuditor.dirtree_check(subdirpath, self.dirs_to_check):
                return

        if FilesAuditor.dir_is_ignored(subdirpath, self.ignored):
            return True

        count = 0

        if self.verbose:
            print "INFO: collecting files in", subdirpath
        # doing a directory higher up in the tree than our depth cutoff,
        # only do the files in it, because we have the full list of dirs
        # up to our cutoff we do them one by one
        if depth < self.depth:
            filenames = os.listdir(subdirpath)
            files = []
            for fname in filenames:
                try:
                    filestat = os.stat(os.path.join(subdirpath, fname))
                except:
                    continue
                if (not stat.S_ISLNK(filestat.st_mode) and
                    stat.S_ISREG(filestat.st_mode)):
                    files.append((fname, filestat))
            self.process_files_from_path(location, subdirpath,
                                         files, count, results)
            return

        # doing a directory at our cutoff depth, walk it,
        # because anything below the depth
        # cutoff won't be in our list
        temp_results = []
        for base, paths, files in self.walk_nolinks(subdirpath):
            expanded_dirs, wildcard_dirs = FilesAuditor.expand_ignored_dirs(
                base, self.ignored)
            if self.dirs_to_check is not None:
                paths[:] = [p for p in paths
                            if FilesAuditor.dirtree_check(os.path.join(base, p),
                                                          self.dirs_to_check)]
            paths[:] = [p for p in paths if
                        (not FilesAuditor.startswithpath(os.path.join(
                            base, p), expanded_dirs) and
                         not FilesAuditor.wildcard_matches(os.path.join(
                             base, p), wildcard_dirs, exact=False))]
            count = self.process_files_from_path(location, base, files,
                                                 count, temp_results,
                                                 checklink=False)
            if count > self.MAX_FILES:
                return

        results.extend(temp_results)

    def find_all_files(self):
        results = []
        for location in Config.cf[self.locations]:
            dirs_to_do = self.get_dirs_to_do(location)
            if self.verbose:
                print "for location", location, "doing dirs", dirs_to_do
            if location.count(os.path.sep) >= self.depth + 1:
                # do the run at least once
                upper_end = location.count(os.path.sep) + 1
            else:
                upper_end = self.depth + 1
            for depth in range(location.count(os.path.sep), upper_end):
                if depth in dirs_to_do:
                    for dname in dirs_to_do[depth]:
                        self.process_one_dir(location, dname, depth, results)
        return results

    @staticmethod
    def get_open_files():
        '''
        scrounge /proc/nnn/fd and collect all open files
        '''
        open_files = set()
        dirs = os.listdir("/proc")
        for dname in dirs:
            if not re.match('^[0-9]+$', dname):
                continue
            try:
                links = os.listdir(os.path.join("/proc", dname, "fd"))
            except:
                # process may have gone away
                continue
            # must follow sym link for all of these, yuck
            files = set()
            for link in links:
                try:
                    files.add(os.readlink(os.path.join("/proc", dname,
                                                       "fd", link)))
                except:
                    continue
            open_files |= files
        return open_files

    def warn_too_many_files(self, path=None):
        print "WARNING: too many files to audit",
        if path is not None:
            fields = path.split(os.path.sep)
            print "in directory %s" % os.path.sep.join(fields[:self.depth + 1])

    def warn_dirsize(self, path):
        fields = path.split(os.path.sep)
        print ("WARNING: directory %s has more than %d files"
               % (os.path.sep.join(fields[:self.depth + 1]), self.MAX_FILES))

    @staticmethod
    def get_dirname_from_warning(warning):
        '''
        some audit output lines warn about directory trees
        having too many files to audit; grab the dirname
        out of such a line and return it
        '''
        start = "WARNING: directory "
        if warning.startswith(start):
            # WARNING: directory %s has more than %d files
            rindex = warning.rfind(" has more than")
            if not rindex:
                return None
            else:
                return warning[len(start):rindex]

        start = "WARNING: too many files to audit in directory "
        if warning.startswith(start):
            return warning[len(start):]

        return None

    def do_local_audit(self):
        open_files = FilesAuditor.get_open_files()

        all_files = {}
        files = self.find_all_files()

        for (f, st) in files:
            all_files[f] = FileInfo(f, self.magic, st)
            all_files[f].load_file_info(self.today, self.cutoff, open_files)

        all_files_sorted = sorted(all_files, key=lambda f: all_files[f].path)
        result = []

        if all_files:
            max_name_length = max([len(all_files[fname].path)
                                   for fname in all_files]) + 2

        for fname in all_files_sorted:
            if (not self.contains(all_files[fname].filetype,
                                  Config.cf['ignored_types'])
                    and not all_files[fname].is_empty):
                result.append(all_files[fname].format_output(
                    self.show_sample_content,
                    False if self.show_summary else self.prettyprint,
                    max_name_length))
        output = "\n".join(result) + "\n"
        if self.show_summary:
            self.display_summary({self.hosts_expr: output})
        else:
            print output
        return output

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
                'binary': {'old': 0, 'maybe_old': 0, 'nonroot': 0},
                'text': {'old': 0, 'maybe_old': 0, 'nonroot': 0}
            }
        if item['binary'] is True:
            group = 'binary'
        else:
            group = 'text'

        if item['old'] == 'T':
            summary[dirname][group]['old'] += 1
        elif item['old'] == '-':
            summary[dirname][group]['maybe_old'] += 1
        if item['owner'] != 0:
            summary[dirname][group]['nonroot'] += 1
        return summary

    def display_host_summary(self):
        if self.summary is not None:
            paths = sorted(self.summary.keys())
            for path in paths:
                for group in self.summary[path]:
                    if (self.summary[path][group]['old'] > 0 or
                            self.summary[path][group]['maybe_old'] > 0 or
                            self.summary[path][group]['nonroot'] > 0):
                        print ("in directory %s, (%s), %d old,"
                               " %d maybe old, %d with non root owner"
                               % (path, group, self.summary[path][group]['old'],
                                  self.summary[path][group]['maybe_old'],
                                  self.summary[path][group]['nonroot']))

    def display_summary(self, result):
        for host in result:
            self.summary = {}
            print "host:", host

            if result[host]:
                self.summary = {}
                try:
                    lines = result[host].split('\n')
                    for line in lines:
                        if line == '':
                            continue
                        if (line.startswith("WARNING:") or
                                line.startswith("INFO:")):
                            print line
                            continue
                        else:
                            try:
                                item = json.loads(
                                    line, object_hook=JsonHelper.decode_dict)
                                if item['empty'] is not True:
                                    self.add_stats(item, self.summary)
                            except:
                                print "WARNING: failed to json load from host",
                                print host, "this line:", line
                    self.display_host_summary()
                except:
                    print "WARNING: failed to process output from host"
            else:
                if self.verbose:
                    print "WARNING: no output from host", host

    def display_remote_host(self, result):
        try:
            lines = result.split('\n')
            files = []
            for line in lines:
                if line == "":
                    continue
                elif line.startswith("WARNING:") or line.startswith("INFO:"):
                    print line
                else:
                    files.append(json.loads(line, object_hook=JsonHelper.decode_dict))

            if files == []:
                return
            path_justify = max([len(finfo['path']) for finfo in files]) + 2
            for finfo in files:
                self.display_from_dict(finfo, self.show_sample_content, path_justify)
        except:
            print "WARNING: failed to load json from host"

    def audit_hosts(self):
        if retention.utils.running_locally(self.hosts_expr):
            result = self.do_local_audit()
        else:
            result = self.runner.run_remotely()
            if result is None:
                print "WARNING: failed to get output from audit script on any host"
            elif self.show_summary:
                self.display_summary(result)
            else:
                for host in result:
                    print "host:", host
                    if result[host]:
                        self.display_remote_host(result[host])
                    else:
                        if self.verbose:
                            print "no output from host", host
            # add some results to rule store
            self.update_status_rules_from_report(result)
        return result, self.ignored

    def update_status_rules_from_report(self, report):
        hostlist = report.keys()
        for host in hostlist:
            try:
                problem_rules = Rule.get_rules(self.cdb, host, Status.text_to_status('problem'))
            except:
                print 'WARNING: problem retrieving problem rules for host', host
                problem_rules = None
            if problem_rules is not None:
                existing_problems = [rule['path'] for rule in problem_rules]
            else:
                existing_problems = []

            dirs_problem, dirs_skipped = get_dirs_toexamine(report[host])
            if dirs_problem is not None:
                dirs_problem = list(set(dirs_problem))
                for dirname in dirs_problem:
                    Rule.do_add_rule(self.cdb, dirname,
                                     Rule.text_to_entrytype('dir'),
                                     Status.text_to_status('problem'), host)

            if dirs_skipped is not None:
                dirs_skipped = list(set(dirs_skipped))
                for dirname in dirs_skipped:
                    if dirname in dirs_problem or dirname in existing_problems:
                        # problem report overrides 'too many to audit'
                        continue
                    Rule.do_add_rule(self.cdb, dirname,
                                     Rule.text_to_entrytype('dir'),
                                     Status.text_to_status('unreviewed'), host)


class LogsAuditor(FilesAuditor):
    def __init__(self, hosts_expr, audit_type, prettyprint=False,
                 oldest=False,
                 show_content=False, show_system_logs=False,
                 dirsizes=False, summary_report=False, depth=2,
                 to_check=None, ignore_also=None,
                 timeout=60, maxfiles=None, store_filepath=None,
                 verbose=False):
        super(LogsAuditor, self).__init__(hosts_expr, audit_type, prettyprint,
                                          show_content, dirsizes,
                                          summary_report, depth,
                                          to_check, ignore_also, timeout,
                                          maxfiles, store_filepath, verbose)
        self.oldest_only = oldest
        self.show_system_logs = show_system_logs
        if self.show_system_logs:
            self.ignored['files'].pop("/var/log")
        self.display_from_dict = LogInfo.display_from_dict

    def generate_executor(self):
        code = ("""
def executor():
    la = LogsAuditor('localhost', '%s', False, %s, %s, %s, %s,
                     False, %d, %s, %s, %d, %d, False)
    la.audit_hosts()
""" %
                (self.audit_type,
                 self.oldest_only,
                 self.show_sample_content,
                 self.dirsizes,
                 self.show_system_logs,
                 self.depth - 1,
                 ('"%s"' % self.to_check
                  if self.to_check is not None else "None"),
                 ('"%s"' % ",".join(self.ignore_also)
                  if self.ignore_also is not None else "None"),
                 self.timeout, self.MAX_FILES))

        self.write_rules_for_minion()

        return code

    @staticmethod
    def get_rotated_freq(rotated):
        '''
        turn the value you get out of logrotate
        conf files for 'rotated' into a one
        char string suitable for our reports
        '''
        if rotated == 'weekly':
            freq = 'w'
        elif rotated == 'daily':
            freq = 'd'
        elif rotated == 'monthly':
            freq = 'm'
        elif rotated == 'yearly':
            freq = 'y'
        else:
            freq = None
        return freq

    @staticmethod
    def get_rotated_keep(line):
        fields = line.split()
        if len(fields) == 2:
            keep = fields[1]
        else:
            keep = None
        return keep

    @staticmethod
    def parse_logrotate_contents(contents,
                                 default_freq='-', default_keep='-'):
        lines = contents.split('\n')
        state = 'want_lbracket'
        logs = {}
        freq = default_freq
        keep = default_keep
        notifempty = '-'
        log_group = []
        for line in lines:
            if line.startswith('#'):
                continue
            line = line.strip()
            if not line:
                continue
            if state == 'want_lbracket':
                if line.endswith('{'):
                    state = 'want_rbracket'
                    line = line[:-1].strip()
                    if not line:
                        continue
                if not line.startswith('/'):
                    # probably a directive or a blank line
                    continue
                if '*' in line:
                    log_group.extend(glob.glob(
                        os.path.join(Config.cf['rotate_basedir'], line)))
                else:
                    log_group.append(line)
            elif state == 'want_rbracket':
                tmp_freq = LogsAuditor.get_rotated_freq(line)
                if tmp_freq:
                    freq = tmp_freq
                    continue
                elif line.startswith('rotate'):
                    tmp_keep = LogsAuditor.get_rotated_keep(line)
                    if tmp_keep:
                        keep = tmp_keep
                elif line == 'notifempty':
                    notifempty = 'T'
                elif line.endswith('}'):
                    state = 'want_lbracket'
                    for log in log_group:
                        logs[log] = [freq, keep, notifempty]
                    freq = default_freq
                    keep = default_keep
                    notifempty = '-'
                    log_group = []
        return logs

    def get_logrotate_defaults(self):
        contents = open(Config.cf['rotate_mainconf']).read()
        lines = contents.split('\n')
        skip = False
        freq = '-'
        keep = '-'
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.endswith('{'):
                skip = True
                continue
            elif line.endswith('}'):
                skip = False
                continue
            elif skip:
                continue
            tmp_freq = LogsAuditor.get_rotated_freq(line)
            if tmp_freq:
                freq = tmp_freq
                continue
            elif line.startswith('rotate'):
                tmp_keep = LogsAuditor.get_rotated_keep(line)
                if tmp_keep:
                    keep = tmp_keep

        return freq, keep

    def find_rotated_logs(self):
        '''
        gather all names of log files from logrotate
        config files
        '''
        rotated_logs = {}
        default_freq, default_keep = self.get_logrotate_defaults()
        rotated_logs.update(LogsAuditor.parse_logrotate_contents(
            open(Config.cf['rotate_mainconf']).read(),
            default_freq, default_keep))
        for fname in os.listdir(Config.cf['rotate_basedir']):
            pathname = os.path.join(Config.cf['rotate_basedir'], fname)
            if os.path.isfile(pathname):
                rotated_logs.update(LogsAuditor.parse_logrotate_contents(
                    open(pathname).read(), default_freq, default_keep))
        return rotated_logs

    def check_mysqlconf(self):
        '''
        check how long mysql logs are kept around
        '''
        # note that I also see my.cnf.s3 and we don't check those (yet)
        output = ''
        for filename in Config.cf['mysqlconf']:
            found = False
            try:
                contents = open(filename).read()
            except:
                # file or directory probably doesn't exist
                continue
            lines = contents.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('datadir'):
                    fields = line.split('=',1)
                    fields = [field.strip() for field in fields]
                    if fields[0] != 'datadir':
                        continue
                    if not fields[1].startswith('/'):
                        continue
                    datadir = fields[1]
                    # strip trailing slash if needed
                    if len(datadir) > 1 and datadir.endswith('/'):
                        datadir = datadir[:-1]
                    # we can skip all bin logs, relay logs, and pid files in this
                    # directory. anything else should get looked at.
                    if '.' in self.hostname:
                        hostname = self.hostname.split('.')[0]
                    else:
                        hostname = self.hostname
                    ignore_these = [hostname + '-bin', hostname + '-relay-bin',
                                    hostname + '.pid', hostname + '-bin.index',
                                    hostname + '-relay-bin.index']

                    # add these files to ignore list; a one line report on
                    # mysql log expiry configuration is sufficient
                    if datadir not in self.ignored['files']:
                        self.ignored['files'][datadir] = ignore_these
                    else:
                        self.ignored['files'][datadir].extend(ignore_these)
                    # skip the subdirectories in here, they will be full of mysql dbs
                    if datadir not in self.ignored['dirs']:
                        self.ignored['files'][datadir] = ['*']
                    else:
                        self.ignored['files'][datadir].append('*')

                if line.startswith('expire_logs_days'):
                    fields = line.split('=',1)
                    fields = [field.strip() for field in fields]
                    if fields[0] != 'expire_logs_days':
                        continue
                    if not fields[1].isdigit():
                        continue
                    found = True
                    if int(fields[1]) > Config.cf['cutoff']/86400:
                        if output:
                            output = output + '\n'
                        output = output + ('WARNING: some mysql logs expired after %s days in %s'
                                           % (fields[1], filename))
            if not found:
                if output:
                    output = output + '\n'
                output = output + 'WARNING: some mysql logs never expired in ' + filename
        return(output)

    def do_local_audit(self):
        '''
        note that no summary report is done for a  single host,
        for logs we summarize across hosts
        '''
        mysql_issues = self.check_mysqlconf()
        result = []
        if mysql_issues:
            result.append(mysql_issues)

        open_files = FilesAuditor.get_open_files()
        rotated = self.find_rotated_logs()

        all_files = {}
        files = self.find_all_files()

        for (f, st) in files:
            all_files[f] = LogInfo(f, self.magic, st)
            all_files[f].load_file_info(self.today, self.cutoff,
                                        open_files, rotated)

        all_files_sorted = sorted(all_files,
                                  key=lambda f: all_files[f].path)
        last_log_normalized = ''
        last_log = ''
        age = 0

        if all_files:
            max_name_length = max([len(all_files[fname].path)
                                   for fname in all_files]) + 2
            max_norm_length = max([len(all_files[fname].normalized)
                                   for fname in all_files]) + 2

        for fname in all_files_sorted:
            if self.contains(all_files[fname].filetype,
                             Config.cf['ignored_types']):
                continue

            if (self.oldest_only and
                all_files[fname].normalized == last_log_normalized):
                # still doing the same group of logs
                if all_files[fname].age <= age:
                    continue
                else:
                    age = all_files[fname].age
                    last_log = fname
            else:
                if last_log:
                    result.append(all_files[last_log].format_output(
                        self.show_sample_content,
                        self.prettyprint, max_name_length, max_norm_length))

                # starting new set of logs (maybe first set)
                last_log_normalized = all_files[fname].normalized
                last_log = fname
                age = all_files[fname].age

        if last_log:
            result.append(all_files[last_log].format_output(
                self.show_sample_content,
                self.prettyprint, max_name_length, max_norm_length))
        output = "\n".join(result) + "\n"
        print output
        return output

    def display_summary(self, audit_results):
        logs = {}
        hosts_count = 0
        all_hosts = audit_results.keys()
        hosts_count = len(all_hosts)

        for host in all_hosts:
            output = None
            if audit_results[host]:
                try:
                    lines = audit_results[host].split('\n')
                    output = []
                    for line in lines:
                        if line == "":
                            continue
                        elif (line.startswith("WARNING:") or
                              line.startswith("INFO:")):
                            print 'host:', host
                            print line
                            continue
                        output.append(json.loads(
                            line, object_hook=JsonHelper.decode_dict))
                except:
                    if output is not None:
                        print output
                    else:
                        print audit_results[host]
                    print "WARNING: failed to load json from host", host
                    continue
            if output is None:
                continue
            for item in output:
                log_name = item['normalized']
                if not item['normalized'] in logs:
                    logs[log_name] = {}
                    logs[log_name]['old'] = set()
                    logs[log_name]['maybe_old'] = set()
                    logs[log_name]['unrot'] = set()
                    logs[log_name]['notifempty'] = set()
                if item['old'] == 'T':
                    logs[log_name]['old'].add(host)
                elif item['old'] == '-':
                    logs[log_name]['maybe_old'].add(host)
                if item['rotated'].startswith('F'):
                    logs[log_name]['unrot'].add(host)
                if item['notifempty'] == 'T':
                    logs[log_name]['notifempty'].add(host)
        sorted_lognames = sorted(logs.keys())
        for logname in sorted_lognames:
            old_count = len(logs[logname]['old'])
            if not old_count:
                maybe_old_count = len(logs[logname]['maybe_old'])
            else:
                maybe_old_count = 0  # we don't care about possibles now
            unrot_count = len(logs[logname]['unrot'])
            notifempty_count = len(logs[logname]['notifempty'])
            LogsAuditor.display_variance_info(old_count, hosts_count,
                                              logs[logname]['old'],
                                              'old', logname)
            LogsAuditor.display_variance_info(maybe_old_count, hosts_count,
                                              logs[logname]['maybe_old'],
                                              'maybe old', logname)
            LogsAuditor.display_variance_info(unrot_count, hosts_count,
                                              logs[logname]['unrot'],
                                              'unrotated', logname)
            LogsAuditor.display_variance_info(notifempty_count, hosts_count,
                                              logs[logname]['notifempty'],
                                              'notifempty', logname)

    @staticmethod
    def display_variance_info(stat_count, hosts_count,
                              host_list, stat_name, logname):
        '''
        assuming most stats are going to be the same across
        a group of hosts, try to show just the variances
        from the norm
        '''
        if stat_count == 0:
            return

        percentage = stat_count * 100 / float(hosts_count)

        if stat_count == 1:
            output_line = ("1 host has %s as %s" %
                           (logname, stat_name))
        else:
            output_line = ("%s (%.2f%%) hosts have %s as %s" %
                           (stat_count, percentage,
                            logname, stat_name))

        if percentage < .20 or stat_count < 6:
            output_line += ': ' + ','.join(host_list)

        print output_line

    def normalize(self, fname):
        return LogUtils.normalize(fname)

    def display_remote_host(self, result):
        '''
        given the (json) output from the salt run on the remote
        host, format it nicely and display it
        '''
        try:
            lines = result.split('\n')
            files = []
            for line in lines:
                if line == "":
                    continue
                elif line.startswith("WARNING:") or line.startswith("INFO:"):
                    print line
                else:
                    files.append(json.loads(
                        line, object_hook=JsonHelper.decode_dict))

            if files == []:
                return
            path_justify = max([len(finfo['path']) for finfo in files]) + 2
            norm_justify = max([len(finfo['normalized']) for finfo in files]) + 2
            for finfo in files:
                self.display_from_dict(finfo, self.show_sample_content,
                                       path_justify, norm_justify)
        except:
            print "WARNING: failed to load json from host:", result


class HomesAuditor(FilesAuditor):
    '''
    auditing of home directories on a set of hosts

    users may have a local '.data_retention' file in their
    home directories with a list, on entry per line, of files
    or directories (dirs must end in '/') to skip during the audit
    '''

    def __init__(self, hosts_expr, audit_type, prettyprint=False,
                 show_content=False, dirsizes=False, summary_report=False,
                 depth=2, to_check=None, ignore_also=None, timeout=60,
                 maxfiles=None, store_filepath=None, verbose=False):
        '''
        see FilesAuditor for the arguments to the constructor
        '''
        super(HomesAuditor, self).__init__(hosts_expr, audit_type, prettyprint,
                                           show_content, dirsizes,
                                           summary_report, depth,
                                           to_check, ignore_also, timeout,
                                           maxfiles, store_filepath, verbose)
        self.homes_owners = {}

        local_ignores = HomesAuditor.get_local_ignores(self.locations)
        local_ignored_dirs, local_ignored_files = HomesAuditor.process_local_ignores(
            local_ignores, self.ignored)
        self.show_local_ignores(local_ignored_dirs, local_ignored_files)

    @staticmethod
    def process_local_ignores(local_ignores, ignored):
        '''
        files or dirs listed in data retention conf in homedir
        are considered 'good' and added to ignore list

        non-absolute paths will be taken as relative to the
        home dir of the data retention config they were
        read from
        '''

        local_ignored_dirs = []
        local_ignored_files = []
        for basedir in local_ignores:
            for path in local_ignores[basedir]:
                if not path.startswith('/'):
                    path = os.path.join(basedir, path)

                if path.endswith('/'):
                    if 'dirs' not in ignored:
                        ignored['dirs'] = {}
                    if '/' not in ignored['dirs']:
                        ignored['dirs']['/'] = []

                    ignored['dirs']['/'].append(path[:-1])
                    local_ignored_dirs.append(path[:-1])
                else:
                    if 'files' not in ignored:
                        ignored['files'] = {}
                    if '/' not in ignored['files']:
                        ignored['files']['/'] = []

                    ignored['files']['/'].append(path)
                    local_ignored_files.append(path)
        return local_ignored_dirs, local_ignored_files

    def show_local_ignores(self, dirs, files):
        '''
        display a list of files and directories being ignored
        during the audit; pass these lists in as arguments
        '''
        if self.verbose:
            if len(dirs):
                sys.stderr.write("INFO: Ignoring the following directories:\n")
                sys.stderr.write(", ".join(dirs) + "\n")

            if len(files):
                sys.stderr.write("INFO: Ignoring the following files:\n")
                sys.stderr.write(", ".join(files) + "\n")

    @staticmethod
    def get_home_dirs(locations):
        '''
        get a list of home directories where the root location(s) for home are
        specified in the Config class (see 'home_locations'), by reading
        these root location dirs and grabbing all subdirectory names from them
        '''
        home_dirs = []

        for location in Config.cf[locations]:
            if not os.path.isdir(location):
                continue
            home_dirs.extend([os.path.join(location, d)
                              for d in os.listdir(location)
                              if os.path.isdir(os.path.join(location, d))])
        return home_dirs

    @staticmethod
    def get_local_ignores(locations):
        '''
        read a list of absolute paths from /home/blah/.data_retention
        for all blah.  Dirs are specified by op sep at the end ('/')
        and files without.
        '''
        local_ignores = {}
        home_dirs = HomesAuditor.get_home_dirs(locations)
        for hdir in home_dirs:
            local_ignores[hdir] = []
            if os.path.exists(os.path.join(hdir, ".data_retention")):
                try:
                    filep = open(os.path.join(hdir, ".data_retention"))
                    entries = filep.read().split("\n")
                    filep.close()
                except:
                    pass
                entries = filter(None, [e.strip() for e in entries])
                # fixme should sanity check these? ???
                # what happens if people put wildcards in the wrong
                # component, or put utter garbage in there, or...?
                local_ignores[hdir].extend(entries)

        return local_ignores

    def generate_executor(self):
        code = ("""
def executor():
    ha = HomesAuditor('localhost', '%s', False, %s, %s, False,
                      %d, %s, %s, %d, %d, False)
    ha.audit_hosts()
""" %
                (self.audit_type,
                 self.show_sample_content,
                 self.dirsizes,
                 self.depth - 1,
                 ('"%s"' % self.to_check
                  if self.to_check is not None else "None"),
                 ('"%s"' % ",".join(self.ignore_also)
                  if self.ignore_also is not None else "None"),
                 self.timeout,
                 self.MAX_FILES))

        self.write_rules_for_minion()

        return code

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

        empty, home, user, rest = item['path'].split(os.path.sep, 3)
        home_dir = os.path.join(os.path.sep, home, user)
        if home_dir not in self.homes_owners:
            try:
                dirstat = os.stat(home_dir)
            except:
                return
            self.homes_owners[home_dir] = str(dirstat.st_uid)

        if item['owner'] != self.homes_owners[home_dir]:
            summary[dirname][group]['odd_owner'] += 1


