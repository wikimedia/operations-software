import os
import sys
import traceback
from clouseau.retention.status import Status
import clouseau.retention.rule
from clouseau.retention.rule import Rule, RuleStore
import salt.utils.yamlloader
from salt.utils.yamldumper import SafeOrderedDumper
import yaml


def get_rules_for_entries(cdb, path, path_entries, host, quiet=False):
    rules = get_rules_for_path(cdb, path, host, True)
    for entry in path_entries:
        rules.extend(get_rules_for_path(cdb, entry, host, True))

    paths_kept = []
    uniq = []
    for rule in rules:
        if rule['path'] not in paths_kept:
            paths_kept.append(rule['path'])
            uniq.append(rule)

    if not quiet:
        uniq_sorted = sorted(uniq, key=lambda r: r['path'])
        for rule in uniq_sorted:
            print rule
    return uniq_sorted

def import_rule_list(cdb, entries, status, host):
    '''
    import status rules for a list of files or dirs
    - anything not ending in '/' is considered to be a file
    - files/dirs must be specified by full path, anything else
    will be skipped
    - failures to add to rule store are reported but processing continues
    '''
    for entry in entries:
        if entry[0] != os.path.sep:
            print "relative path in rule, skipping:", entry
            continue
        if entry[-1] == '/':
            entry_type = text_to_entrytype('dir')
            entry = entry[:-1]
        else:
            entry_type = text_to_entrytype('file')
        try:
            do_add_rule(cdb, entry, entry_type,
                        status, host)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            sys.stderr.write(repr(traceback.format_exception(
                exc_type, exc_value, exc_traceback)))
            sys.stderr.write("Couldn't add rule for %s to rule store\n" %
                             entry)

def import_rules(cdb, rules_path, host):
    # we don't toss all existing rules, these get merged into
    # the rules already in the rules store

    # it is possible to bork the list of files by deliberately
    # including a file/dir with a newline in the name; this will
    # just mean that your rule doesn't cover the files/dirs you want.

    try:
        contents = open(rules_path).read()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sys.stderr.write(repr(traceback.format_exception(
            exc_type, exc_value, exc_traceback)))
        sys.stderr.write("Couldn't read rules from %s.\n" % rules_path)
        return

    yaml_contents = salt.utils.yamlloader.load(contents, Loader=salt.utils.yamlloader.SaltYamlSafeLoader)
    for status in Status.status_cf:
        if status in yaml_contents:
            import_rule_list(
                cdb, yaml_contents[status],
                Status.status_cf[status][0], host)

def do_remove_rule(cdb, path, host):
    cdb.store_db_delete({'basedir': os.path.dirname(path),
                         'name': os.path.basename(path)},
                        host)

def do_remove_rules(cdb, status, host):
    cdb.store_db_delete({'status': status},
                        host)

def do_add_rule(cdb, path, rtype, status, host):
    cdb.store_db_replace({'basedir': os.path.dirname(path),
                          'name': os.path.basename(path),
                          'type': rtype,
                          'status': status},
                         host)

def check_host_table_exists(cdb, host):
    return cdb.store_db_check_host_table(host)

def normalize_path(path, ptype):
    '''
    make sure the path ends in '/' if it's dir type, otherwise
    that it does not, return the normalized path
    '''
    if ptype == 'dir':
        if path[-1] != os.path.sep:
            path = path + os.path.sep
    else:
        if path[-1] == os.path.sep:
            path = path[:-1]
    return path

def export_rules(cdb, rules_path, host, status=None):
    rules = get_rules(cdb, host, status)
    sorted_rules = {}
    for stext in Status.STATUS_TEXTS:
        sorted_rules[stext] = []
    for rule in rules:
        if rule['status'] in Status.STATUS_TEXTS:
            rule['path'] = normalize_path(rule['path'], rule['type'])
            sorted_rules[rule['status']].append(rule['path'])
        else:
            continue

    rules_by_status = {}
    for status in Status.STATUS_TEXTS:
        rules_by_status[status] = sorted_rules[status]
    try:
        filep = open(rules_path, "w+")
        contents = yaml.dump(rules_by_status,
                             line_break='\n',
                             default_flow_style=False,
                             Dumper=SafeOrderedDumper)
        filep.write(contents)
        filep.close()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sys.stderr.write(repr(traceback.format_exception(
            exc_type, exc_value, exc_traceback)))
        sys.stderr.write("Couldn't save rules into %s.\n" % rules_path)

def entrytype_to_text(abbrev):
    if abbrev in Rule.TYPES:
        return Rule.TYPES_TO_TEXT[abbrev]
    else:
        return None

def text_to_entrytype(fullname):
    for key in Rule.TYPES_TO_TEXT:
        if Rule.TYPES_TO_TEXT[key] == fullname:
            return key
    return None

