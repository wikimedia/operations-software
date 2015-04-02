import os
import sys
import time
import socket
import runpy
import stat
import locale

sys.path.append('/srv/audits/retention/scripts/')

import retention.utils
import retention.magic
from retention.rule import Rule
import retention.config
from retention.fileinfo import FileInfo
import retention.fileutils
import retention.ruleutils
from retention.ignores import Ignores
import retention.ignores

class LocalFilesAuditor(object):
    '''
    audit files on the local host
    in a specified set of directories
    '''
    def __init__(self, audit_type,
                 show_content=False, dirsizes=False,
                 depth=2, to_check=None, ignore_also=None,
                 timeout=60, maxfiles=None):
        '''
        audit_type:   type of audit e.g. 'logs', 'homes'
        show_content: show the first line or so from problematic files
        dirsizes:     show only directories which have too many files to
                      audit properly, don't report on files at all
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
        '''

        self.audit_type = audit_type
        self.locations = audit_type + "_locations"
        self.show_sample_content = show_content
        self.dirsizes = dirsizes
        self.depth = depth + 1  # actually count of path separators in dirname
        self.to_check = to_check

        self.filenames_to_check = None
        self.dirs_to_check = None
        self.set_up_to_check()

        self.ignore_also = ignore_also
        if self.ignore_also is not None:
            self.ignore_also = self.ignore_also.split(',')
        self.timeout = timeout

        self.ignored = {}
        self.ignores = Ignores(None)
        self.ignores.set_up_ignored()

        self.hostname = socket.getfqdn()

        retention.config.set_up_conf()
        self.cutoff = retention.config.cf['cutoff']

        self.perhost_rules_from_store = None
        self.perhost_rules_from_file = None
        self.set_up_perhost_rules()

        self.today = time.time()
        self.magic = retention.magic.magic_open(retention.magic.MAGIC_NONE)
        self.magic.load()
        self.summary = None
        self.display_from_dict = FileInfo.display_from_dict
        self.MAX_FILES = maxfiles
        self.set_up_max_files()

    def set_up_max_files(self):
        '''
        more than this many files in a subdir we won't process,
        we'll just try to name top offenders

        if we've been asked only to report dir trees that are
        too large in this manner, we can set defaults mich
        higher, since we don't stat files, open them to guess
        their filetype, etc; processing then goes much quicker
        '''

        if self.MAX_FILES is None:
            if self.dirsizes:
                self.MAX_FILES = 1000
            else:
                self.MAX_FILES = 100

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

    def set_up_perhost_rules(self):
        self.perhost_rules_from_store = runpy.run_path(
            '/srv/audits/retention/configs/%s_store.cf' % self.hostname)['rules']
        self.perhost_rules_from_file = runpy.run_path(
            '/srv/audits/retention/configs/allhosts_file.cf')['perhostcf']

        if self.perhost_rules_from_store is not None:
            self.ignores.add_perhost_rules_to_ignored(self.hostname)

        if (self.perhost_rules_from_file is not None and
                'ignored_dirs' in self.perhost_rules_from_file):
            if '/' not in self.ignores.ignored['dirs']:
                self.ignores.ignored['dirs']['/'] = []
            if self.hostname in self.perhost_rules_from_file['ignored_dirs']:
                for path in self.perhost_rules_from_file[
                        'ignored_dirs'][self.hostname]:
                    if path.startswith('/'):
                        self.ignores.ignored['dirs']['/'].append(path)
            if '*' in self.perhost_rules_from_file['ignored_dirs']:
                for path in self.perhost_rules_from_file[
                        'ignored_dirs'][self.hostname]:
                    if path.startswith('/'):
                        self.ignores.ignored['dirs']['/'].append(path)

    def normalize(self, fname):
        '''
        subclasses may want to do something different, see
        LogsAuditor for an example
        '''
        return fname

    def file_is_wanted(self, fname, basedir):
        '''
        decide if we want to audit the specific file or not
        (is it ignored, or in an ignored directory, or of a type
        we skip)
        args: fname - the abs path to the file / dir

        returns True if wanted or False if not
        '''
        fname = self.normalize(fname)

        if retention.ignores.file_is_ignored(fname, basedir, self.ignores.ignored):
            return False

        if (self.filenames_to_check is not None and
                fname not in self.filenames_to_check):
            return False

        return True

    def get_subdirs_to_do(self, dirname, dirname_depth, todo):

        locale.setlocale(locale.LC_ALL, '')
        if retention.fileutils.dir_is_ignored(dirname, self.ignores.ignored):
            return todo
        if retention.fileutils.dir_is_wrong_type(dirname):
            return todo

        if self.depth < dirname_depth:
            return todo

        if dirname_depth not in todo:
            todo[dirname_depth] = []

        if self.dirs_to_check is not None:
            if retention.fileutils.subdir_check(dirname, self.dirs_to_check):
                todo[dirname_depth].append(dirname)
        else:
            todo[dirname_depth].append(dirname)

        if self.depth == dirname_depth:
            # don't read below the depth level
            return todo

        dirs = [os.path.join(dirname, d)
                for d in os.listdir(dirname)]
        if self.dirs_to_check is not None:
            dirs = [d for d in dirs if retention.fileutils.dirtree_check(
                d, self.dirs_to_check)]

        for dname in dirs:
            todo = self.get_subdirs_to_do(dname, dirname_depth + 1, todo)
        return todo

    def get_dirs_to_do(self, dirname):
        if (self.dirs_to_check is not None and
                not retention.fileutils.dirtree_check(dirname, self.dirs_to_check)):
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
            if not retention.fileutils.dirtree_check(subdirpath, self.dirs_to_check):
                return

        if retention.fileutils.dir_is_ignored(subdirpath, self.ignores.ignored):
            return True

        count = 0

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
            expanded_dirs, wildcard_dirs = retention.ignores.expand_ignored_dirs(
                base, self.ignores.ignored)
            if self.dirs_to_check is not None:
                paths[:] = [p for p in paths
                            if retention.fileutils.dirtree_check(os.path.join(base, p),
                                                                 self.dirs_to_check)]
            paths[:] = [p for p in paths if
                        (not retention.fileutils.startswithpath(os.path.join(
                            base, p), expanded_dirs) and
                         not retention.fileutils.wildcard_matches(os.path.join(
                             base, p), wildcard_dirs, exact=False))]
            count = self.process_files_from_path(location, base, files,
                                                 count, temp_results,
                                                 checklink=False)
            if count > self.MAX_FILES:
                return

        results.extend(temp_results)

    def find_all_files(self):
        results = []
        for location in retention.config.cf[self.locations]:
            dirs_to_do = self.get_dirs_to_do(location)
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

    def warn_too_many_files(self, path=None):
        print "WARNING: too many files to audit",
        if path is not None:
            fields = path.split(os.path.sep)
            print "in directory %s" % os.path.sep.join(fields[:self.depth + 1])

    def warn_dirsize(self, path):
        fields = path.split(os.path.sep)
        print ("WARNING: directory %s has more than %d files"
               % (os.path.sep.join(fields[:self.depth + 1]), self.MAX_FILES))

    def do_local_audit(self):
        open_files = retention.fileutils.get_open_files()

        all_files = {}
        files = self.find_all_files()

        count = 0
        for (f, st) in files:
            if count < 10:
                print "got", f, st
                count += 1
            all_files[f] = FileInfo(f, self.magic, st)
            all_files[f].load_file_info(self.today, self.cutoff, open_files)

        all_files_sorted = sorted(all_files, key=lambda f: all_files[f].path)
        result = []

        if all_files:
            max_name_length = max([len(all_files[fname].path)
                                   for fname in all_files]) + 2

        for fname in all_files_sorted:
            if (not retention.fileutils.contains(all_files[fname].filetype,
                                                 retention.config.cf['ignored_types'])
                    and not all_files[fname].is_empty):
                result.append(all_files[fname].format_output(
                    self.show_sample_content, False,
                    max_name_length))
        output = "\n".join(result) + "\n"
        return output
