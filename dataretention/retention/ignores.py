import os
import sys
import socket
import salt.client
import salt.utils.yamlloader

from clouseau.retention.status import Status
import clouseau.retention.utils
import clouseau.retention.fileutils
import clouseau.retention.ruleutils
import clouseau.retention.config

def prep_good_rules_tosend(dirname, hosts):
    '''
    on the master:

    prepare a dict of file paths vs contents of good
    rules, for use by salt cp.recv
    (sending these files to the minions)

    this method expects the good rules to have
    previously been exported from the rules store
    '''
    results = {}
    if not hosts:
        return results
    for host in hosts:
        path = os.path.join(dirname, host + '_store_good.yaml')
        if os.path.exists(path):
            try:
                results[path] = open(path).read()
            except:
                # if we can't get the file contents for some reason,
                # make sure this file isn't in the dict
                results.pop(path, None)
    return results

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
    if clouseau.retention.fileutils.wildcard_matches(dirname, wildcard_dirs):
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
        if '*' in ignored['prefixes']:
            if clouseau.retention.fileutils.startswith(basename, ignored['prefixes']['*']):
                return True
        if basedir in ignored['prefixes']:
            if clouseau.retention.fileutils.startswith(
                    basename, ignored['prefixes'][basedir]):
                return True

    if 'extensions' in ignored:
        if '*' in ignored['extensions']:
            if clouseau.retention.fileutils.endswith(basename, ignored['extensions']['*']):
                return True
        if basedir in ignored['extensions']:
            if clouseau.retention.fileutils.endswith(
                    basename, ignored['extensions'][basedir]):
                return True

    if 'files' in ignored:
        if basename in ignored['files']:
            return True
        if '*' in ignored['files']:
            if clouseau.retention.fileutils.endswith(basename, ignored['files']['*']):
                return True

        if '/' in ignored['files']:
            if fname in ignored['files']['/']:
                return True
            if clouseau.retention.fileutils.wildcard_matches(
                    fname, [w for w in ignored['files']['/'] if '*' in w]):
                return True

        if basedir in ignored['files']:
            if clouseau.retention.fileutils.endswith(basename, ignored['files'][basedir]):
                return True
    return False

def get_home_dirs(confdir, locations):
    '''
    get a list of home directories where the root location(s) for home are
    specified in the Config class (see 'home_locations'), by reading
    these root location dirs and grabbing all subdirectory names from them
    '''
    clouseau.retention.config.set_up_conf(confdir)
    home_dirs = []

    for location in clouseau.retention.config.conf[locations]:
        if not os.path.isdir(location):
            continue
        home_dirs.extend([os.path.join(location, d)
                          for d in os.listdir(location)
                          if os.path.isdir(os.path.join(location, d))])
    return home_dirs

def init_ignored():
    ignored = {}
    ignored['files'] = {}
    ignored['files']['/'] = []
    ignored['dirs'] = {}
    ignored['dirs']['/'] = []
    ignored['prefixes'] = {}
    ignored['extensions'] = {}
    return ignored

def get_local_ignores(confdir, locations):
    '''
    read a list of absolute paths from /home/blah/.data_retention
    for all blah.  Dirs are specified by op sep at the end ('/')
    and files without.
    '''
    local_ignores = {}
    home_dirs = get_home_dirs(confdir, locations)
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

def process_local_ignores(local_ignores):
    '''
    files or dirs listed in data retention conf in homedir
    are considered 'good' and added to ignore list

    non-absolute paths will be taken as relative to the
    home dir of the data retention config they were
    read from
    '''

    result = clouseau.retention.ignores.init_ignored()
    for basedir in local_ignores:
        for path in local_ignores[basedir]:
            if not path.startswith('/'):
                path = os.path.join(basedir, path)

            if path.endswith('/'):
                result['dirs']['/'].append(path[:-1])
            else:
                result['files']['/'].append(path)
    return result

def get_ignored_from_rulestore(cdb, hosts):
    ignored = {}
    for host in hosts:
        rules_from_store = clouseau.retention.ruleutils.get_rules(
            cdb, host, Status.text_to_status('good'))

        if rules_from_store is not None:
            ignored[host] = clouseau.retention.ignores.init_ignored()

            for rule in rules_from_store:
                if rule['status'] != 'good':
                    continue
                path = rule['path']
                if rule['type'] == 'dir':
                    if path.endswith('/'):
                        path = path[:-1]
                    ignored[host]['dirs']['/'].append(path)
                else:
                    ignored[host]['files']['/'].append(path)
    return ignored

def convert_rules_to_ignored(rules):
    '''
    from rules passed in as arg (retrieved
    from rulestore), grab the relevant ones,
    turn them into an ignores object, and
    return it
    '''
    ignored = clouseau.retention.ignores.init_ignored()

    if 'good' not in rules:
        return

    for path in rules['good']:
        if path.endswith('/'):
            ignored['dirs']['/'].append(path[:-1])
        else:
            ignored['files']['/'].append(path)
    return ignored

def get_ignored_from_exported_rules(confdir):
    hostname = socket.getfqdn()
    fromstore_file = os.path.join(confdir, 'fromstore', hostname + "_store_good.yaml")
    if os.path.exists(fromstore_file):
        contents = open(fromstore_file).read()
        exported_rules = salt.utils.yamlloader.load(
            contents, Loader=salt.utils.yamlloader.SaltYamlSafeLoader)
    else:
        exported_rules = None
    if exported_rules is not None:
        ignored = clouseau.retention.ignores.convert_rules_to_ignored(exported_rules)
    else:
        ignored = clouseau.retention.ignores.init_ignored()
    return ignored

