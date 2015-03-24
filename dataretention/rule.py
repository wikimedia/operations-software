import os
import sys
import re
import json
import traceback
import sqlite3
from saltclientplus import LocalClientPlus
from status import Status

class Rule(object):
    '''
    manage rules, i.e. tuples (status, abspath, type)
    '''

    first_line_expected = re.compile(r'^\s*dir_rules\s*=\s*{\s*$')
    last_line_expected = re.compile(r'^\s*}\s*')
    blank_expr = re.compile(r'^\s*$')
    comment_expr = re.compile(r'^#.*$')
    entry_expr = re.compile(r"^\s*'(.*)'\s*,?\s*$")
    end_entries_expr = re.compile(r"^\s*],?\s*$")

    TYPES_TO_TEXT = {'D': 'dir', 'F': 'file', 'L': 'link', 'U': 'unknown'}
    TYPES = TYPES_TO_TEXT.keys()

    STATE_START = 0
    STATE_EXPECT_STATUS = 1
    STATE_EXPECT_ENTRIES = 2

    @staticmethod
    def to_unicode(param):
        '''
        convert a parameter to unicode if it is not already
        '''
        newparam = param
        if not isinstance(param, unicode):
            try:
                newparam = unicode(param, 'utf-8')
            except:
                pass
        if newparam is None:
            newparam = param
        return newparam

    @staticmethod
    def from_unicode(param):
        '''
        convert a parameter from unicode back to bytes it is not already
        '''
        newparam = param
        if isinstance(param, unicode):
            try:
                newparam = param.encode('utf-8', 'replace')
            except:
                pass
            if newparam is None:
                newparam = param
        return newparam

    @staticmethod
    def get_rules_for_entries(cdb, path, path_entries, host, quiet=False):
        rules = Rule.get_rules_for_path(cdb, path, host, True)
        for entry in path_entries:
            rules.extend(Rule.get_rules_for_path(cdb, entry, host, True))

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

    @staticmethod
    def format_rules_for_export(rules_list, indent_count):
        if len(rules_list) == 0:
            return "[]"

        spaces = " " * 4
        indent = spaces * indent_count
        return ("[\n" + indent + spaces +
                (",\n" + indent + spaces).join(
                    ["'" + rule['path'].replace("'", r"\'") + "'"
                     for rule in rules_list]
                )
                + "\n" + indent + "]")

    @staticmethod
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
                entry_type = Rule.text_to_entrytype('dir')
                entry = entry[:-1]
            else:
                entry_type = Rule.text_to_entrytype('file')
            try:
                Rule.do_add_rule(cdb, entry, entry_type,
                                 status, host)
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                sys.stderr.write(repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback)))
                sys.stderr.write("Couldn't add rule for %s to rule store\n" %
                                 entry)

    @staticmethod
    def import_handle_status(line):
        '''
        see if the line passed is a status def line
        returns status found (if any) and next state
        '''
        for stat in Status.status_cf:
            result = Status.status_cf[stat][1].match(line)
            if result is not None:
                if "]" in result.group(0):
                    return None, Rule.STATE_EXPECT_STATUS
                else:
                    return stat, Rule.STATE_EXPECT_ENTRIES
        return None, None

    @staticmethod
    def import_rules(cdb, rules_path, host):
        # we don't toss all existing rules, these get merged into
        # the rules already in the rules store

        # it is possible to bork the list of files by deliberately
        # including a file/dir with a newline in the name; this will
        # just mean that your rule doesn't cover the files/dirs you want.
        try:
            rules_text = open(rules_path).read()
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            sys.stderr.write(repr(traceback.format_exception(
                exc_type, exc_value, exc_traceback)))
            sys.stderr.write("Couldn't read rules from %s.\n" % rules_path)
            return

        lines = rules_text.split("\n")
        state = Rule.STATE_START
        rules = {}
        active = None
        for line in lines:
            if Rule.comment_expr.match(line) or Rule.blank_expr.match(line):
                continue
            elif state == Rule.STATE_START:
                if not Rule.first_line_expected.match(line):
                    print "unexpected line in rules file, wanted "
                    print "'dir_rules = ...', aborting:"
                    print line
                    return
                else:
                    state = Rule.STATE_EXPECT_STATUS
            elif state == Rule.STATE_EXPECT_STATUS:
                if Rule.last_line_expected.match(line):
                    # done parsing file
                    break
                active, state = Rule.import_handle_status(line)
                if state == Rule.STATE_EXPECT_STATUS:
                    continue
                elif state == Rule.STATE_EXPECT_ENTRIES:
                    rules[active] = []
                elif state is None:
                    # not a status with empty list, not a status
                    # expecting entries on following lines, bail
                    print "unexpected line in rules file, aborting:"
                    print line
                    return
            elif state == Rule.STATE_EXPECT_ENTRIES:
                if Rule.entry_expr.match(line):
                    result = Rule.entry_expr.match(line)
                    rules[active].append(result.group(1))
                elif Rule.end_entries_expr.match(line):
                    active = None
                    state = Rule.STATE_EXPECT_STATUS
                else:
                    active, state = Rule.import_handle_status(line)
                    if state == Rule.STATE_EXPECT_STATUS:
                        # end of entries with crap syntax, we forgive
                        continue
                    elif state == Rule.STATE_EXPECT_ENTRIES:
                        # found a status line with empty list.
                        # so end of these entries ayways
                        state = Rule.STATE_EXPECT_STATUS
                        continue
                    elif state is None:
                        # not an entry, not a status, not end of entries
                        print "unexpected line in rules file, wanted entry, "
                        print "status or entry end marker, aborting:"
                        print line
                        return
            else:
                print "unexpected line in rules file, aborting:"
                print line
                return

        for status in Status.status_cf:
            if status in rules:
                Rule.import_rule_list(
                    cdb, rules[status],
                    Status.status_cf[status][0], host)

    @staticmethod
    def do_remove_rule(cdb, path, host):
        cdb.store_db_delete({'basedir': os.path.dirname(path),
                             'name': os.path.basename(path)},
                            host)

    @staticmethod
    def do_remove_rules(cdb, status, host):
        cdb.store_db_delete({'status': status},
                            host)

    @staticmethod
    def do_add_rule(cdb, path, rtype, status, host):
        cdb.store_db_replace({'basedir': os.path.dirname(path),
                              'name': os.path.basename(path),
                              'type': rtype,
                              'status': status},
                             host)

    @staticmethod
    def check_host_table_exists(cdb, host):
        return cdb.store_db_check_host_table(host)
        
    @staticmethod
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

    @staticmethod
    def export_rules(cdb, rules_path, host, status=None):
        # would be nice to be able to only export some rules. whatever

        rules = Rule.get_rules(cdb, host, status)
        sorted_rules = {}
        for stext in Status.STATUS_TEXTS:
            sorted_rules[stext] = []
        for rule in rules:
            if rule['status'] in Status.STATUS_TEXTS:
                rule['path'] = Rule.normalize_path(rule['path'], rule['type'])
                sorted_rules[rule['status']].append(rule)
            else:
                continue

        output = "dir_rules = {\n"
        for status in Status.STATUS_TEXTS:
            output += "    '%s': %s,\n" % (
                status, Rule.format_rules_for_export(sorted_rules[status], 2))
        output += "}\n"
        try:
            filep = open(rules_path, "w")
            filep.write("# -*- coding: utf-8 -*-\n")
            filep.write(output)
            filep.close()
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            sys.stderr.write(repr(traceback.format_exception(
                exc_type, exc_value, exc_traceback)))
            sys.stderr.write("Couldn't save rules into %s.\n" % rules_path)

    @staticmethod
    def entrytype_to_text(abbrev):
        if abbrev in Rule.TYPES:
            return Rule.TYPES_TO_TEXT[abbrev]
        else:
            return None

    @staticmethod
    def text_to_entrytype(fullname):
        for key in Rule.TYPES_TO_TEXT:
            if Rule.TYPES_TO_TEXT[key] == fullname:
                return key
        return None

    @staticmethod
    def row_to_rule(row):
        # ('/home/ariel/wmf/security', '/home/ariel/wmf/security/openjdk6', 'D', 'G')
        (basedir, name, entrytype, status) = row
        basedir = Rule.from_unicode(basedir)
        name = Rule.from_unicode(name)
        rule = {'path': os.path.join(basedir, name),
                'type': Rule.entrytype_to_text(entrytype),
                'status': Status.status_to_text(status)}
        return rule

    @staticmethod
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
            rules.append(Rule.row_to_rule(row))
        return rules

    @staticmethod
    def show_rules(cdb, host, status=None, prefix=None):
        rules = Rule.get_rules(cdb, host, status)
        if rules:
            rules_sorted = sorted(rules, key=lambda r: r['path'])
            for rule in rules_sorted:
                if prefix is None or rule['path'].startswith(prefix):
                    print rule

    @staticmethod
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
            rules.append(Rule.row_to_rule(row))
        return rules

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def get_rules_for_path(cdb, path, host, quiet=False):
        # get all paths starting from / and descending to the specified path
        prefixes = Rule.get_prefixes(path)
        rows = []
        # get all entries where the dir part of the path is a prefix and the
        # name part of the path will be checked to see if it is the next dir
        # elt in the path or wildcard matches it

        for pref in prefixes:
            rows.extend(Rule.get_rules_with_prefix(cdb, pref, host))
        # split out the rules with wildcards in the basename from the rest
        regulars, wildcards = Rule.check_rule_prefixes(rows)
        keep = []
        paths_kept = []
        for plain in regulars:
            if Rule.rule_is_prefix(os.path.dirname(plain['path']),
                                   os.path.basename(plain['path']), path):
                if plain['path'] not in paths_kept:
                    keep.append(plain)
                    paths_kept.append(plain['path'])
        for wild in wildcards:
            if Rule.rule_is_prefix(os.path.dirname(wild['path']),
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

    @staticmethod
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

    @staticmethod
    def get_rule_as_json(path, ptype, status):
        rule = {'basedir': os.path.dirname(path),
                'name': os.path.basename(path),
                'type': ptype,
                'status': status}
        return json.dumps(rule)


class RuleStore(object):
    '''
    store of directory/file status information for data retention auditing
    uses sqlite3

    each host store is a separate table
    each record in a table has the following fields:

    basedir path (key) type status
    where:
        basedir is the directory containing the entry
        name is the name of the entry
        type is one of D (dir) or F (file) or possibly L(link) or U(unknown)
        status is one of
           P - problem                  -- known to have problematic files
           G - good                     -- known to be ok and no
                                           need to recheck in future
           R - recheck files            -- all files during current run ok but
                                           must be rechecked on next run
           U - unknown, needs review    -- unknown, directory never reviewed by
                                           a human

    Not every file or directory in an audited area needs to have an entry
    in this store; files or directories without entries will be treated as
    though they have U status (unknown)
    '''

    def __init__(self, storename):
        '''
        args: full path to sqlite db with rules

        this does not open the db, that happens
        on an as needed basis
        '''

        self.TABLE = 'filestatus'
        self.FIELDS = {'basedir': 'text', 'name': 'text',
                       'type': 'text', 'status': 'text'}
        self.storename = storename
        self.store_db = None
        self.crs = None
        self.known_hosts = None

    def get_tablename(self, host):
        '''
        each host's rules are stored in a separate table,
        get and return the table name for the given host
        the hostname should be the fqdn
        '''

        return self.TABLE + "_" + host.replace('-', '__').replace('.', '_')

    def get_salt_known_hosts(self):
        '''
        get all known salt minions by doing a test.ping
        and getting the list of expanded minions (not of responsive hosts,
        of known hosts)
        FIXME there are functions provided for this in more recent
        versions of salt, use them
        '''

        if self.known_hosts is None:
            client = LocalClientPlus()
            # fixme we should just look up the salt keys, cheaper
            self.known_hosts = client.cmd_expandminions('*', "test.ping",
                                                        expr_form='glob')
        return self.known_hosts

    def store_db_init(self, hosts):
        '''
        open the sqlite db and set up for queries,
        if it has not been done earlier
        '''

        if self.store_db is not None:
            return

        self.store_db = sqlite3.connect(self.storename)
        self.crs = self.store_db.cursor()

        if hosts is None:
            return

        for host in hosts:
            if self.no_table_for_host(host):
                self.crs.execute(
                    '''CREATE TABLE %s
                    (`basedir` text, `name` text, `type` text,
                    `status` text, PRIMARY KEY (`basedir`, `name`))'''
                    % self.get_tablename(host))
                self.store_db.commit()

    def no_table_for_host(self, host):
        '''
        check if there is no table created in the rules db
        for the specified host;
        returns True if this is the case,
        False if there is in fact an entry,
        None if the host is not in the list of salt known hosts
        '''

        if self.known_hosts is None:
            self.get_salt_known_hosts()
        if host not in self.known_hosts:
            # hostname probably bogus.
            print "WARNING: host not known, typo?", host
            return None

        hosts_in_db = self.store_db_list_all_hosts()
        if hosts_in_db is None or host not in hosts_in_db:
            return True
        else:
            return False

    def check_params(self, params, fieldlist=None, show=True):
        if fieldlist is None:
            fieldlist = self.FIELDS.keys()
        err = False
        for field in fieldlist:
            if field not in params:
                if show:
                    print "WARNING: missing field %s" % field
                    print "WARNING: received:", params
                err = True
            else:
                ftype = self.FIELDS[field]
                # fixme what about path, no sanitizing there, this is bad.
                # same for hostname, no checking...
                if ftype == 'integer' and not params[field].isdigit():
                    if show:
                        print ("WARNING: bad param %s, should be number: %s"
                               % (field, params[field]))
                    err = True
                elif ftype == 'text':
                    if field == 'type' and params[field] not in Rule.TYPES:
                        if show:
                            print "WARNING: bad type %s specified" % params[field]
                            err = True
                    elif (field == 'status' and
                          params[field] not in Status.STATUSES):
                        if show:
                            print ("WARNING: bad status %s specified" %
                                   params[field])
                        err = True
        if err:
            return False
        else:
            return True

    def store_db_check_host_table(self, host):
        '''
        check if a table for the specific host exists, returning True if so
        '''
        self.crs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='%s'"
                         % self.get_tablename(host))
        self.store_db.commit()
        result = self.crs.fetchone()
        if result is None:
            return False
        else:
            return True

    def store_db_insert(self, params, host):
        '''
        insert a row into the rules table for the specified
        host; each entry consists of basedir, name, type, status
        of a file/dir, and the params passed in should be a dict
        with values for those fields

        '''
        if not self.check_params(params):
            print "WARNING: bad parameters specified"

        self.crs.execute("INSERT INTO %s VALUES (?, ?, ?, ?)"
                         % self.get_tablename(host),
                         (Rule.to_unicode(params['basedir']),
                          Rule.to_unicode(params['name']),
                          params['type'],
                          params['status']))
        self.store_db.commit()

    def store_db_replace(self, params, host):
        '''
        replace entries in the table for the specified
        host; each entry consists of basedir, name, type, status
        of a file/dir, and the params passed in should be a dict
        with values for those fields
        '''
        if not self.check_params(params):
            print "WARNING: bad params passed", params

        self.crs.execute("INSERT OR REPLACE INTO  %s VALUES (?, ?, ?, ?)"
                         % self.get_tablename(host),
                         (Rule.to_unicode(params['basedir']),
                          Rule.to_unicode(params['name']),
                          params['type'],
                          params['status']))
        self.store_db.commit()

    @staticmethod
    def params_to_string(params):
        result = []
        values_to_sub = []
        for pname in params:
            if '%' in params[pname]:
                result.append("%s LIKE ?" % pname)
                values_to_sub.append(params[pname])
            else:
                result.append("%s=?" % pname)
                values_to_sub.append(params[pname])
        return " AND ".join(result), values_to_sub

    def store_db_select(self, from_params, where_params, host):
        '''
        get a row from rules table for the specified host
        from_params is a list of the fields desired from the row,
        where_params is a dict with key, value pairs the field name and
        the field value desired, % in a field value is permitted
        '''

        # fixme quoting
        crs = self.store_db.cursor()

        if where_params is not None:
            clause, params_to_sub = RuleStore.params_to_string(where_params)
            query = ("SELECT %s FROM %s WHERE %s"
                     % (",".join(from_params),
                        self.get_tablename(host),
                        clause))
        else:
            query = ("SELECT %s FROM %s"
                     % (",".join(from_params),
                        self.get_tablename(host)))
            params_to_sub = None

        if params_to_sub:
            crs.execute(query, params_to_sub)
        else:
            crs.execute(query)
        self.store_db.commit()
        return crs

    @staticmethod
    def store_db_get_one_row(cursor):
        '''
        return one row from a select result
        '''
        return cursor.fetchone()

    @staticmethod
    def store_db_get_all_rows(cursor):
        '''
        return all rows from a select result
        '''
        return cursor.fetchall()

    def store_db_delete(self, params, host):
        '''
        delete row(s) from table for specified host
        either specify the basedir and name (= the full path)
        for some rule, in which case that rule will be
        deleted, or
        specify a status in which case all entries with
        that status will be deleted
        '''
        # fixme quoting
        if (not self.check_params(params, ['basedir', 'name'], show=False)
                and not self.check_params(params, ['status'], show=False)):
            print "WARNING: bad params passed", params
        clause, params_to_sub = RuleStore.params_to_string(params)
        query = ("DELETE FROM %s WHERE %s"
                 % (self.get_tablename(host),
                    clause))
        self.crs.execute(query, params_to_sub)
        self.store_db.commit()

    def store_db_close(self):
        '''
        close connection to the rule store db
        and close the file itself
        '''
        if self.store_db is not None:
            self.store_db.close()
            self.store_db = None

    def store_db_list_all_hosts(self):
        '''
        get and return list of known hosts from the rules db
        extracting them from the tablenames
        '''
        hosts = []
        if self.store_db is None:

            if not os.path.exists(self.storename):
                return hosts

            store_db = sqlite3.connect(self.storename)
            crs = store_db.cursor()

        else:
            crs = self.crs

        crs.execute("SELECT name FROM sqlite_master WHERE type='table';")

        tables = [row[0] for row in crs.fetchall()]
        for table in tables:
            if table.startswith(self.TABLE + "_"):
                hosts.append(table[len(self.TABLE + "_"):].
                             replace('__', '-').replace('_', '.'))
        return hosts

