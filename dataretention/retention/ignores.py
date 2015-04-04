import os
import sys
import runpy
import salt.client
import salt.utils.yamlloader

from retention.status import Status
import retention.utils
import retention.fileutils
import retention.ruleutils
import retention.config

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

def dir_is_ignored(dirname, ignored):
    expanded_dirs, wildcard_dirs = expand_ignored_dirs(
        os.path.dirname(dirname), ignored)
    if dirname in expanded_dirs:
        return True
    if retention.fileutils.wildcard_matches(dirname, wildcard_dirs):
        return True
    return False

def file_is_ignored(fname, basedir, ignored):
    '''
    pass normalized name (abs path), basedir (location audited),
    hash of ignored files, dirs, prefixes, extensions
    get back True if the file is to be ignored and
    False otherwise
    '''

    basename = os.path.basename(fname)

    if 'prefixes' in ignored:
        if retention.fileutils.startswith(basename, ignored['prefixes']):
            return True

    if 'extensions' in ignored:
        if '*' in ignored['extensions']:
            if retention.fileutils.endswith(basename, ignored['extensions']['*']):
                return True
        if basedir in ignored['extensions']:
            if retention.fileutils.endswith(
                    basename, ignored['extensions'][basedir]):
                return True

    if 'files' in ignored:
        if basename in ignored['files']:
            return True
        if '*' in ignored['files']:
            if retention.fileutils.endswith(basename, ignored['files']['*']):
                return True

        if '/' in ignored['files']:
            if fname in ignored['files']['/']:
                return True
            if retention.fileutils.wildcard_matches(
                    fname, [w for w in ignored['files']['/'] if '*' in w]):
                return True

        if basedir in ignored['files']:
            if retention.fileutils.endswith(basename, ignored['files'][basedir]):
                return True
    return False

def get_home_dirs(locations):
    '''
    get a list of home directories where the root location(s) for home are
    specified in the Config class (see 'home_locations'), by reading
    these root location dirs and grabbing all subdirectory names from them
    '''
    retention.config.set_up_conf()
    home_dirs = []

#    filep = open('/home/ariel/src/wmf/git-ops-software/software/dataretention/retention/junk', 'w+')
#    filep.write('INFO: ' + ','.join(dir('retention.config')))
#    filep.close()
#    print 'INFO:', dir('retention.config')
    for location in retention.config.cf[locations]:
        if not os.path.isdir(location):
            continue
        home_dirs.extend([os.path.join(location, d)
                          for d in os.listdir(location)
                          if os.path.isdir(os.path.join(location, d))])
    return home_dirs

def get_local_ignores(locations):
    '''
    read a list of absolute paths from /home/blah/.data_retention
    for all blah.  Dirs are specified by op sep at the end ('/')
    and files without.
    '''
    local_ignores = {}
    home_dirs = get_home_dirs(locations)
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


