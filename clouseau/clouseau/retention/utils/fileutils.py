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
