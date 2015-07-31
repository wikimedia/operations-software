import os
import sqlite3
from clouseau.retention.saltclientplus import LocalClientPlus
from clouseau.retention.status import Status

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

def get_tablename(host):
    '''
    each host's rules are stored in a separate table,
    get and return the table name for the given host
    the hostname should be the fqdn
    '''
    return RuleStore.TABLE + "_" + host.replace('-', '__').replace('.', '_')

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

def check_params(params, fieldlist=None, show=True):
    if fieldlist is None:
        fieldlist = RuleStore.FIELDS.keys()
    err = False
    for field in fieldlist:
        if field not in params:
            if show:
                print "WARNING: missing field %s" % field
                print "WARNING: received:", params
            err = True
        else:
            ftype = RuleStore.FIELDS[field]
            # fixme what about path, no sanitizing there, this is bad.
            # same for hostname, no checking...
            if ftype == 'integer' and not params[field].isdigit():
                if show:
                    print ("WARNING: bad param %s, should be number: %s"
                           % (field, params[field]))
                err = True
            elif ftype == 'text':
                if field == 'type' and params[field] not in RuleStore.TYPES:
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

    TABLE = 'filestatus'
    FIELDS = {'basedir': 'text', 'name': 'text',
              'type': 'text', 'status': 'text'}
    TYPES_TO_TEXT = {'D': 'dir', 'F': 'file', 'L': 'link', 'U': 'unknown'}
    TYPES = TYPES_TO_TEXT.keys()

    def __init__(self, storename):
        '''
        args: full path to sqlite db with rules

        this does not open the db, that happens
        on an as needed basis
        '''

        self.storename = storename
        self.store_db = None
        self.crs = None
        self.known_hosts = None

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
                    % get_tablename(host))
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

    def store_db_check_host_table(self, host):
        '''
        check if a table for the specific host exists, returning True if so
        '''
        self.crs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='%s'"
                         % get_tablename(host))
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
        if not check_params(params):
            print "WARNING: bad parameters specified"

        self.crs.execute("INSERT INTO %s VALUES (?, ?, ?, ?)"
                         % get_tablename(host),
                         (to_unicode(params['basedir']),
                          to_unicode(params['name']),
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
        if not check_params(params):
            print "WARNING: bad params passed", params

        self.crs.execute("INSERT OR REPLACE INTO  %s VALUES (?, ?, ?, ?)"
                         % get_tablename(host),
                         (to_unicode(params['basedir']),
                          to_unicode(params['name']),
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
                        get_tablename(host),
                        clause))
        else:
            query = ("SELECT %s FROM %s"
                     % (",".join(from_params),
                        get_tablename(host)))
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
        if (not check_params(params, ['basedir', 'name'], show=False)
                and not check_params(params, ['status'], show=False)):
            print "WARNING: bad params passed", params
        clause, params_to_sub = RuleStore.params_to_string(params)
        query = ("DELETE FROM %s WHERE %s"
                 % (get_tablename(host),
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
            if table.startswith(RuleStore.TABLE + "_"):
                hosts.append(table[len(RuleStore.TABLE + "_"):].
                             replace('__', '-').replace('_', '.'))
        return hosts