class Ignores(object):
    '''
    collection of files and directories ignored by the audit
    on a given host
    '''

    def __init__(self, cdb):
        self.cdb = cdb
        self.perhost_rules_from_file = None
        if cdb is not None:
            self.hosts = self.cdb.store_db_list_all_hosts()
        else:
            self.hosts = None

        self.perhost_ignores = {}
        self.perhost_ignores_from_rules = {}
        self.perhost_rules_from_store = {}
        self.get_perhost_cf_from_file()
        self.ignored = {}

    def set_up_ignored(self, confdir, ignore_also=None):
        '''
        collect up initial list of files/dirs to skip during audit
        '''

        self.ignored['files'] = {}
        self.ignored['dirs'] = {}
        self.ignored['prefixes'] = {}
        self.ignored['extensions'] = {}

        if confdir is not None:
            configfile = os.path.join(confdir, 'ignored.yaml')
            if os.path.exists(configfile):
                try:
                    contents = open(configfile).read()
                    ign = salt.utils.yamlloader.load(contents, Loader=salt.utils.yamlloader.SaltYamlSafeLoader)
                    if 'ignored_files' in ign:
                        self.ignored['files'] = ign['ignored_files']
                    if 'ignored_dirs' in ign:
                        self.ignored['dirs'] = ign['ignored_dirs']
                    if 'ignored_prefixes' in ign:
                        self.ignored['prefixes'] = ign['ignored_prefixes']
                    if 'ignored_extensions' in ign:
                        self.ignored['extensions'] = ign['ignored_extensions']
                except:
                    pass

        if ignore_also is not None:
            # silently skip paths that are not absolute
            for path in ignore_also:
                if path.startswith('/'):
                    if path.endswith('/'):
                        if '/' not in self.ignored['dirs']:
                            self.ignored['dirs']['/'] = []
                        self.ignored['dirs']['/'].append(path[:-1])
                    else:
                        if '/' not in self.ignored['files']:
                            self.ignored['files']['/'] = []
                        self.ignored['files']['/'].append(path)

    def get_perhost_from_rules(self, hosts=None):
        if hosts == None:
            hosts = self.hosts
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

    def get_perhost_cf_from_file(self):
        if os.path.exists('audit_files_perhost_config.py'):
            try:
                self.perhost_rules_from_file = runpy.run_path(
                    'audit_files_perhost_config.py')['perhostcf']
            except:
                self.perhost_rules_from_file = None

        if self.perhost_rules_from_file is None:
            return

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

    def add_perhost_rules_to_ignored(self, host):
        '''
        add dirs/files to be skipped during audit based
        on rules in the rule store db
        '''
        if '/' not in self.ignored['dirs']:
            self.ignored['dirs']['/'] = []
        if '/' not in self.ignored['files']:
            self.ignored['files']['/'] = []
        if host not in self.perhost_rules_from_store:
            return

        for rule in self.perhost_rules_from_store[host]:
            path = os.path.join(rule['basedir'], rule['name'])
            if rule['status'] == 'good':
                if retention.ruleutils.entrytype_to_text(rule['type']) == 'dir':
                    if path not in self.ignored['dirs']['/']:
                        self.ignored['dirs']['/'].append(path)
                elif retention.ruleutils.entrytype_to_text(rule['type']) == 'file':
                    if path not in self.ignored['files']['/']:
                        self.ignored['files']['/'].append(path)
                else:
                    # some other random type, don't care
                    continue

    def show_ignored(self, basedirs):
        sys.stderr.write(
            "INFO: The below does not include per-host rules\n")
        sys.stderr.write(
            "INFO: or rules derived from the directory status entries.\n")

        if 'dirs' in self.ignored:
            sys.stderr.write("INFO: Ignoring the following directories:\n")
            for basedir in self.ignored['dirs']:
                if basedir in basedirs or basedir == '*' or basedir == '/':
                    sys.stderr.write(
                        "INFO: " + ','.join(self.ignored['dirs'][basedir])
                        + " in " + basedir + '\n')

        if 'files' in self.ignored:
            sys.stderr.write("INFO: Ignoring the following files:\n")
            for basedir in self.ignored['files']:
                if basedir in basedirs or basedir == '*' or basedir == '/':
                    sys.stderr.write(
                        "INFO: " + ','.join(self.ignored['files'][basedir])
                        + " in " + basedir + '\n')

        if 'prefixes' in self.ignored:
            sys.stderr.write(
                "INFO: Ignoring files starting with the following:\n")
            sys.stderr.write(
                "INFO: " + ','.join(self.ignored['prefixes']) + '\n')

        if 'extensions' in self.ignored:
            sys.stderr.write(
                "INFO: Ignoring files ending with the following:\n")
            for basedir in self.ignored['extensions']:
                if basedir in basedirs or basedir == '*':
                    sys.stderr.write("INFO: " + ','.join(
                        self.ignored['extensions'][basedir])
                                     + " in " + basedir + '\n')