def set_up_global_ignored(confdir):
    '''
    collect up initial list of files/dirs to skip during audit
    '''

    ignored = clouseau.retention.ignores.init_ignored()

    if confdir is not None:
        configfile = os.path.join(confdir, 'global_ignored.yaml')
        if os.path.exists(configfile):
            try:
                contents = open(configfile).read()
                ign = salt.utils.yamlloader.load(contents, Loader=salt.utils.yamlloader.SaltYamlSafeLoader)
                if 'ignored_files' in ign:
                    ignored['files'] = ign['ignored_files']
                if 'ignored_dirs' in ign:
                    ignored['dirs'] = ign['ignored_dirs']
                if 'ignored_prefixes' in ign:
                    ignored['prefixes'] = ign['ignored_prefixes']
                if 'ignored_extensions' in ign:
                    ignored['extensions'] = ign['ignored_extensions']
            except:
                pass
    return ignored

def convert_ignore_also_to_ignores(ignore_also):
    ignored = clouseau.retention.ignores.init_ignored()
    if ignore_also is not None:
        # silently skip paths that are not absolute
        for path in ignore_also:
            if path.startswith('/'):
                if path.endswith('/'):
                    ignored['dirs']['/'].append(path[:-1])
                else:
                    ignored['files']['/'].append(path)
    return ignored

def get_perhost_ignored_from_file(confdir):
    '''
    get the lists of files and dirs to be ignored,
    from the perhost_ignored file, for all hosts
    in file
    '''
    perhost_ignores = None
    configfile = os.path.join(confdir, 'perhost_ignored.yaml')
    if os.path.exists(configfile):
        try:
            contents = open(configfile).read()
            yamlcontents = salt.utils.yamlloader.load(contents, Loader=salt.utils.yamlloader.SaltYamlSafeLoader)
            perhost_ignores = yamlcontents['perhostcf']
        except:
            perhost_ignores = None
    return perhost_ignores

def convert_perhost_ignored(perhost_ignored):
    '''
    add to ignored dirs and files lists the entries
    we get from the perhost_ignored file for each
    host in file
    '''
    ignored = {}
    if perhost_ignored is None:
        return

    if 'ignored_dirs' in perhost_ignored:
        for host in perhost_ignored['ignored_dirs']:
            if host not in ignored:
                ignored[host] = {}
            ignored[host]['dirs'] = {}
            ignored[host]['dirs']['/'] = [
                (lambda path: path[:-1] if path[-1] == '/'
                 else path)(p)
                for p in perhost_ignored[
                    'ignored_dirs'][host]]
    if 'ignored_files' in perhost_ignored:
        for host in perhost_ignored['ignored_files']:
            if host not in ignored:
                ignored[host] = {}
            ignored[host]['files'] = {}
            ignored[host]['files']['/'] = (
                perhost_ignored['ignored_files'][host])
    return ignored


class Ignores(object):
    '''
    collection of files and directories ignored by the audit
    on a given host
    '''

    def __init__(self, confdir):
        self.global_ignored = clouseau.retention.ignores.set_up_global_ignored(confdir)
        perhost_ignored = clouseau.retention.ignores.get_perhost_ignored_from_file(confdir)
        self.perhost_ignored = clouseau.retention.ignores.convert_perhost_ignored(perhost_ignored)

    def merge(self, ignoreds, hostname=None):
        '''
        grab the global, the perhost for the specified host, the passed in ignoreds
        and combine them all up into one giant ignored, return that
        '''
        result = clouseau.retention.ignores.init_ignored()
        todo = ignoreds + [self.global_ignored]
        if hostname is not None and hostname in self.perhost_ignored:
            todo.append(self.perhost_ignored[hostname])

        for ign in todo:
            for igntype in ign:
                for item in ign[igntype]:
                    if item not in result[igntype]:
                        result[igntype][item] = list(ign[igntype][item])
                    else:
                        result[igntype][item] = list(set(result[igntype][item] + ign[igntype][item]))
        return result

    def show_ignored(self, basedirs, ignored, headertext=None):
        if headertext:
            sys.stderr.write("INFO: " + headertext + '\n')

        if 'dirs' in ignored:
            sys.stderr.write("INFO: Ignoring the following directories:\n")
            for basedir in ignored['dirs']:
                if basedir in basedirs or basedir == '*' or basedir == '/':
                    sys.stderr.write(
                        "INFO: " + ','.join(ignored['dirs'][basedir])
                        + " in " + basedir + '\n')

        if 'files' in ignored:
            sys.stderr.write("INFO: Ignoring the following files:\n")
            for basedir in ignored['files']:
                if basedir in basedirs or basedir == '*' or basedir == '/':
                    sys.stderr.write(
                        "INFO: " + ','.join(ignored['files'][basedir])
                        + " in " + basedir + '\n')

        if 'prefixes' in ignored:
            sys.stderr.write(
                "INFO: Ignoring files starting with the following:\n")
            sys.stderr.write(
                "INFO: " + ','.join(ignored['prefixes']) + '\n')

        if 'extensions' in ignored:
            sys.stderr.write(
                "INFO: Ignoring files ending with the following:\n")
            for basedir in ignored['extensions']:
                if basedir in basedirs or basedir == '*':
                    sys.stderr.write("INFO: " + ','.join(
                        ignored['extensions'][basedir])
                                     + " in " + basedir + '\n')
