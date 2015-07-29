import os
import time
import json

import clouseau.retention.magic
from clouseau.retention.status import Status
from clouseau.retention.saltclientplus import LocalClientPlus
from clouseau.retention.rule import RuleStore
import clouseau.retention.config
from clouseau.retention.fileinfo import FileInfo
from clouseau.retention.utils import JsonHelper
from retention.runner import Runner
import clouseau.retention.ruleutils


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
            bad_dir = RemoteFilesAuditor.get_dirname_from_warning(json_entry)
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


class RemoteFilesAuditor(object):
    '''
    audit files across a set of remote hosts,
    in a specified set of directories
    '''
    def __init__(self, hosts_expr, audit_type,
                 confdir=None,
                 prettyprint=False,
                 show_content=False, dirsizes=False, summary_report=False,
                 depth=2, to_check=None, ignore_also=None,
                 timeout=60, maxfiles=None,
                 store_filepath=None,
                 verbose=False):
        '''
        hosts_expr:   list or grain-based or wildcard expr for hosts
                      to be audited
        audit_type:   type of audit e.g. 'logs', 'homes'
        confdir:      directory where the yaml config files are stored
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

        self.hosts_expr = hosts_expr
        self.audit_type = audit_type
        self.confdir = confdir
        self.locations = audit_type + "_locations"
        self.prettyprint = prettyprint
        self.show_sample_content = show_content
        self.dirsizes = dirsizes
        self.show_summary = summary_report
        self.depth = depth + 1  # actually count of path separators in dirname
        self.to_check = to_check

        self.ignore_also = ignore_also
        self.timeout = timeout
        self.store_filepath = store_filepath
        self.verbose = verbose

        clouseau.retention.config.set_up_conf(confdir)
        self.cutoff = clouseau.retention.config.conf['cutoff']

        client = LocalClientPlus()
        hosts, expr_type = Runner.get_hosts_expr_type(self.hosts_expr)
        self.expanded_hosts = client.cmd_expandminions(
            hosts, "test.ping", expr_form=expr_type)

        self.MAX_FILES = maxfiles
        self.set_up_max_files(maxfiles)

        self.cdb = RuleStore(self.store_filepath)
        self.cdb.store_db_init(self.expanded_hosts)
        self.set_up_and_export_rule_store()

        self.today = time.time()
        self.magic = clouseau.retention.magic.magic_open(clouseau.retention.magic.MAGIC_NONE)
        self.magic.load()
        self.summary = None
        self.display_from_dict = FileInfo.display_from_dict
        self.runner = None

    def get_audit_args(self):
        audit_args = [self.confdir,
                      self.show_sample_content,
                      self.dirsizes,
                      self.depth - 1,
                      self.to_check,
                      self.ignore_also,
                      self.MAX_FILES]
        return audit_args

    def set_up_runner(self):

        self.runner = Runner(self.confdir,
                             self.store_filepath,
                             self.hosts_expr,
                             self.expanded_hosts,
                             self.audit_type,
                             self.get_audit_args(),
                             self.show_sample_content,
                             self.to_check,
                             self.timeout,
                             self.verbose)

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
        destdir = os.path.join(os.path.dirname(self.store_filepath),
                               "data_retention.d")
        if not os.path.isdir(destdir):
            os.makedirs(destdir, 0755)
        for host in hosts:
            all_destpath = os.path.join(destdir, host + "_store.yaml")
            clouseau.retention.ruleutils.export_rules(self.cdb, all_destpath, host)
            good_destpath = os.path.join(destdir, host + "_store_good.yaml")
            clouseau.retention.ruleutils.export_rules(self.cdb, good_destpath, host,
                                                      Status.text_to_status('good'))

    def normalize(self, fname):
        '''
        subclasses may want to do something different, see
        LogsAuditor for an example
        '''
        return fname

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
        self.set_up_runner()
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
        return result

    def update_status_rules_from_report(self, report):
        hostlist = report.keys()
        for host in hostlist:
            try:
                problem_rules = clouseau.retention.ruleutils.get_rules(self.cdb, host, Status.text_to_status('problem'))
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
                    clouseau.retention.ruleutils.do_add_rule(self.cdb, dirname,
                                                             clouseau.retention.ruleutils.text_to_entrytype('dir'),
                                                             Status.text_to_status('problem'), host)

            if dirs_skipped is not None:
                dirs_skipped = list(set(dirs_skipped))
                for dirname in dirs_skipped:
                    if dirname in dirs_problem or dirname in existing_problems:
                        # problem report overrides 'too many to audit'
                        continue
                    clouseau.retention.ruleutils.do_add_rule(self.cdb, dirname,
                                                             clouseau.retention.ruleutils.text_to_entrytype('dir'),
                                                             Status.text_to_status('unreviewed'), host)