def row_to_rule(row):
    # ('/home/ariel/wmf/security', '/home/ariel/wmf/security/openjdk6', 'D', 'G')
    (basedir, name, entrytype, status) = row
    basedir = clouseau.retention.rule.from_unicode(basedir)
    name = clouseau.retention.rule.from_unicode(name)
    rule = {'path': os.path.join(basedir, name),
            'type': entrytype_to_text(entrytype),
            'status': Status.status_to_text(status)}
    return rule

def get_rules(cdb, host, status=None):
    if status:
        crs = cdb.store_db_select(['basedir', 'name', 'type', 'status'],
                                  {'status': status}, host)
    else:
        crs = cdb.store_db_select(['basedir', 'name', 'type', 'status'],
                                  None, host)
    rules = []
    rows = RuleStore.store_db_get_all_rows(crs)
    for row in rows:
        rules.append(row_to_rule(row))
    return rules

def show_rules(cdb, host, status=None, prefix=None):
    rules = get_rules(cdb, host, status)
    if rules:
        rules_sorted = sorted(rules, key=lambda r: r['path'])
        for rule in rules_sorted:
            if prefix is None or rule['path'].startswith(prefix):
                print rule

def get_rules_with_prefix(cdb, path, host):
    '''
    retrieve all rules where the basedir starts with the specified path
    '''
    # prefixes...
    crs = cdb.store_db_select(['basedir', 'name', 'type', 'status'],
                              {'basedir': path}, host)
    rules = []
    rows = RuleStore.store_db_get_all_rows(crs)
    for row in rows:
        rules.append(row_to_rule(row))
    return rules

def check_rule_prefixes(rows):
    '''
    separate out the rules with wildcards in the name field
    and those without
    '''
    text = []
    wildcards = []
    if rows is None:
        return text, wildcards

    for row in rows:
        if '*' in os.path.basename(row['path']):
            wildcards.append(row)
        else:
            text.append(row)
    return text, wildcards

def rule_is_prefix(basedir, name, path, wildcard=False):
    '''
    if the dir part of the rule entry plus the basename is
    a proper path prefix of the specified path (followed by the
    path separator, or it's the exact path), return True, else False

    wildcard matches are done only for a single wildcard in the name
    component of the rule entry and does not cross a directory path
    component i.e. basedir = /a/b and name = c* will not match
    path /a/b/cow/dog  but will match /a/b/cow
    '''
    if not wildcard:
        if path.startswith(os.path.join(basedir, name) + os.path.sep):
            return True
        elif path == os.path.join(basedir, name):
            return True
    else:
        rulepath = os.path.join(basedir, name)
        if len(rulepath) >= len(path):
            return False

        left, right = rulepath.split('*', 1)
        if path.startswith(left):
            if path.endswith(right):
                if os.path.sep not in path[len(left): -1 * len(right)]:
                    return True
    return False

def get_rules_for_path(cdb, path, host, quiet=False):
    # get all paths starting from / and descending to the specified path
    prefixes = get_prefixes(path)
    rows = []
    # get all entries where the dir part of the path is a prefix and the
    # name part of the path will be checked to see if it is the next dir
    # elt in the path or wildcard matches it

    for pref in prefixes:
        rows.extend(get_rules_with_prefix(cdb, pref, host))
    # split out the rules with wildcards in the basename from the rest
    regulars, wildcards = check_rule_prefixes(rows)
    keep = []
    paths_kept = []
    for plain in regulars:
        if rule_is_prefix(os.path.dirname(plain['path']),
                          os.path.basename(plain['path']), path):
            if plain['path'] not in paths_kept:
                keep.append(plain)
                paths_kept.append(plain['path'])
    for wild in wildcards:
        if rule_is_prefix(os.path.dirname(wild['path']),
                          os.path.basename(wild['path']),
                          path, wildcard=True):
            if wild['path'] not in paths_kept:
                keep.append(wild)
                paths_kept.append(wild['path'])

    if len(keep) == 0:
        keep_sorted = keep
    else:
        keep_sorted = sorted(keep, key=lambda r: r['path'])
    if not quiet:
        print "No rules for directory"
    else:
        for rule in keep_sorted:
            print rule
    return keep_sorted

def get_prefixes(path):
    '''
    given an absolute path like /a/b/c, return the list of all paths
    starting from / and descending to the specified path
    i.e. if given '/a/b/c', would return ['/', '/a', '/a/b', 'a/b/c']
    for relative paths or empty paths we return an empty prefix list
    '''
    if not path or path[0] != '/':
        return []
    fields = path.split(os.path.sep)
    prefix = "/"
    prefixes = [prefix]
    for field in fields:
        if field:
            prefix = os.path.join(prefix, field)
            prefixes.append(prefix)
    return prefixes
