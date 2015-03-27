import os
import re
import stat

def startswith(string_arg, list_arg):
    '''
    check if the string arg starts with any elt in
    the list_arg
    '''
    for elt in list_arg:
        if string_arg.startswith(elt):
            return True
    return False

def contains(string_arg, list_arg):
    '''
    check if the string arg cotains any elt in
    the list_arg
    '''
    for elt in list_arg:
        if elt in string_arg:
            return True
    return False

def endswith(string_arg, list_arg):
    '''
    check if the string arg ends with any elt in
    the list_arg
    '''
    for elt in list_arg:
        if string_arg.endswith(elt):
            return True
    return False

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

def file_is_ignored(fname, basedir, ignored):
    '''
    pass normalized name (abs path), basedir (location audited),
    hash of ignored files, dirs, prefixes, extensions
    get back True if the file is to be ignored and
    False otherwise
    '''

    basename = os.path.basename(fname)

    if 'prefixes' in ignored:
        if startswith(basename, ignored['prefixes']):
            return True

    if 'extensions' in ignored:
        if '*' in ignored['extensions']:
            if endswith(basename, ignored['extensions']['*']):
                return True
        if basedir in ignored['extensions']:
            if endswith(
                    basename, ignored['extensions'][basedir]):
                return True

    if 'files' in ignored:
        if basename in ignored['files']:
            return True
        if '*' in ignored['files']:
            if endswith(basename, ignored['files']['*']):
                return True

        if '/' in ignored['files']:
            if fname in ignored['files']['/']:
                return True
            if wildcard_matches(
                    fname, [w for w in ignored['files']['/'] if '*' in w]):
                return True

        if basedir in ignored['files']:
            if endswith(basename, ignored['files'][basedir]):
                return True
    return False

def dir_is_ignored(dirname, ignored):
    expanded_dirs, wildcard_dirs = expand_ignored_dirs(
        os.path.dirname(dirname), ignored)
    if dirname in expanded_dirs:
        return True
    if wildcard_matches(dirname, wildcard_dirs):
        return True
    return False

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
