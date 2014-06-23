# pylint: disable=unused-wildcard-import

import os
import sys
import salt.client
import salt.utils
import time
import getopt
import re
import glob
import json
import gzip
import calendar
import datetime
import socket
import runpy
import stat
import readline
import atexit
import sqlite3
import traceback
import locale
import zlib
import base64

############
# the following code is taken from magic.py, see
# https://github.com/mammadori/magic-python

import ctypes

from ctypes import *
from ctypes.util import find_library


def _init():
    """
    Loads the shared library through ctypes and returns a library
    L{ctypes.CDLL} instance
    """
    return ctypes.cdll.LoadLibrary(find_library('magic'))

_libraries = {}
_libraries['magic'] = _init()

# Flag constants for open and setflags
MAGIC_NONE = NONE = 0
MAGIC_DEBUG = DEBUG = 1
MAGIC_SYMLINK = SYMLINK = 2
MAGIC_COMPRESS = COMPRESS = 4
MAGIC_DEVICES = DEVICES = 8
MAGIC_MIME_TYPE = MIME_TYPE = 16
MAGIC_CONTINUE = CONTINUE = 32
MAGIC_CHECK = CHECK = 64
MAGIC_PRESERVE_ATIME = PRESERVE_ATIME = 128
MAGIC_RAW = RAW = 256
MAGIC_ERROR = ERROR = 512
MAGIC_MIME_ENCODING = MIME_ENCODING = 1024
MAGIC_MIME = MIME = 1040
MAGIC_APPLE = APPLE = 2048

MAGIC_NO_CHECK_COMPRESS = NO_CHECK_COMPRESS = 4096
MAGIC_NO_CHECK_TAR = NO_CHECK_TAR = 8192
MAGIC_NO_CHECK_SOFT = NO_CHECK_SOFT = 16384
MAGIC_NO_CHECK_APPTYPE = NO_CHECK_APPTYPE = 32768
MAGIC_NO_CHECK_ELF = NO_CHECK_ELF = 65536
MAGIC_NO_CHECK_TEXT = NO_CHECK_TEXT = 131072
MAGIC_NO_CHECK_CDF = NO_CHECK_CDF = 262144
MAGIC_NO_CHECK_TOKENS = NO_CHECK_TOKENS = 1048576
MAGIC_NO_CHECK_ENCODING = NO_CHECK_ENCODING = 2097152

MAGIC_NO_CHECK_BUILTIN = NO_CHECK_BUILTIN = 4173824


class magic_set(Structure):
    pass
magic_set._fields_ = []
magic_t = POINTER(magic_set)

_open = _libraries['magic'].magic_open
_open.restype = magic_t
_open.argtypes = [c_int]

_close = _libraries['magic'].magic_close
_close.restype = None
_close.argtypes = [magic_t]

_file = _libraries['magic'].magic_file
_file.restype = c_char_p
_file.argtypes = [magic_t, c_char_p]

_buffer = _libraries['magic'].magic_buffer
_buffer.restype = c_char_p
_buffer.argtypes = [magic_t, c_void_p, c_size_t]

_error = _libraries['magic'].magic_error
_error.restype = c_char_p
_error.argtypes = [magic_t]

_setflags = _libraries['magic'].magic_setflags
_setflags.restype = c_int
_setflags.argtypes = [magic_t, c_int]

_load = _libraries['magic'].magic_load
_load.restype = c_int
_load.argtypes = [magic_t, c_char_p]

_errno = _libraries['magic'].magic_errno
_errno.restype = c_int
_errno.argtypes = [magic_t]


class Magic(object):
    def __init__(self, ms):
        self._magic_t = ms

    def close(self):
        """
        Closes the magic database and deallocates any resources used.
        """
        _close(self._magic_t)

    def file(self, filename):
        """
        Returns a textual description of the contents of the argument passed
        as a filename or None if an error occurred and the MAGIC_ERROR flag
        is set.  A call to errno() will return the numeric error code.
        """
        try:  # attempt python3 approach first
            bi = bytes(filename, 'utf-8')
            return str(_file(self._magic_t, bi), 'utf-8')
        except:
            return _file(self._magic_t, filename)

    def buffer(self, buf):
        """
        Returns a textual description of the contents of the argument passed
        as a buffer or None if an error occurred and the MAGIC_ERROR flag
        is set. A call to errno() will return the numeric error code.
        """
        try:  # attempt python3 approach first
            return str(_buffer(self._magic_t, buf, len(buf)), 'utf-8')
        except:
            return _buffer(self._magic_t, buf, len(buf))

    def error(self):
        """
        Returns a textual explanation of the last error or None
        if there was no error.
        """
        try:  # attempt python3 approach first
            return str(_error(self._magic_t), 'utf-8')
        except:
            return _error(self._magic_t)

    def setflags(self, flags):
        """
        Set flags on the magic object which determine how magic checking
        behaves; a bitwise OR of the flags described in libmagic(3), but
        without the MAGIC_  prefix.

        Returns -1 on systems that don't support utime(2) or utimes(2)
        when PRESERVE_ATIME is set.
        """
        return _setflags(self._magic_t, flags)

    def load(self, filename=None):
        """
        Must be called to load entries in the colon separated list of
        database files passed as argument or the default database file
        if no argument before any magic queries can be performed.

        Returns 0 on success and -1 on failure.
        """
        return _load(self._magic_t, filename)

    def errno(self):
        """
        Returns a numeric error code. If return value is 0, an internal
        magic error occurred. If return value is non-zero, the value is
        an OS error code. Use the errno module or os.strerror() can be used
        to provide detailed error information.
        """
        return _errno(self._magic_t)


def magic_open(flags):
    """
    Returns a magic object on success and None on failure.
    Flags argument as for setflags.
    """
    return Magic(_open(flags))


# end magic.py code
############

class JsonHelper(object):
    # adapted from
    # http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-ones-from-json-in-python
    @staticmethod
    def decode_list(data):
        result = []
        for item in data:
            if isinstance(item, unicode):
                item = item.encode('utf-8', 'replace')
            elif isinstance(item, list):
                item = JsonHelper.decode_list(item)
            elif isinstance(item, dict):
                item = JsonHelper.decode_dict(item)
            result.append(item)
        return result

    @staticmethod
    def decode_dict(data):
        result = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8', 'replace')
            elif isinstance(value, list):
                value = JsonHelper.decode_list(value)
            elif isinstance(value, dict):
                value = JsonHelper.decode_dict(value)
            result[key] = value
        return result


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

    def check_params(self, params, fieldlist=None):
        if fieldlist is None:
            fieldlist = self.FIELDS.keys()
        err = False
        for field in fieldlist:
            if field not in params:
                print "WARNING: missing field %s" % field
                print "WARNING: received:", params
                err = True
            else:
                ftype = self.FIELDS[field]
                # fixme what about path, no sanitizing there, this is bad.
                # same for hostname, no checking...
                if ftype == 'integer' and not params[field].isdigit():
                    print ("WARNING: bad param %s, should be number: %s"
                           % (field, params[field]))
                    err = True
                elif ftype == 'text':
                    if field == 'type' and params[field] not in Rule.TYPES:
                        print "WARNING: bad type %s specified" % params[field]
                        err = True
                    elif (field == 'status' and
                          params[field] not in Status.STATUSES):
                        print ("WARNING: bad status %s specified" %
                               params[field])
                        err = True
        if err:
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
                         (RuleStore.to_unicode(params['basedir']),
                          RuleStore.to_unicode(params['name']),
                          params['type'],
                          params['status']))
        self.store_db.commit()

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
                newpaaram = param
        return newparam

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
                         (RuleStore.to_unicode(params['basedir']),
                          RuleStore.to_unicode(params['name']),
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
        # fixme quoting, two groups of params
        if not self.check_params(params, ['basedir', 'name']):
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
        for t in tables:
            if t.startswith(self.TABLE + "_"):
                hosts.append(t[len(self.TABLE + "_"):].
                             replace('__', '-').replace('_', '.'))
        return hosts


class FileExaminer(object):
    '''
    retrieval and display of file contents on local or remote host
    '''
    def __init__(self, path, host, num_lines, timeout=20, quiet=False):
        self.path = path
        self.host = host
        self.timeout = timeout
        self.num_lines = num_lines
        self.quiet = quiet

    def run(self):
        '''
        do all the work
        '''
        if Runner.running_locally(self.host):
            fi = FileInfo(self.path, None)
            if fi.get_is_binary(self.num_lines):
                result = "BINARY CONTENT\n"
            else:
                result = fi.start_content
            if not self.quiet:
                print result,
            return result
        else:
            client = LocalClientPlus()
            code = "# -*- coding: utf-8 -*-\n"
            code += self.generate_executor()
            with open(__file__, 'r') as fp_:
                code += fp_.read()
            result = client.cmd([self.host], "cmd.exec_code",
                                ["python2", code],
                                expr_form='list',
                                timeout=self.timeout)
            if self.host in result:
                if not self.quiet:
                    print result[self.host]
                return result[self.host]

    def generate_executor(self):
        '''
        horrible hack: this code is fed to salt when we feed this
        script to stdin to run it remotely, thus bypassing all
        the command line argument parsing logic

        in this case we set up for FileExaminer directly
        '''
        code = """
def executor():
    fe = FileExaminer('%s', 'localhost', %d, %d)
    fe.run()
""" % (self.path, self.num_lines, self.timeout)
        return code


class DirExaminer(object):
    '''
    retrieval and display of directory contents on local or remote host
    '''
    def __init__(self, path, host, batchno=1, batchsize=300, timeout=20,
                 prettyprint=False):
        self.path = path
        self.st = None
        self.host = host
        self.timeout = timeout
        self.batchno = batchno
        self.batchsize = batchsize
        self.prettyprint = prettyprint

    def run(self, quiet=False):
        '''
        do all the work

        note that 'quiet' applies only to remotely
        run, and the same is true for returning the contents.
        maybe we want to fix that
        '''

        if Runner.running_locally(self.host):
            dc = DirContents(self.path, self.batchno, self.batchsize,
                             self.prettyprint)
            result = dc.get_contents()
            if result != 'ok':
                print ('WARNING: failed to get directory contents'
                       'for <%s> (%s)'
                       % (self.path, result))
            else:
                dc.get_batch_entryinfo()
                dc.show_batch()
        else:
            while True:
                client = LocalClientPlus()
                code = "# -*- coding: utf-8 -*-\n"
                code += self.generate_executor()
                with open(__file__, 'r') as fp_:
                    code += fp_.read()
                result = client.cmd([self.host], "cmd.exec_code",
                                    ["python2", code],
                                    expr_form='list',
                                    timeout=self.timeout)
                if self.host in result:
                    lines = result[self.host].split("\n")

                    maxlen = 0
                    for line in lines:
                        if (line.startswith("WARNING:") or
                            line.startswith("INFO:")):
                            continue
                        else:
                            try:
                                entry = json.loads(
                                    line, object_hook=JsonHelper.decode_dict)
                                if len(entry['path']) > maxlen:
                                    maxlen = len(entry['path'])
                            except:
                                continue

                    if not quiet:
                        for line in lines:
                            if (line.startswith("WARNING:") or
                                line.startswith("INFO:")):
                                print line
                            else:
                                try:
                                    entry = json.loads(
                                        line,
                                        object_hook=JsonHelper.decode_dict)
                                    EntryInfo.display_from_dict(
                                        entry, True, maxlen)
                                except:
                                    print line
                    return result[self.host]
                else:
                    print "Failed to retrieve dir content for", self.path, "on", self.host
                    continuing = ("Try again? Y/N [N]: ")
                    if continuing == "":
                        continuing = "N"
                    if continuing.upper() != "Y":
                        return None

    def generate_executor(self):
        '''
        horrible hack: this code is fed to salt when we feed this
        script to stdin to run it remotely, thus bypassing all
        the command line argument parsing logic

        in this case we set up for DirExaminer directly
        '''
        code = """
def executor():
    de = DirExaminer('%s', 'localhost', %d, %d, %d)
    de.run()
""" % (self.path, self.batchno, self.batchsize, self.timeout)
        return code


class LocalIgnores(object):
    '''
    retrieval and display dirs / files listed as to
    be ignored in per-user lists on local host
    '''
    def __init__(self, host, timeout, audit_type):
        self.host = host
        self.timeout = timeout
        self.audit_type = audit_type
        self.locations = audit_type + "_locations"

    def run(self, quiet=False):
        '''
        do all the work

        note that 'quiet' applies only to remotely
        run, and the same is true for returning the contents.
        maybe we want to fix that
        '''

        local_ignores = {}

        if Runner.running_locally(self.host):
            local_ignores = HomesAuditor.get_local_ignores(self.locations)
            output = json.dumps(local_ignores)
            print output
        else:
            client = LocalClientPlus()
            code = "# -*- coding: utf-8 -*-\n"
            code += self.generate_executor()
            with open(__file__, 'r') as fp_:
                code += fp_.read()
            result = client.cmd([self.host], "cmd.exec_code",
                                ["python2", code],
                                expr_form='list',
                                timeout=self.timeout)
            if self.host in result:
                input = result[self.host]
                try:
                    local_ignores = json.loads(
                        input, object_hook=JsonHelper.decode_dict)
                except:
                    print "WARNING: failed to get local ignores on host",
                    print self.host,
                    print "got this:", input
                    local_ignores = {}

            if not quiet:
                print local_ignores

            return local_ignores

    def generate_executor(self):
        code = """
def executor():
    de = LocalIgnores('localhost', %d, '%s')
    de.run()
""" % (self.timeout, self.audit_type)
        return code


class DirContents(object):
    '''
    retrieval and display directory contents on local host
    '''
    def __init__(self, path, batchno=1, batchsize=50, prettyprint=False):
        self.path = path
        self.st = None
        self.full_contents = None
        self.batch_contents = None
        self.batch_entryinfo = None
        self.batchno = batchno
        self.batchsize = batchsize
        self.prettyprint = prettyprint

    def get_dir_stats(self, path=None):
        '''
        return results of stat call on the specified dir
        '''
        if path is None:
            path = self.path
        if self.st is None:
            try:
                self.st = os.stat(self.path)
            except:
                return None
        return self.st

    def read_dir_batch(self):
        '''
        retrieve directory contents if not already cached,
        grab the specified batch of entries (counting from 1)
        if there there are fewer batches than the
        requested batch number, the batch is set to the empty list

        NOTE this is horrid, os.listdir reads the whole dir anyways
        so batching rereads the whole list and tosses everything
        we don't want
        '''
        if self.full_contents is None:
            try:
                # can be a problem for directories with hundreds
                # of thousands of entries, will we encounter that?
                self.full_contents = os.listdir(self.path)
            except:
                self.full_contents = None
                return

        if len(self.full_contents) < (self.batchno - 1) * self.batchsize:
            self.batch_contents = []
        else:
            self.batch_contents = self.full_contents[
                (self.batchno - 1) * self.batchsize: self.batchno
                * self.batchsize]

    def get_contents(self):
        if self.batch_contents is None:
            self.get_dir_stats()
            if self.st is None:
                return "dir stat failed"
            if stat.S_ISLNK(self.st.st_mode):
                return "link"
            if not stat.S_ISDIR(self.st.st_mode):
                return "not dir"
            self.read_dir_batch()
            if self.batch_contents is None:
                return "dir read failed"

        return "ok"

    @staticmethod
    def get_entryinfo(path):
        '''
        get entry info object for path, populated
        '''
        finfo = EntryInfo(path)
        finfo.produce_json()
        return finfo.json

    def get_batch_entryinfo(self):
        '''
        get entry info for the entries in self.batch_contents
        (stat, first line of contents if not binary)
        '''
        if self.batch_contents is None:
            self.batch_entryinfo = None
            return

        results = []
        for dname in self.batch_contents:
            info = DirContents.get_entryinfo(os.path.join(self.path, dname))
            if info is not None:
                results.append(info)

        self.batch_entryinfo = results

    def display_json(self, json_text):
        if not self.prettyprint:
            print json_text
            return

        try:
            item = json.loads(json_text, object_hook=JsonHelper.decode_dict)
        except:
            print json_text
            return
        output = FileInfo.format_pretty_output_from_dict(item, path_justify=50)
        print output

    def show_batch(self):
        for entry in self.batch_entryinfo:
            self.display_json(entry)


class Status(object):
    '''
    manage statuses (good, problem, etc) of files/dirs
    '''

    status_expr = r"^\s*'%s'\s*:\s*\[\s*(\],?)?\s*$"
    status_cf = {'good': ['G', re.compile(status_expr % 'good')],
                 'problem': ['P', re.compile(status_expr % 'problem')],
                 'recheck': ['R', re.compile(status_expr % 'recheck')],
                 'unreviewed': ['U', re.compile(status_expr % 'unreviewed')]}

    STATUSES = [status_cf[key][0] for key in status_cf]
    STATUS_TEXTS = [key for key in status_cf]

    @staticmethod
    def status_to_text(abbrev):
        for key in Status.status_cf:
            if Status.status_cf[key][0] == abbrev:
                return key
        return None

    @staticmethod
    def text_to_status(abbrev):
        for key in Status.status_cf:
            if key == abbrev:
                return Status.status_cf[key][0]
        return None

    @staticmethod
    def get_statuses_prompt(separator):
        return separator.join(["%s(%s)" %
                               (key, Status.status_cf[key][0])
                               for key in Status.status_cf])


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
        for s in Status.status_cf:
            result = Status.status_cf[s][1].match(line)
            if result is not None:
                if "]" in result.group(0):
                    return None, Rule.STATE_EXPECT_STATUS
                else:
                    return s, Rule.STATE_EXPECT_ENTRIES
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
    def do_add_rule(cdb, path, rtype, status, host):
        cdb.store_db_replace({'basedir': os.path.dirname(path),
                              'name': os.path.basename(path),
                              'type': rtype,
                              'status': status},
                             host)

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
    def export_rules(cdb, rules_path, host, stype=None):
        # would be nice to be able to only export some rules. whatever

        rules = Rule.get_rules(cdb, host)
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
        basedir = RuleStore.from_unicode(basedir)
        name = RuleStore.from_unicode(name)
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


class CommandLine(object):
    '''
    prompt user at the command line for actions to take on a given
    directory or file, show results
    '''

    # todo: down and up should check you really are (descending,
    # ascending path)

    def __init__(self, store_filepath, timeout, audit_type, hosts_expr=None):
        self.cdb = RuleStore(store_filepath)
        self.cdb.store_db_init(None)
        self.timeout = timeout
        self.audit_type = audit_type
        self.locations = audit_type + "_locations"
        self.hosts_expr = hosts_expr

        self.host = None
        self.today = time.strftime("%Y%m%d", time.gmtime())
        self.basedir = None
        self.current_dir = None
        self.prompt = None
        CommandLine.init_readline_hist()
        self.hostlist = None
        self.dirs_problem = None
        self.dirs_skipped = None
        self.current_dir_contents_list = None
        self.current_dir_contents_dict = None
        # this is arbitrary, can tweak it later
        # how many levels down we keep in our list of
        # top-level dirs from which the user can start
        # their interactive session
        self.max_depth_top_level = 3

        self.choices = None
        self.choice_default = None

        self.filtertype = 'all'

        # fixme completely wrong
        self.batchno = 1

        self.ignored = None
        self.local_ignores = None

        self.perhost_ignores = {}
        self.perhost_rules_from_file = None
        self.get_perhostcf_from_file()
        self.perhost_ignores_from_rules = {}
        self.get_perhost_ignores_from_rules()

    def get_perhost_ignores_from_rules(self, hosts=None):
        if hosts is None:
            hosts = self.cdb.store_db_list_all_hosts()
        for host in hosts:
            self.perhost_rules_from_store = Rule.get_rules(
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

    def get_perhostcf_from_file(self):
        if os.path.exists('audit_files_perhost_config.py'):
            try:
                self.perhost_rules_from_file = runpy.run_path(
                    'audit_files_perhost_config.py')['perhostcf']
            except:
                self.perhost_rules_from_file = None

        if self.perhost_rules_from_file is not None:
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

    @staticmethod
    def init_readline_hist():
        readline.parse_and_bind("tab: complete")
        histfile = os.path.join(os.path.expanduser("~"), ".audit_hist")
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        atexit.register(readline.write_history_file, histfile)
        # also fix up delims so we don't have annoying dir elt behavior
        delims = readline.get_completer_delims()
        delims = delims.replace("/", "")
        readline.set_completer_delims(delims)

    def save_history(self, histfile):
        readline.write_history_file(histfile)

    def host_completion(self, text, state):
        if text == "":
            matches = self.hostlist
        else:
            matches = [h for h in self.hostlist
                       if h.startswith(text)]
        if len(matches) > 1 and state == 0:
            for m in matches:
                print m,
            print

        try:
            return matches[state]
        except IndexError:
            return None

    def prompt_for_host(self):
        '''
        prompt user for host in self.hostlist,
        with tab completion
        '''
        readline.set_completer(self.host_completion)
        while True:
            host_todo = raw_input(
                "Host on which to examine dirs/files (blank to exit): ")
            host_todo = host_todo.strip()
            if host_todo == "":
                return None
            if host_todo in self.hostlist:
                return host_todo
            else:
                print "Please choose one of the following hosts:"
                CommandLine.print_columns(self.hostlist, 4)

    def dir_completion(self, text, state):
        if self.current_dir is None:
            dirs_problem_to_depth = [CommandLine.get_path_prefix(
                d, self.max_depth_top_level) for d in self.dirs_problem]
            dirs_skipped = [s for s in self.dirs_skipped
                            if s not in dirs_problem_to_depth]
            relevant_dirs = (sorted(list(set(dirs_problem_to_depth)))
                             + sorted(list(set(dirs_skipped))))
        else:
            if self.current_dir_contents_list is None:
                self.get_dir_contents(self.current_dir, self.batchno)
            relevant_dirs = sorted([s for s in self.current_dir_contents_dict
                                    if self.current_dir_contents_dict[s]['type'] == 'dir'])
        if text == "":
            matches = relevant_dirs
        else:
            depth = text.count(os.path.sep)
            # how many path elts do we have in the text, show
            # matches for basedir of it plus next elt
            matches = ([d for d in relevant_dirs
                        if d.startswith(text) and
                        d.count(os.path.sep) == depth])
        try:
            return matches[state]
        except IndexError:
            return None

    def dir_entries_completion(self, text, state):
        if not self.current_dir_contents_list:
            self.get_dir_contents(self.current_dir, self.batchno)
        entries = sorted([s for s in self.current_dir_contents_dict
                          if (self.current_dir_contents_dict[s]['type'] == 'file' or
                              self.current_dir_contents_dict[s]['type'] == 'dir')])
        if text == "":
            matches = entries
        else:
            depth = text.count(os.path.sep)
            # how many path elts do we have in the text, show
            # matches for basedir of it plus next elt
            matches = ([d for d in entries
                        if d.startswith(text) and
                        d.count(os.path.sep) == depth])
        try:
            return matches[state]
        except IndexError:
            return None

    def prompt_for_dir(self):
        '''
        prompt user for host in self.hostlist,
        with tab completion
        '''

        readline.set_completer(self.dir_completion)
        dir_todo = raw_input("Directory (blank to exit): ")
        dir_todo = dir_todo.strip()
        if dir_todo == "":
            return None
        else:
            return dir_todo

    def choices_completion(self, text, state):
        matches = self.choices
        if text == "":
            matches = [self.choice_default]
        try:
            return matches[state]
        except IndexError:
            return None

    @staticmethod
    def get_path_prefix(path, depth):
        if path is None:
            return path
        if path.count(os.path.sep) < depth:
            return path
        fields = path.split(os.path.sep)
        return os.path.sep.join(fields[:depth + 1])

    @staticmethod
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

    @staticmethod
    def print_columns(items, cols):
        num_rows = len(items) / cols
        extra = len(items) % cols
        if extra:
            num_rows = num_rows + 1

        max_len = {}
        for col in range(0, cols):
            max_len[col] = 0

        for row in range(0, num_rows):
            for col in range(0, cols):
                try:
                    text = items[row + num_rows * col]
                except IndexError:
                    continue
                try:
                    count = len(unicode(text, 'utf-8'))
                except:
                    count = len(text)
                if len(text) > max_len[col]:
                    max_len[col] = len(text)

        for row in range(0, num_rows):
            for col in range(0, cols):
                try:
                    # fixme ljust probably gets this wrong for
                    # text that's really multibyte chars
                    print items[row + num_rows * col].ljust(max_len[col]),
                except IndexError:
                    pass
            print

    def do_one_host(self, host, report):
        self.set_host(host)
        if not Runner.running_locally(self.host):
            self.get_perhost_ignores_from_rules([host])

        if Runner.running_locally(self.host):
            self.dirs_problem, self.dirs_skipped = CommandLine.get_dirs_toexamine(report)
        else:
            if host not in report:
                self.dirs_problem = None
                self.dirs_skipped = None
            else:
                self.dirs_problem, self.dirs_skipped = CommandLine.get_dirs_toexamine(report[host])
        if self.dirs_problem is None and self.dirs_skipped is None:
            print "No report available from this host"
        elif len(self.dirs_problem) == 0 and len(self.dirs_skipped) == 0:
            print "No problem dirs and no skipped dirs on this host"
        else:
            dirs_problem_to_depth = [CommandLine.get_path_prefix(
                d, self.max_depth_top_level)
                for d in self.dirs_problem]
            dirs_skipped = [s for s in self.dirs_skipped
                            if s not in dirs_problem_to_depth]
            relevant_dirs = (sorted(list(set(dirs_problem_to_depth)))
                             + sorted(list(set(dirs_skipped))))
            while True:
                dir_todo = self.prompt_for_dir()
                if dir_todo is None:
                    print "Done with this host"
                    break
                elif dir_todo not in relevant_dirs:
                    print "Please choose one of the following directories:"
                    # fixme another arbitrary setting
                    CommandLine.print_columns(relevant_dirs, 5)
                else:
                    self.basedir = None
                    self.current_dir = None
                    self.do_one_directory(dir_todo)

    def run(self, report, ignored):
        '''
        call with full report output (not summary) across
        hosts, this will permit the user to examine
        directories and files of specified hosts and
        add/update rules for those dirs and files
        '''
        self.ignored = ignored
        if Runner.running_locally(self.hosts_expr):
            host_todo = "localhost"
            self.do_one_host(host_todo, report)
            return

        self.hostlist = report.keys()
        while True:
            host_todo = self.prompt_for_host()
            if host_todo is None:
                print "exiting at user request"
                break
            else:
                local_ign = LocalIgnores(host_todo, self.timeout, self.audit_type)
                self.local_ignores = local_ign.run(True)
                local_ignored_dirs, local_ignored_files = HomesAuditor.process_local_ignores(
                    self.local_ignores, self.ignored)
                self.do_one_host(host_todo, report)

    def set_host(self, host):
        self.host = host

    def do_one_directory(self, path):
        '''
        given a list which contains absolute paths for the
        subdirectories / files of a given directory, (we don't
        go more than one level down, it's likely to be too much),
        ask the user what status to give this directory, and
        show the user information for each contained dir/file if
        desired, as well as info about the directory
        '''
        while True:
            todo = self.get_do_command(path)
            if todo is None:
                break

    def get_do_command(self, path):
        command = self.show_menu(path, 'top')
        return self.do_command(command, 'top', path)

    def show_menu(self, path, level):
        if level == 'top':
            self.choices = ['S', 'E', 'I', 'F', 'R', 'Q']
            self.choice_default = 'S'
            readline.set_completer(self.choices_completion)
            command = raw_input("S(set status)/E(examine directory)/"
                                "Filter directory listings/"
                                "I(ignore)/R(manage rules)/Q(quit menu) [S]: ")
            command = command.strip()
            if command == "":
                command = self.choice_default
        elif level == 'status':
            self.choices = Status.STATUSES + ['Q']
            self.choice_default = Status.text_to_status('good')
            readline.set_completer(self.choices_completion)
            statuses_text = Status.get_statuses_prompt(", ")
            command = raw_input(statuses_text + ", Q(quit status menu) [%s]: "
                                % self.choice_default)
            command = command.strip()
            if command == "":
                command = self.choice_default
            elif command == 'Q' or command == 'q':
                level = 'top'
        elif level == 'examine':
            self.choices = ['D', 'U', 'E', 'F', 'C', 'R', 'M', 'Q']
            self.choice_default = 'E'
            readline.set_completer(self.choices_completion)
            command = raw_input("D(down a level)/U(up a level)/E(show entries)/"
                                "C(show contents of file)/R(show rules)/"
                                "F(filter directory listings/"
                                "M(mark file(s))/Q(quit examine menu) [E]: ")
            command = command.strip()
            if command == "":
                command = self.choice_default
            elif command == 'Q' or command == 'q':
                level = 'top'
        elif level == 'rule':
            self.choices = ['S', 'C', 'A', 'R', 'E', 'I', 'Q']
            self.choice_default = 'D'
            readline.set_completer(self.choices_completion)
            command = raw_input("S(show all rules of type)/D(show rules covering dir)/"
                                "C(show rules covering dir contents)/"
                                "A(add rule to rules store)/"
                                "R(remove rule from rules store/"
                                "E(export rules from store to file)/"
                                "I(import rules from file to store)/Q(quit rule menu) [D]: ")
            command = command.strip()
            if command == "":
                command = self.choice_default
            elif command == 'Q' or command == 'q':
                level = 'top'
        else:
            command = None
        return command

    @staticmethod
    def show_help(level):
        if level == 'status':
            print """Status must be one of the following:
            P  (the directory or file may contain sensitive information)
            G  (the directory or file is known to be ok and should remain so)
            R  (the directory or file is known to be ok but entries
                must be rechecked on next run)
            U  (the file or directory has not been checked, status unknown)
            Q  (quit this level of the menu)"""
        elif level == 'top':
            print """Command must be one of the following:
            S  set the status for the directory
            E  examine the directory
            F set filter for listing directory contents
            I  ignore this directory or file for now
            R  show rules for all dirs/files
            Q  quit the menu"""
        elif level == 'examine':
            print """Command must be one of the following:
            D descend the directory tree one level (user will be prompted for subdir)
            U ascend the directory tree one level (not higher than base of tree)
            E show information on entries in directory
            F set filter for listing directory contents
            C show first few lines of contents of file in directory
            R  show rules covering current directory
            M  mark file(s) as ok (user will be prompted for filename expr)
            Q  quit the menu"""
        elif level == 'rule':
            print """Command must be one of the following:
            S show all rules for this host
            D show all rules covering the current directory
            C show all rules covering current directory contents
            A add rule to rules store
            R remove rule from rules store
            I import rules from file (overrides dups, won't remove other rules)
            E export rules to file
            Q quit the menu"""
        else:
            print "unknown help level requested,", level

    def get_dir_contents(self, path, batchno):
        # via salt get the directory contents for the first N = 1000
        # entries, unsorted.

        # fixme batchno? batchno should increment too
        # for now more than 1000 entries in a dir = we silently toss them
        direxamin = DirExaminer(path, self.host, batchno, 1000, self.timeout, prettyprint=False)
        contents = direxamin.run(True)
        if contents is not None:
            contents = contents.split("\n")

        self.current_dir_contents_list = []
        self.current_dir_contents_dict = {}

        if contents is None:
            return

        for item in contents:
            try:
                result = json.loads(item, object_hook=JsonHelper.decode_dict)
                self.current_dir_contents_list.append(result)
                self.current_dir_contents_dict[result['path']] = result
            except:
                print "WARNING: problem getting dir contents, retrieved", item
#                exc_type, exc_value, exc_traceback = sys.exc_info()
#                sys.stderr.write(repr(traceback.format_exception(
#                    exc_type, exc_value, exc_traceback)))

    def get_file_contents(self, path):
        # get 20 lines and hope that's enough for the user to evaluate
        # fixme the number of lines should be configurable
        fileexamin = FileExaminer(path, self.host, 20, self.timeout, quiet=True)
        contents = fileexamin.run()
        return contents

    @staticmethod
    def show_pager(current_page, num_items, num_per_page):
        readline.set_completer(None)
        while True:
            to_show = raw_input("P(prev)/N(next)/F(first)/"
                                "L(last)/<num>(go to page num)/Q(quit) [N]: ")
            to_show = to_show.strip()
            if to_show == "":
                to_show = 'N'

            if to_show == 'P' or to_show == 'p':
                # prev page
                if current_page > 1:
                    return current_page - 1
                else:
                    return current_page

            elif to_show == 'N' or to_show == 'n':
                # next page
                num_pages = num_items / num_per_page
                if num_items % num_per_page:
                    num_pages += 1
                if current_page < num_pages:
                    return current_page + 1
                else:
                    return current_page

            elif to_show == 'F' or to_show == 'f':
                # first page
                return 1

            elif to_show == 'L' or 'to_show' == 'l':
                # last page
                num_pages = num_items / num_per_page
                if num_items % num_per_page:
                    num_pages += 1
                return num_pages

            elif to_show.isdigit():
                desired_page = int(to_show)
                num_pages = num_items / num_per_page
                if num_items % num_per_page:
                    num_pages += 1

                if desired_page < 1:
                    return 1
                elif desired_page > num_pages:
                    return num_pages
                else:
                    return desired_page

            elif to_show == 'Q' or to_show == 'q':
                return None
            else:
                print "unknown option"

    def get_basedir_from_path(self, path):
        for location in Config.cf[self.locations]:
            if path == location or path.startswith(location + os.path.sep):
                return location
        # fixme is this really the right fallback? check it
        return '/'

    def entry_is_not_ignored(self, path, entrytype):
        basedir = self.get_basedir_from_path(path)
        if self.audit_type == 'logs' and entrytype == 'file':
            path = LogsAuditor.normalize(path)

        if entrytype == 'file':
            if FilesAuditor.file_is_ignored(path, basedir, self.ignored):
                return False

            # check perhost file
            if self.host in self.perhost_ignores:
                if FilesAuditor.file_is_ignored(
                        path, basedir,
                        self.perhost_ignores[self.host]):
                    return False

            # check perhost rules
            if self.host in self.perhost_ignores_from_rules:
                if FilesAuditor.file_is_ignored(
                        path, basedir,
                        self.perhost_ignores_from_rules[self.host]):
                    return False

        elif entrytype == 'dir':
            if FilesAuditor.dir_is_ignored(path, self.ignored):
                return False

            # check perhost file
            if self.host in self.perhost_ignores:
                if FilesAuditor.dir_is_ignored(
                        path, self.perhost_ignores[self.host]):
                    return False

            # check perhost rules
            if self.host in self.perhost_ignores_from_rules:
                if FilesAuditor.dir_is_ignored(
                        path, self.perhost_ignores_from_rules[self.host]):
                    return False
        else:
            # unknown type, I guess we skip it then
            return False

        return True

    def show_dir_contents(self, path, batchno):
        self.get_dir_contents(path, batchno)

        # fixme this 50 is pretty arbitrary oh well
        justify = 50

        keys = self.current_dir_contents_dict.keys()
        if self.filtertype == 'file':
            items = (sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'file'))
        elif self.filtertype == 'dir':
            items = (sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'dir'))
        elif self.filtertype == 'all':
            items = sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'dir')
            items = items + sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'file')
        elif self.filtertype == 'check':
            items = sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'dir'
                and self.entry_is_not_ignored(
                    self.current_dir_contents_dict[item]['path'],
                    self.current_dir_contents_dict[item]['type']))
            items = items + sorted(
                item for item in keys
                if self.current_dir_contents_dict[item]['type'] == 'file'
                and self.entry_is_not_ignored(
                    self.current_dir_contents_dict[item]['path'],
                    self.current_dir_contents_dict[item]['type']))

        page = 1
        num_per_page = 50  # another arbitrary value
        num_items = len(items)
        num_in_last_page = num_items % num_per_page
        num_pages = num_items / num_per_page
        if num_in_last_page:
            num_pages += 1

        num_to_show = num_per_page
        if num_pages == 1:
            num_to_show = num_in_last_page

        while True:
            for item in items[(page - 1) * num_per_page:
                              (page - 1) * num_per_page + num_to_show]:
                if not item:
                    # fixme why do we have an empty item I wonder
                    continue
                try:
                    result = FileInfo.format_pretty_output_from_dict(
                        self.current_dir_contents_dict[item], path_justify=justify)
                except:
                    print "item is", item
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    sys.stderr.write(repr(traceback.format_exception(
                        exc_type, exc_value, exc_traceback)))
                    result = None
                if result is not None:
                    print result

            if num_pages == 1:
                break

            page = CommandLine.show_pager(page, num_items, num_per_page)
            if page is None:
                return
            elif page == num_pages:
                num_to_show = num_in_last_page
            else:
                num_to_show = num_per_page

    # fixme use this (also make it have first + last, more helpful prolly)
    def set_prompt(self):
        if self.current_dir is None:
            self.prompt = "> "
        elif len(self.current_dir) < 10:
            self.prompt = self.current_dir + ">"
        else:
            self.prompt = "..." + self.current_dir[-7:] + ">"

    def get_entries_from_wildcard(self, file_expr):
        '''
        get entries from current_dir that match the
        expression
        '''
        # fixme that dang batchno, what a bad idea it was
        if self.current_dir_contents_list is None:
            self.get_dir_contents(self.current_dir, 1)
        # one wildcard only, them's the breaks
        if '*' in file_expr:
            start, end = file_expr.split('*', 1)
            return [c for c in self.current_dir_contents_dict
                    if (c.startswith(start) and
                        c.endswith(end) and
                        len(c) >= len(start) + len(end))]
        elif file_expr in self.current_dir_contents_dict:
            return [file_expr]
        else:
            return []

    def do_mark(self):
        readline.set_completer(self.dir_entries_completion)
        file_expr = raw_input("file or dirname expression (empty to quit): ")
        file_expr = file_expr.strip()
        if file_expr == '':
            return True
        if file_expr[-1] == os.path.sep:
            file_expr = file_expr[:-1]
        if '*' in file_expr:
            entries_todo = self.get_entries_from_wildcard(file_expr)
        else:
            entries_todo = [file_expr]
        if not self.current_dir_contents_list:
            self.get_dir_contents(self.current_dir, self.batchno)
            if not self.current_dir_contents_list:
                print 'failed to get directory contents for', self.current_dir
                print 'marking dirs/files regardless'
        for entry in entries_todo:
            if entry not in self.current_dir_contents_dict:
                print 'skipping %s, not in current dir listing' % entry
                print self.current_dir_contents_dict
                continue
            filetype = Rule.entrytype_to_text(
                self.current_dir_contents_dict[entry]['type'])
            if filetype == 'link':
                print 'No need to mark', file_expr, 'links are always skipped'
                continue
            elif filetype != 'dir' and filetype != 'file':
                print 'Not a dir or regular file, no need to mark, skipping'
                continue
            status = Status.text_to_status('good')
            Rule.do_add_rule(self.cdb, file_expr, filetype, status, self.host)
        return True

    def check_rules_path(self, rules_path):
        # sanity check on the path, let's not read/write
        # into/from anything in the world

        # fixme write this
        return True

    def do_rule(self, command):
        if command == 'A' or command == 'a':
            # fixme need different completer here I think, that
            # completes relative to self.current_dir
            readline.set_completer(None)
            path = raw_input("path or wildcard expr in rule (empty to quit): ")
            path = path.strip()
            if path == '':
                return True
            self.choices = Status.STATUSES + ['Q']
            self.choice_default = Status.text_to_status('good')
            readline.set_completer(self.choices_completion)
            while True:
                statuses_text = Status.get_statuses_prompt(", ")
                status = raw_input(statuses_text + " Q(quit)) [%s]: " %
                                   self.choice_default)
                status = status.strip()
                if status == "":
                    status = self.choice_default
                if status[0].upper() in Status.STATUSES:
                    status = status[0].upper()
                    break
                elif status == 'q' or status == 'Q':
                    return None
                else:
                    print "Unknown status type"
                    continue

            # fixme should check that any wildcard is only one and only
            # in the last component... someday

            if path[0] != os.path.sep:
                path = os.path.join(self.current_dir, path)
            if path[-1] == os.path.sep:
                path = path[:-1]
                filetype = Rule.text_to_entrytype('dir')
            else:
                filetype = Rule.text_to_entrytype('file')

            Rule.do_add_rule(self.cdb, path, filetype, status, self.host)
            # update the ignores list since we have a new rule
            self.perhost_ignores_from_rules = {}
            self.get_perhost_ignores_from_rules([self.host])
            return True
        elif command == 'S' or command == 's':
            self.choices = ['A'] + Status.STATUSES + ['Q']
            self.choice_default = Status.text_to_status('problem')
            readline.set_completer(self.choices_completion)
            while True:
                statuses_text = Status.get_statuses_prompt(", ")
                status = raw_input("status type A(all), " + statuses_text +
                                   ", Q(quit)) [%s]: " % self.choice_default)
                status = status.strip()
                if status == "":
                    status = self.choice_default

                if status == 'q' or status == 'Q':
                    return None
                elif status[0].upper() not in ['A'] + Status.STATUSES:
                    print "Unknown status type"
                    continue

                readline.set_completer(None)
                prefix = raw_input("starting with prefix? [/]: ")
                prefix = prefix.strip()
                if prefix == "":
                    prefix = "/"
                if status == 'a' or status == 'A':
                    Rule.show_rules(self.cdb, self.host, prefix=prefix)
                    return True
                elif status[0].upper() in Status.STATUSES:
                    Rule.show_rules(self.cdb, self.host, status[0].upper(),
                                    prefix=prefix)
                    return True
        elif command == 'D' or command == 'd':
            if not self.current_dir_contents_list:
                self.get_dir_contents(self.current_dir, self.batchno)
            Rule.get_rules_for_path(self.cdb, self.current_dir, self.host)
            return True
        elif command == 'C' or command == 'c':
            if not self.current_dir_contents_list:
                self.get_dir_contents(self.current_dir, self.batchno)
            Rule.get_rules_for_entries(self.cdb, self.current_dir,
                                       self.current_dir_contents_dict,
                                       self.host)
            return True
        elif command == 'R' or command == 'r':
            # fixme need different completer here I think, that
            # completes relative to self.current_dir
            readline.set_completer(None)
            path = raw_input("path or wildcard expr in rule (empty to quit): ")
            path = path.strip()
            if path == '':
                return True
            elif path[0] != os.path.sep:
                path = os.path.join(self.current_dir, path)
            if path[-1] == os.path.sep:
                path = path[:-1]
            Rule.do_remove_rule(self.cdb, path, self.host)
            # update the ignores list since we removed a rule
            self.perhost_ignores_from_rules = {}
            self.get_perhost_ignores_from_rules([self.host])
            return True
        elif command == 'I' or command == 'i':
            readline.set_completer(None)
            rules_path = raw_input("full path to rules file (empty to quit): ")
            rules_path = rules_path.strip()
            if rules_path == '':
                return True
            if not self.check_rules_path(rules_path):
                print "bad rules file path specified, aborting"
            else:
                Rule.import_rules(self.cdb, rules_path, self.host)
            return True
        elif command == 'E' or command == 'e':
            readline.set_completer(None)
            rules_path = raw_input("full path to rules file (empty to quit): ")
            rules_path = rules_path.strip()
            if rules_path == '':
                return True
            if not self.check_rules_path(rules_path):
                print "bad rules file path specified, aborting"
            else:
                Rule.export_rules(self.cdb, rules_path, self.host)
            return True
        elif command == 'Q' or command == 'q':
            print "quitting this level"
            return None
        else:
            CommandLine.show_help('rule')
            return True

    def do_file_contents(self):
        # fixme need a different completer here... meh
        readline.set_completer(None)
        filename = raw_input("filename (empty to quit): ")
        filename = filename.strip()
        if filename == '':
            return
        if filename[0] != os.path.sep:
            filename = os.path.join(self.current_dir, filename)
        contents = self.get_file_contents(filename)
        if contents is not None:
            print contents
        else:
            print "failed to get contents of file"

    def do_filter(self):
        self.choices = ['A', 'D', 'F', 'C', 'Q']
        self.choice_default = 'C'
        readline.set_completer(self.choices_completion)
        while True:
            filtertype = raw_input("filter A(all), D(directories only),"
                                   " F(files only),"
                                   " C(Entries checked (not ignored),"
                                   " Q(quit)) [?]: ")
            filtertype = filtertype.strip()
            if filtertype == "":
                filtertype = self.choice_default
            if filtertype == 'a' or filtertype == 'A':
                self.filtertype = 'all'
                return True
            elif filtertype == 'D' or filtertype == 'd':
                self.filtertype = 'dir'
                return True
            elif filtertype == 'F' or filtertype == 'f':
                self.filtertype = 'file'
                return True
            elif filtertype == 'C' or filtertype == 'c':
                self.filtertype = 'check'
                return True
            elif filtertype == 'q' or filtertype == 'Q':
                return None
            else:
                print "Unknown filter type"
                continue

    def do_examine(self, command):
        if command == 'D' or command == 'd':
            while True:
                # prompt user for dir to descend
                readline.set_completer(self.dir_completion)
                directory = raw_input("directory name (empty to quit): ")
                directory = directory.strip()
                if directory == '':
                    return command
                if directory[-1] == os.path.sep:
                    directory = directory[:-1]
                if (directory[0] == '/' and
                        not directory.startswith(self.current_dir +
                                                 os.path.sep)):
                    print 'New directory is not a subdirectory of',
                    print self.current_dir, "skipping"
                else:
                    self.current_dir = os.path.join(self.current_dir,
                                                    directory)
                    self.current_dir_contents_list = None
                    self.current_dir_contents_dict = None
                    self.set_prompt()
                    print 'Now at', self.current_dir
                    return True
        elif command == 'U' or command == 'u':
            if self.current_dir != self.basedir:
                self.current_dir = os.path.dirname(self.current_dir)
                self.current_dir_contents_list = None
                self.current_dir_contents_dict = None
                self.set_prompt()
                print 'Now at', self.current_dir
            else:
                print 'Already at top', self.current_dir
            return True
        elif command == 'E' or command == 'e':
            self.show_dir_contents(self.current_dir, 1)
            return True
        elif command == 'C' or command == 'c':
            self.do_file_contents()
            return True
        elif command == 'F' or command == 'f':
            self.do_filter()
            return True
        elif command == 'R' or command == 'r':
            continuing = True
            while continuing:
                command = self.show_menu(self.current_dir, 'rule')
                continuing = self.do_command(command, 'rule', self.current_dir)
            return True
        elif command == 'M' or command == 'm':
            return self.do_mark()
        elif command == 'Q' or command == 'q' or command == '':
            print "quitting this level"
            return None
        else:
            CommandLine.show_help('examine')
            return True

    def do_top(self, command, dir_path):
        if command == 'S' or command == 's':
            continuing = True
            while continuing:
                command = self.show_menu(dir_path, 'status')
                continuing = self.do_command(command, 'status', dir_path)
            return True
        elif command == 'E' or command == 'e':
            self.show_dir_contents(self.current_dir, 1)
            continuing = True
            while continuing:
                # fixme this should let the user page through batches,
                # not use '1' every time
                command = self.show_menu(self.current_dir, 'examine')
                continuing = self.do_command(command, 'examine',
                                             self.current_dir)
            return True
        elif command == 'F' or command == 'f':
            self.do_filter()
            return True
        elif command == 'I' or command == 'i':
            # do nothing
            return command
        elif command == 'R' or command == 'r':
            continuing = True
            while continuing:
                command = self.show_menu(self.current_dir, 'rule')
                continuing = self.do_command(command, 'rule', self.current_dir)
            return True
        elif command == 'Q' or command == 'q':
            return None
        else:
            CommandLine.show_help('top')
            return True

    def do_command(self, command, level, dir_path):
        if self.basedir is None:
            self.basedir = dir_path
        if self.current_dir is None:
            self.current_dir = dir_path

        if command is None:
            return

        if level == 'top':
            return self.do_top(command, dir_path)
        elif level == 'status':
            if command in Status.STATUSES:
                # this option is invoked on a directory so
                # type is dir every time
                Rule.do_add_rule(self.cdb, dir_path,
                                 Rule.text_to_entrytype('dir'),
                                 command, self.host)
                return None
            elif command == 'Q' or command == 'q':
                return None
            else:
                CommandLine.show_help(level)
                return True
        elif level == 'examine':
            return self.do_examine(command)
        elif level == 'rule':
            return self.do_rule(command)
        else:
            return None


class EntryInfo(object):
    '''
    minimum info about a directory entry
    '''
    def __init__(self, path):
        self.path = path
        self.st = None
        self.start_content = None
        self.is_binary = None
        self.entry_dict = None

    def get_stats(self):
        if self.st is None:
            try:
                self.st = os.stat(self.path)
            except:
                return None
        return self.st

    def get_mtime_formatted(self):
        '''
        get the mtime of the file if not already loaded,
        and return it, or None on error
        '''
        self.get_stats()
        if self.st is not None:
            return time.ctime(self.st.st_mtime)
        else:
            return ""

    def get_start_content(self, num_lines=1):
        '''
        get up to the first 1000 characters or the first line from the file
        if not already loaded, and return them, or None on error
        this also sets is_empty to the correct value, as a side effect,
        if not already set
        '''
        firstline = None
        if re.search(r'\.gz(\.[0-9]+)?$', self.path):
            try:
                filep = gzip.open(self.path, "rb")
                lines = ""
                for count in range(0, num_lines):
                    line = filep.readline(1000)
                    if line == "":
                        break
                    else:
                        if firstline is None:
                            firstline = line
                        lines += line
                filep.close()
            except:
                return None
        else:
            try:
                filep = open(self.path, "r")
                lines = ""
                firstline = None
                for count in range(0, num_lines):
                    line = filep.readline(1000)
                    if line == "":
                        break
                    else:
                        if firstline is None:
                            firstline = line
                        lines += line
                filep.close()
            except:
                return None

        if lines == '':
            self.is_empty = True
            firstline = "EMPTY"
        else:
            self.is_empty = False

        # and for binary then...?
        if EntryInfo.check_text_binary(lines):
            firstline = "BINARY"

        self.entrydate = EntryInfo.get_date_fromtext(firstline)

        self.start_content = lines
        return self.start_content

    @staticmethod
    def check_text_binary(content):
        textchars = (''.join(map(chr, [7, 8, 9, 10, 12, 13, 27] +
                                 range(0x20, 0x100))))
        try:
            is_binary = bool(content.translate(None, textchars))
        except:
            return None
        return is_binary

    def get_is_binary(self, num_lines=1):
        '''
        decide if file is binary or not, if not already checked
        returns True if binary, False if not, None on error
        this looks inside of gz and bz2 compressed files to determine
        if that content is binary or not.
        expect this method to be 'mostly right', not 100%.
        this also sets is_empty as a side effect, if not already set
        '''
        if self.is_binary is None:
            self.get_start_content(num_lines)
        self.is_binary = EntryInfo.check_text_binary(self.start_content)
        return self.is_binary

    def get_owner(self):
        '''
        get file owner if not already loaded, and return it, or -1 on error
        '''
        self.get_stats()
        if self.st is not None:
            return self.st.st_uid
        else:
            return -1

    def load_file_info(self):
        self.get_stats()
        self.get_start_content()
        self.get_is_binary()

    def produce_dict(self):
        self.load_file_info()
        try:
            self.entry_dict = {}
            self.entry_dict['path'] = self.path
            self.entry_dict['owner'] = self.get_owner()
            self.entry_dict['size'] = self.st[stat.ST_SIZE]
            self.entry_dict['mtime'] = self.get_mtime_formatted()
            if stat.S_ISLNK(self.st.st_mode):
                self.entry_dict['type'] = 'link'
            elif stat.S_ISDIR(self.st.st_mode):
                self.entry_dict['type'] = 'dir'
            elif stat.S_ISREG(self.st.st_mode):
                self.entry_dict['type'] = 'file'
            else:
                self.entry_dict['type'] = 'unknown'

            if self.start_content is not None:
                self.entry_dict['content'] = self.start_content
        except:
            self.entry_dict = {}

    def produce_json(self, entry_dict=None):
        self.json = None
        if entry_dict is None:
            self.produce_dict()
            entry_dict = self.entry_dict
        try:
            self.json = json.dumps(entry_dict)
        except:
            if 'content' in entry_dict:
                entry_dict['content'] = 'UNKNOWN (probably binary)'
                try:
                    self.json = json.dumps(entry_dict)
                except:
                    print 'WARNING: failed to json dump', entry_dict['path']
                    return None
            else:
                print 'WARNING: failed to json dump', entry_dict['path']
                return None
        return self.json

    @staticmethod
    def get_date_fromtext(text):
        '''
        given a text string look for the first date string in there
        of arbitrary format
        this is very sketchy, not at all guaranteed to work, and
        especially not in fancy locales
        '''

        current_year = str(datetime.datetime.now().year)
        # formats actually seen in log files:

        datecheck = {
            # May  5 03:31:02
            '%b %d %H:%M:%S ?%Y':
            [r'[A-Z][a-z]{2}\s+[0-9][0-9]?\s[0-9]{2}:[0-9]{2}:[0-9]{2}(?!\s+[0-9]{4})',
             ' ?' + current_year],
            # Jan 15 12:53:26 2014
            '%b %d %H:%M:%S %Y':
            [r'[A-Z][a-z]{2}\s+[0-9][0-9]?\s[0-9]{2}:[0-9]{2}:[0-9]{2}\s[0-9]{4}', ''],
            # 2013-03-08 04:10:33
            '%Y-%m-%d %H:%M:%S':
            [r'[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}', ''],
            # 130312 09:30:58
            '%y%m%d %H:%M:%S':
            [r'[0-9]{6}\s[0-9]{2}:[0-9]{2}:[0-9]{2}', ''],
            # 10/Feb/2014:03:52:38 +0200
            '%d/%b/%Y:%H:%M:%S':
            [r'[0-9]{2}/[A-Z][a-z]{2}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2}', '']
        }
        if (text is None or text == 'BINARY' or text == 'EMPTY'
                or text == 'UNAVAILABLE' or text == ''):
            return None

        for date_format in datecheck:
            result = re.search(datecheck[date_format][0], text)
            if result:
                try:
                    seconds = calendar.timegm(time.strptime(
                        result.group(0) + datecheck[date_format][1], date_format))
                except:
                    continue
                return seconds

        # Mar  8 03:51:00.928699
        # [A-Z][a-z]{2}\s+[0-9][0-9]?\s[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+
        # 2013-03-11 09:40:24.358+0000
        # [0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+\+[0-9]{4}
        # 2013-07-23 14:18:15,555
        # [0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]+
        # covered by the above

        # failed to find date
        return None

    @staticmethod
    def display_from_dict(item, show_content=False, path_justify=None):
        if path_justify is None:
            path_justify = 50  # very arbitrary, whatever
        print ("file:%s owner:%s size:%s mod:%s type:%s"
               % (item['path'].ljust(path_justify),
                  str(item['owner']).ljust(5),
                  str(item['size']).ljust(10), item['mtime'],
                  item['type']))
        if show_content and 'content' in item:
            print "    content:%s" % item['content'],
            if item['content'][-1] != '\n':
                print


class FileInfo(EntryInfo):
    '''
    maintain and provide information (stat, filetype, other)
    about a file
    '''
    def __init__(self, path, magic, statinfo=None):
        '''
        constructor
        args: full path to the file, magic object
        for determining file type
        '''
        super(FileInfo, self).__init__(path)
        self.name = os.path.basename(self.path)
        self.st = statinfo
        self.filetype = None
        self.is_empty = None
        self.is_open = None
        self.age = None
        self.is_old = None
        self.entrydate = None
        self.magic = magic

    def get_ctime(self):
        '''
        get the ctime of the file if not already loaded,
        and return it, or None on error
        '''
        self.get_stats()
        if self.st is not None:
            return self.st.st_ctime
        else:
            return None

    def get_mtime(self):
        '''
        get the mtime of the file if not already loaded,
        and return it, or None on error
        '''
        self.get_stats()
        if self.st is not None:
            return self.st.st_mtime
        else:
            return None

    @staticmethod
    def get_time_formatted(time_raw):
        '''
        format unix time to a printable string
        and return it, or the empty string on error
        '''
        if time_raw is None:
            return ""
        else:
            return time.ctime(time_raw)

    def get_ctime_formatted(self):
        '''
        get the ctime of the file in a printable string
        and return it, or the empty string on error
        '''
        return FileInfo.get_time_formatted(self.get_ctime)

    def get_mtime_formatted(self):
        '''
        get the mtime of the file in a printable string
        and return it, or the empty string on error
        '''
        return FileInfo.get_time_formatted(self.get_mtime)

    def get_filetype(self):
        '''
        get the filetype via libmagic, if not alreaded loaded,
        and return it, or the empty string on error
        '''
        if self.filetype is None:
            try:
                # fixme maybe use the content buffer instead for this?
                self.filetype = self.magic.file(self.path)
            except:
                self.filetype = ""
        return self.filetype

    def isdir(self):
        if self.filetype == 'dir':
            return True
        else:
            return False

    def get_is_empty(self):
        if self.is_empty is None:
            self.get_start_content()
        return self.is_empty

    def get_is_open(self, open_files=None):
        if open_files is None:
            open_files = []
        if self.is_open is None:
            if self.path in open_files:
                self.is_open = True
            else:
                self.is_open = False
        return self.is_open

    def get_age(self, from_time=None):
        if self.age is None:
            if from_time is None:
                return self.age

            self.get_ctime()
            self.get_mtime()
            if self.st is not None:
                age = max(from_time - self.st.st_ctime,
                          from_time - self.st.st_mtime)
            else:
                age = None

            self.get_start_content()
            if self.entrydate is not None:
                if age is None:
                    age = 0
                age = max(age, from_time - self.entrydate)

            self.age = age

        return self.age

    def get_is_old(self, from_time=None, cutoff=None):
        '''
        determine as best as possible if the file is older than
        a certain number of seconds from the specified time
        '''
        if self.is_old is not None:
            return self.is_old

        age = self.get_age(from_time)

        if age is not None and cutoff is not None:
            if age > cutoff:
                self.is_old = True
            elif (self.entrydate is not None and
                  0 < from_time - self.entrydate < cutoff):
                self.is_old = False
            else:
                self.is_old = -1
        return self.is_old

    def load_file_info(self, from_time, cutoff, open_files=None):
        if open_files is None:
            open_files = []
        self.get_stats()
        self.get_is_empty()
        self.get_is_old(from_time, cutoff)
        self.get_filetype()
        self.get_is_open(open_files)

    @staticmethod
    def bool_to_string(value):
        '''
        turn bools into the equivalent string,
        also treating 1 as True, -1 and None as unknown ('--')
        and all other numeric etc values as False
        '''

        if value is None or value == -1:
            return '-'
        elif value is True:
            return 'T'
        else:
            return 'F'

    @staticmethod
    def string_to_bool(value):
        '''
        turn strings 'T', 'F', '--' into the bool
        values True, False, None; this is almost the
        inverse of bool_to_string
        '''
        if value == 'T':
            return True
        elif value == 'F':
            return False
        else:
            return None

    @staticmethod
    def stat_to_dict(fstat):
        stat_dict = {
            'dev': fstat.st_dev,
            'inode': fstat.st_ino,
            'mode': fstat.st_mode,
            'nlink': fstat.st_nlink,
            'uid': fstat.st_uid,
            'gid': fstat.st_gid,
            'dev_spec': fstat.st_rdev,
            'size': fstat.st_size,
            'blksize': fstat.st_blksize,
            'blkcnt': fstat.st_blocks,
            'atime': fstat.st_atime,
            'mtime': fstat.st_mtime,
            'ctime': fstat.st_ctime
        }

        return stat_dict

    def produce_dict(self):
        self.entry_dict = {'path': self.path,
                           'owner': str(self.get_owner()),
                           'ctime': FileInfo.get_time_formatted(
                               self.get_ctime()),
                           'mtime': FileInfo.get_time_formatted(
                               self.get_mtime()),
                           'open': FileInfo.bool_to_string(self.is_open),
                           'empty': FileInfo.bool_to_string(
                               self.get_is_empty()),
                           'old': FileInfo.bool_to_string(self.get_is_old()),
                           'type': self.get_filetype(),
                           'binary': self.get_is_binary(),
                           'stat': FileInfo.stat_to_dict(self.st),
                           'entrydate': self.entrydate}
        if ((not self.is_binary and 'data' not in self.filetype and
            'binary' not in self.filetype) and
                self.start_content is not None):
            self.entry_dict['content'] = self.start_content
        return self.entry_dict

    @staticmethod
    def format_pretty_output_from_dict(item, show_content=False, path_justify=None):
        output = ("file: %s" % item['path'].ljust(path_justify) +
                  ("  owner:%s" % str(item['owner']).ljust(5) if 'owner' in item else "") +
                  ("  (creat:%s" % item['ctime'] if 'ctime' in item else "") +
                  ("  mod:%s" % item['mtime'] if 'mtime' in item else "") +
                  ("  open:%s" % item['open'] if 'open' in item else "") +
                  ("  empty:%s" % item['empty'] if 'empty' in item else "") +
                  ("  old:%s" % item['old'] if 'old' in item else "") +
                  ("  type:%s" % item['type'] if 'type' in item else ""))
        if show_content and 'content' in item:
            output = output + "\n    content:%s" % item['content']
        return output

    def format_output_from_dict(self, item, show_content=False,
                                prettyprint=False, path_justify=None):
        if prettyprint:
            output = FileInfo.format_pretty_output_from_dict(
                item, show_content, path_justify)
        else:
            output = self.produce_json(item)
        return output

    def format_output(self, show_content=False,
                      prettyprint=False, path_justify=None):
        '''
        format information about a file for output
        depending on the sort of output desired
        '''

        item = self.produce_dict()
        return self.format_output_from_dict(item, show_content,
                                            prettyprint, path_justify)

    @staticmethod
    def fileinfo_from_dict(self, item, fromtime=None):
        '''
        this is the inverse of produce_dict, returning a new
        FileInfo object
        '''
        if fromtime is None:
            fromtime = time.time()
        # fixme - eh? what's broken?
        finfo = FileInfo(item['path'], magic=None, statinfo=None)
        finfo.st = item['stat']
        finfo.filetype = item['filetype']
        if 'content' in item:
            finfo.start_content = item['content']
        finfo.is_empty = FileInfo.string_to_bool(item['empty'])
        finfo.is_binary = FileInfo.string_to_bool(item['binary'])
        finfo.is_open = FileInfo.string_to_bool(item['open'])
        finfo.age = None  # not perfect but what can we do
        finfo.is_old = FileInfo.string_to_bool(item['old'])
        finfo.entrydate = item['entrydate']

    @staticmethod
    def display_from_dict(item, show_content=False, path_justify=None):
        print ("file:%s owner:%s creat:%s mod:%s open:%s empty:%s old:%s type:%s"
               % (item['path'].ljust(path_justify), item['owner'].ljust(5),
                  item['ctime'], item['mtime'], item['open'],
                  item['empty'], item['old'], item['type']))
        if show_content and 'content' in item:
            print "    content:%s" % item['content']


class LogUtils(object):
    @staticmethod
    def normalize(path):
        '''
        strip off compression
        suffix if any, plus the number of the log if any,
        leaving only the 'base' name of the file
        '''

        logname = os.path.basename(path)
        logname = re.sub(r'(\.[0-9]+)?(\.gz)?$', '', logname)
        logname = re.sub(r'(\.[0-9]+)?(\.log)(\.gz)?$', '.log', logname)
        logname = re.sub(r'([.-][0-9]+)(\.gz)?$', '', logname)
        return logname


class LogInfo(FileInfo):
    '''
    maintain and provide information (stat, filetype, other)
    about a log file
    '''

    def __init__(self, path, magic, statinfo=None):
        '''
        constructor
        args: full path to the file, magic object
        for determining file type
        '''
        super(LogInfo, self).__init__(path, magic, statinfo)
        self.normalized = LogUtils.normalize(self.path)
        self.normalized_path = os.path.join(os.path.dirname(self.path),
                                            self.normalized)
        self.rotated = None

    def load_file_info(self, from_time, cutoff, open_files=None, rotated=None):
        if rotated is None:
            rotated = []
        if open_files is None:
            open_files = []
        super(LogInfo, self).load_file_info(from_time, cutoff, open_files)
        self.get_rotated(rotated)

    def get_rotated(self, rotated_files):

        if self.normalized_path in rotated_files:
            self.rotated = 'T(%s/%s)' % (
                rotated_files[self.normalized_path][0],
                rotated_files[self.normalized_path][1])
            self.notifempty = rotated_files[self.normalized_path][2]
        else:
            self.rotated = 'F'
            self.notifempty = '-'

        return self.rotated

    def produce_dict(self):
        super(LogInfo, self).produce_dict()
        self.entry_dict['rotated'] = self.rotated
        self.entry_dict['normalized'] = self.normalized
        self.entry_dict['notifempty'] = self.notifempty
        return self.entry_dict

    def format_output(self, show_content=False, prettyprint=False,
                      path_justify=None, norm_justify=None):
        '''
        format information about a file for output
        depending on the sort of output desired
        '''
        item = self.produce_dict()

        if prettyprint:
            output = ("file:%s %s owner:%s  creat:%s mod:%s open:%s empty:%s rot:%s old:%s notifempty:%s, type:%s"
                      % (item['path'].ljust(path_justify),
                         item['normalized'].ljust(norm_justify),
                         item['owner'].ljust(5), item['ctime'],
                         item['mtime'], item['open'], item['empty'],
                         item['rotated'].ljust(6), item['old'],
                         item['notifempty'], item['type']))
            if show_content and 'content' in item:
                output = output + "\n    content:%s" % item['content']
        else:
            output = self.produce_json(item)
        return output

    @staticmethod
    def display_from_dict(item, show_content=False, path_justify=None, norm_justify=None):
        print ("file:%s %s  owner:%s creat:%s mod:%s open:%s empty:%s rot:%s old:%s notifempty:%s type:%s"
               % (item['path'].ljust(path_justify),
                  item['normalized'].ljust(norm_justify),
                  item['owner'].ljust(5), item['ctime'],
                  item['mtime'], item['open'], item['empty'],
                  item['rotated'].ljust(6), item['old'],
                  item['notifempty'], item['type']))
        if show_content and 'content' in item:
            print "    content:%s" % item['content']


class Config(object):
    '''
    directories and files to skip, where to look for files to be
    scanned, etc.
    change to suit your setup.
    '''

    cf = {
        'root_locations': ["/root"],
        'logs_locations': ["/var/log", "/a/search", "/a/sqldata",
                           "/var/store"],
        'homes_locations': ["/home", "/data/db20/home"],

        'rotate_basedir': "/etc/logrotate.d",
        'rotate_mainconf': "/etc/logrotate.conf",

        # ignore these
        'ignored_dirs': {
            '*':
            [".aptitude", ".augeas",
             ".bash.completion.d",
             ".bazaar", "benchmarks",
             ".byobu", ".bzr",
             ".store", ".cassandra", ".cache",
             ".config", ".cpan",
             ".dbus",
             "deb", ".debug", ".debtags", ".drush",
             ".fontconfig", ".gconfd",
             ".gem", ".git",
             ".gnome", ".gnupg",
             "hadoop-benchmarks", ".hivehistory",
             ".ipython", ".irssi",
             ".jmxsh_history", ".kde",
             ".lftp", ".links2",
             ".liquidprompt", "mediawiki-config",
             ".mozilla", "novaclient",
             ".npm", ".oprofile",
             ".oozie-auth-token", ".pig_history",
             ".pip", ".puppet",
             ".ssh", "software",
             ".spamassassin", ".subversion",
             ".sunw", ".svn", ".texmf-var",
             ".w3m", ".wapi", ".vim"],

            '/var/log':
            ["anaconda", "apt", "atop", "dist-upgrade",
             "fsck", "ganeti/cleaner", "ganeti/master-cleaner",
             "hadoop-hdfs", "hadoop-yarn", "hive", "hhvm",
             "installer", "journal", "l10nupdatelog",
             "libvirt", "news", "ntpstats",
             "oozie", "samba", "src/pystatsd", "sysstat", "upstart",
             "wikidata", "zuul"],

            '/var/cache':
            ["abrt-di", "akmods", "apache2", "apt",
             "apt-show-versions", "apt-xapian-index",
             "archiva", "cups", "debconf", "dnf", "fontconfig",
             "fonts", "git", "jenkins/war", "jetty", "ldconfig",
             "lighttpd/compress", "man", "pbuilder",
             "planet", "pppconfig",
             "request-tracker4/mason_data",
             "salt", "samba", "smokeping/images", "svnusers", "yum"],

            '/a/sqldata':
            ["*"],

            '/a/search':
            ["conf", "dumps", "indexes"]
        },
        'ignored_prefixes': [".bash_", ".xauth"],
        'ignored_files': {
            '*':
            [".ackrc", "apt.conf", "authorized_keys",
             ".bashrc",
             ".bconsole_history",
             "CmdTool.log", ".cshrc", ".cvspass",
             ".data_retention",
             ".emacs",
             ".exrc", ".forward",
             ".gdbinit", "gdbinit",
             ".gitconfig", ".gitignore",
             ".gitmodules", ".gitreview",
             ".gitignore_global", ".gnupg",
             ".gtkrc", ".hivehistory",
             ".hhvm.hhbc", ".hphpd.history",
             ".hphpd.ini",
             ".htoprc", ".hushlogin",
             ".inputrc", ".joe_state", ".joerc",
             ".lesshst", ".liquidpromptrc", "MegaSAS.log",
             ".mailcap", ".mh_profile",
             ".mime.types",
             ".mwsql_history",
             ".mweval_history", ".my.cnf",
             ".mysql_history", ".nano_history",
             ".npmrc",
             ".pearrc", ".pep8",
             ".php_history",
             ".pinerc", ".profile",
             "proxy-server.conf", "README",
             "README.txt",
             ".rediscli_history", ".rnd", ".screenrc",
             ".selected_editor", ".sh_history",
             "swift.conf", ".tcshrc",
             ".toprc", ".tramp_history",
             "twemproxy.conf", ".variables",
             ".vcl", ".viminfo", ".viminfo.tmp",
             ".vimrc", ".Xauthority",
             ".zshrc", ".zsh_history"],

            '/var/log':
            ["alternatives.log", "atop.log", "auth.log",
             "boot", "boot.log", "btmp", "daemon.log",
             "debug", "dmesg", "dnf.log",
             "dpkg.log", "faillog", "fontconfig.log", "fsck",
             "kern.log", "lastlog", "lpr.log", "messages",
             "puppet.log", "syslog", "udev", "ufw.log"],
        },
        'ignored_types': ["script", "package", "python", "debian", "HTML",
                          "RPM", "GIF", "JPEG", "PNG", "SVG", "program", "DSA",
                          "PDF", "symbolic link",
                          "executable", "shared object", "MS Windows icon"],
        'ignored_extensions': {
            '*':
            ["amd64.changes",
             ".builder", ".cfg", ".class", ".conf", ".css",
             ".deb", ".dsc",
             ".flv", ".gem",
             ".html", ".jar", ".java", ".jpg", ".js", ".json",
             ".ogg", ".ogv", ".odp", ".odt", ".ods",
             ".patch", ".pdf", ".php", ".png",
             ".ppm", "precise.tar.gz",
             ".py", ".pyc",
             ".pem", ".ring.gz", ".sh",
             ".swo", ".swp", ".ttf", ".tokudb", ".xcf",
             ".webm", "~"]
        },
        # older than 90 days is bad
        'cutoff': 90 * 86400,
        # run on this many hosts at once
        'batchsize': 20
    }


class LocalClientPlus(salt.client.LocalClient):
    '''
    extend the salt LocalClient module with methods for showing
    list of known minions that match the specified expression,
    and for copying file content to a newly created remote file
    '''

    @staticmethod
    def condition_kwarg(arg, kwarg):
        '''
        Return a single arg structure for caller to use
        '''
        if isinstance(kwarg, dict):
            kw_ = []
            for key, val in kwarg.items():
                kw_.append('{0}={1}'.format(key, val))
            return list(arg) + kw_
        return arg

    def cmd_expandminions(self, tgt, fun, arg=(), timeout=30,
                          expr_form='glob', ret='',
                          kwarg=None, **kwargs):
        '''
        return an expanded list of minions, assuming that the expr form
        is glob or list or some other such thing that can be expanded
        and not e.g. grain based

        this is wasteful because we actually run the job but it's less
        wasteful than
          salt "$hosts" -v --out raw test.ping |
          grep '{' | mawk -F"'" '{ print $2 }'
        '''
        arg = LocalClientPlus.condition_kwarg(arg, kwarg)
        pub_data = self.run_job(tgt, fun, arg, expr_form, ret,
                                timeout, **kwargs)

        if not pub_data:
            return []
        else:
            return list(set(pub_data['minions']))


class Runner(object):
    '''
    Manage running current script remotely via salt on one or more hosts
    '''

    def __init__(self, hosts_expr, expanded_hosts,
                 audit_type, generate_executor,
                 show_sample_content=False, to_check=None,
                 timeout=30, verbose=False):
        self.hosts_expr = hosts_expr
        self.expanded_hosts = expanded_hosts
        self.hosts, self.hosts_expr_type = Runner.get_hosts_expr_type(
            self.hosts_expr)
        self.audit_type = audit_type
        self.generate_executor = generate_executor
        self.show_sample_content = show_sample_content
        self.to_check = to_check
        self.timeout = timeout
        self.verbose = verbose

    @staticmethod
    def running_locally(hosts_expr):
        '''
        determine whether this script is to run on the local
        host or on one or more remote hosts
        '''
        if hosts_expr == "127.0.0.1" or hosts_expr == "localhost":
            return True
        else:
            return False

    def run_remotely(self):
        '''
        run the current script on specified remote hosts
        '''

        client = LocalClientPlus()

        if self.expanded_hosts is None:
            self.expanded_hosts = client.cmd_expandminions(
                self.hosts, "test.ping", expr_form=self.hosts_expr_type)
        code = "# -*- coding: utf-8 -*-\n"
        code += self.generate_executor()
        with open(__file__, 'r') as fp_:
            code += fp_.read()

        hostbatches = [self.expanded_hosts[i: i + Config.cf['batchsize']]
                       for i in range(0, len(self.expanded_hosts),
                                      Config.cf['batchsize'])]

        result = {}
        for hosts in hostbatches:
            if self.verbose:
                sys.stderr.write("INFO: running on hosts\n")
                sys.stderr.write(','.join(hosts) + '\n')

            # try to work around a likely race condition in zmq/salt
            # time.sleep(5)
            new_result = client.cmd(hosts, "cmd.exec_code", ["python2", code],
                                    expr_form='list', timeout=self.timeout)
            if new_result is not None:
                result.update(new_result)
            # fixme, collect and report on hosts that did
            # not respond
        return result

    @staticmethod
    def get_hosts_expr_type(hosts_expr):
        '''
        return the type of salt host expr and stash
        the converted expression as well
        '''

        if hosts_expr.startswith('grain:'):
            hosts = hosts_expr[6:]
            return hosts, 'grain'
        elif hosts_expr.startswith('pcre:'):
            hosts = hosts_expr[5:]
            return hosts, 'pcre'
        elif hosts_expr.startswith('list:'):
            hosts = hosts_expr[5:].split(',')
            return hosts, 'list'
        else:
            hosts = hosts_expr
            return hosts, 'glob'  # default


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

        if not Runner.running_locally(self.hosts_expr):
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

        self.perhost_rules_from_file = PerHostConfig.perhostcf
        self.perhost_raw = None
        if self.perhost_rules_from_file is None:
            if os.path.exists('audit_files_perhost_config.py'):
                try:
                    self.perhost_rules_from_file = runpy.run_path(
                        'audit_files_perhost_config.py')['perhostcf']
                    self.perhost_raw = open(
                        'audit_files_perhost_config.py').read()
                except:
                    pass

        if Runner.running_locally(self.hosts_expr):
            self.set_up_perhost_rules()

        if not Runner.running_locally(self.hosts_expr):
            self.cdb = RuleStore(self.store_filepath)
            self.cdb.store_db_init(self.expanded_hosts)
            self.set_up_and_export_rule_store()
        else:
            self.cdb = None

        self.show_ignored(Config.cf[self.locations])

        self.today = time.time()
        self.magic = magic_open(MAGIC_NONE)
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
        self.perhost_rules_from_store = PerHostRules.rules
        if self.perhost_rules_from_store is None:
            self.perhost_rules_compressed = PerHostRules.compressed
            if self.perhost_rules_compressed is not None:
                self.decompress_perhost_rules()

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

    def decompress_perhost_rules(self):
        '''
        we compress rules from the rule store before sending
        them to the remote host vi salt, it's much more reliable
        so the client must uncompress them
        '''
        rules_json_string = zlib.decompress(base64.b64decode(
            self.perhost_rules_compressed))
        rules_json_dict = json.loads(rules_json_string,
                                     object_hook=JsonHelper.decode_dict)
        self.perhost_rules_from_store = {}
        for host in rules_json_dict:
            if host not in self.perhost_rules_from_store:
                self.perhost_rules_from_store[host] = []
            for rule in rules_json_dict[host]:
                self.perhost_rules_from_store[host].append(
                    json.loads(rule,
                               object_hook=JsonHelper.decode_dict))

    def get_perhost_rules_as_json(self):
        '''
        this reads from the data_retention.d dirctory files for the minions
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

    def get_perhost_rules_compressed_code(self, indent):
        '''
        piece of the code that will be fed to salt and run on the
        remote hosts; this provides the rules for the host
        retrieved from the rules store db, in compressed format
        '''
        rules_json_dict = self.get_perhost_rules_as_json()
        rules_json_string = json.dumps(rules_json_dict)
        rules_json_compressed = zlib.compress(rules_json_string, 9)
        rules_json_b64 = base64.b64encode(rules_json_compressed)

        code = "\n\nclass PerHostRules(object):\n"
        code = code + indent + "compressed = '" + rules_json_b64 + "'\n"
        code = code + indent + "rules = None\n\n"
        return code

    def get_perhost_rules_normal_code(self, indent):
        rules = self.get_perhost_rules_as_json()

        code = "\n\nclass PerHostRules(object):\n" + indent + "rules = {}\n\n"
        for host in rules:
            code += indent + "rules['%s'] = [\n" % host
            code += (indent + indent +
                     (",\n%s" % (indent + indent)).join(rules[host]) + "\n")
            code += indent + "]\n"
        return code

    def generate_other_code(self):
        indent = "    "
        code = self.get_perhost_rules_compressed_code(indent)

        if self.perhost_raw is not None:
            code += ("\n\nclass PerHostConfig(object):\n" +
                     indent + self.perhost_raw + "\n\n")
        return code

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

        code += self.generate_other_code()
        return code

    def show_ignored(self, basedirs):
        if self.verbose:
            if not Runner.running_locally(self.hosts_expr):
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
        if Runner.running_locally(self.hosts_expr):
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

            dirs_problem, dirs_skipped = CommandLine.get_dirs_toexamine(report[host])
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

        code += self.generate_other_code()
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

    def do_local_audit(self):
        '''
        note that no summary report is done for a  single host,
        for logs we summarize across hosts
        '''
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
        result = []
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
            if audit_results[host]:
                output = None
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

        code += self.generate_other_code()
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


def usage(message=None):
    if message:
        sys.stderr.write(message + "\n")
    usage_message = """Usage: audit_files.py --target <hostexpr>
             [--prettyprint] [-report] [--depth <number>] [--dirsizes]
             [--maxfiles <number>] [--sample] [--files <filelist>]
             [--ignore <filelist>] [--examine <path>]
             [--timeout <number>] [--verbose]

This script audit a directory tree, producing a list of files, displaying
for each:
    'creation time' i.e. inode change time,
    modification time
    whether the file is currently opened by a process
    whether the file is older than 90 days (without creation time this cannot
        always be determined)
    the file type
    the uid of the file owner

Alternatively it can be used to provide more limited directory info for
a single directory on a remote host. (This is used in interactive mode.)

The script requires salt to run remotely, and expects to be run
from the salt master.

Options:

    audit       (-a) -- specify the type of audit to be done, one of 'root',
                        'logs' or 'homes'; this may not be specified with
                        the 'info' option.
    target      (-t) -- for local runs, this must be 'localhost' or '127.0.1'
                        for remote hosts, this should be a host expression
                        recognizable by salt, in the following format:
                           grain:<salt grain>
                           pcre:<regex>
                           list:<host1>,<host2>,...
                           <glob or string>
    prettyprint (-p) -- print results in a nice format suitable for human
                        consumption (default: print json output)
    report      (-r) -- show a summary report for the group of hosts with
                        details only for anomalies (default: false)
                        this option implies 'oldest'
    depth       (-d) -- inspect directories at this depth when checking that
                        directories don't have too many files to audit
                        (default: 0)
    dirsizes    (-D) -- don't report on files, just check the directories up to
                        the specified or default depth and report on those that
                        have more than maxfiles
    maxfiles    (-m) -- directories with more than this many files will be
                        skipped and a warning shown (default: 100, unless
                        dirsizes is specified, then 1000)
    sample      (-s) -- display the first line from each file along with the
                        regular file info, for files that are text format
                        (default: false)
    timeout     (-T) -- for audit of remote hosts, how many seconds to wait
                        for the salt command to return before giving up
                        (default: 60)
    files       (-f) -- comma-separated list of filenames (basename only and no
                        paths) and/or directories (full path must be specified)
                        which will be checked; if none is specified all files
                        in a standard list of directories will be examined
    ignore      (-i) -- comma-separated list of files and/or directories to be
                        ignored in addition to the usual ones; if the name ends
                        in '/' it is treated as a directory, else as a file,
                        in either case the full path must be specified or the
                        the element will be silently ignored.
    interactive (-I) -- after the report is completed, enter interactive mode,
                        allowing the user to inspect directories on any host
                        and/or set audit rules for them or their contents

    examine     (-e) -- instead of an audit, display information about the
                        specified directory or file; this may not be specified
                        with 'audit'.

    filecontents(-F) -- instead of an audit, display the first so many lines
                        of the specified file; this may not be specified
                        with 'audit'.
    linecount   (-l) -- number of lines of file content to be displayed
                        (efault: 1)

For 'logs' audit type:

    system      (-S) -- show system logs (e.g. syslog, messages) along with
                        app logs; this relies on a hard-coded list of presumed
                        system logs (default: false)
    oldest      (-o) -- only show the oldest log in a group of rotated
                        logs (default: show all logs)
"""
    sys.stderr.write(usage_message)
    sys.exit(1)


global_keys = [key for key, value_unused in
               sys.modules[__name__].__dict__.items()]
if 'executor' not in global_keys:
    def executor():
        # this function is generated by the caller on the salt master
        # and passed along with the code to remote clients.
        # someone reaching this version of the function did so by
        # mistake (calling the script locally without args).
        usage()

if 'PerHostConfig' not in global_keys:
    class PerHostConfig(object):
        # placeholder like the executor above, this class is
        # generated on the salt master and passed with script
        # code to the clients
        perhostcf = None

if 'PerHostRules' not in global_keys:
    class PerHostRules(object):
        # placeholder like the executor above, this class is
        # generated on the salt master and passed with script
        # code to the clients
        rules = None
        compressed = None

def main():
    if len(sys.argv) == 1:
        # special case, no args, we expect a special
        # executor function to have been defined and
        # added to the existing code, shovelled into
        # the interpreter... if not there, whine
        for key, value_unused in sys.modules[__name__].__dict__.items():
            if key == 'executor':
                executor()
                sys.exit(0)
        usage()

    hosts_expr = None
    audit_type = None
    files_to_check = None
    prettyprint = False
    show_sample_content = False
    summary_report = False
    verbose = False
    ignore_also = None
    dir_info = None
    batchno = 1
    file_info = None
    linecount = 1
    maxfiles = None
    timeout = 60
    depth = 0
    dirsizes = False
    show_system_logs = False
    oldest_only = False
    interactive = False
    store_filepath = "/etc/data_retention/dataretention_rules.sq3"

    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "a:b:d:Df:F:l:i:Ie:m:oprsSt:T:vh",
            ["audit=", "files=",
             "filecontents=", "linecount=",
             "ignore=",
             "interactive",
             "depth=", "maxfiles=",
             "oldest", "prettyprint", "report",
             "dirsizes", "examine", "batchno",
             "sample", "system",
             "target=", "timeout=", "verbose", "help"])

    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))

    for (opt, val) in options:
        if opt in ["-t", "--target"]:
            hosts_expr = val
        elif opt in ["-a", "--audit"]:
            audit_type = val
        elif opt in ["-d", "--depth"]:
            if not val.isdigit():
                usage("depth must be a number")
            depth = int(val)
        elif opt in ["-f", "--files"]:
            files_to_check = val
        elif opt in ["-F", "--filecontents"]:
            file_info = val
        elif opt in ["-l", "--linecount"]:
            if not val.isdigit():
                usage("linecount must be a number (starting from 1)")
            linecount = int(val)
        elif opt in ["-i", "--ignore"]:
            ignore_also = val
        elif opt in ["-I", "--interactive"]:
            interactive = True
        elif opt in ["-e", "--examine"]:
            dir_info = val
        elif opt in ["-b", "--batchno"]:
            if not val.isdigit():
                usage("batcho must be a number (starting from 1)")
            batchno = int(val)
        elif opt in ["-m", "--maxfiles"]:
            if not val.isdigit():
                usage("maxfiles must be a number")
            maxfiles = int(val)
        elif opt in ["-o", "--oldest"]:
            oldest_only = True
        elif opt in ["-p", "--prettyprint"]:
            prettyprint = True
        elif opt in ["-r", "--report"]:
            summary_report = True
        elif opt in ["-D", "--dirsizes"]:
            dirsizes = True
        elif opt in ["-s", "--sample"]:
            show_sample_content = True
        elif opt in ["-S", "--system"]:
            show_system_logs = True
        elif opt in ["-T", "--timeout"]:
            if not val.isdigit():
                usage("timeout must be a number")
            timeout = int(val)
        elif opt in ["-h", "--help"]:
            usage()
        elif opt in ["-v", "--verbose"]:
            verbose = True
        else:
            usage("Unknown option specified: %s" % opt)

    if len(remainder) > 0:
        usage("Unknown option specified: <%s>" % remainder[0])

    if hosts_expr is None:
        usage("Mandatory target argument not specified")

    count = len(filter(None, [audit_type, dir_info, file_info]))
    if count == 0:
        usage("One of 'audit', 'examine' "
              "or 'filecontents' must be specified")
    elif count > 1:
        usage("Only one of 'audit', 'examine' "
              "or 'filecontents' may be specified")

    if dir_info is not None:
        # for now more than 1000 entries in a dir = we silently toss them
        direxam = DirExaminer(dir_info, hosts_expr, batchno, 1000, timeout)
        direxam.run()
        sys.exit(0)
    elif file_info is not None:
        fileexam = FileExaminer(file_info, hosts_expr, linecount, timeout)
        fileexam.run()
        sys.exit(0)

    if audit_type not in ['root', 'logs', 'homes']:
        usage("audit type must be one of 'root', 'logs', 'homes'")

    if show_system_logs and not audit_type == 'logs':
        usage("'system' argument may only be used with logs audit")

    if oldest_only and not audit_type == 'logs':
        usage("'oldest' argument may only be used with logs audit")

    if audit_type == 'logs':
        logsaudit = LogsAuditor(hosts_expr, audit_type, prettyprint,
                                oldest_only, show_sample_content, dirsizes,
                                show_system_logs,
                                summary_report, depth, files_to_check, ignore_also,
                                timeout, maxfiles, store_filepath, verbose)
        report, ignored = logsaudit.audit_hosts()
        if interactive:
            cmdline = CommandLine(store_filepath, timeout, audit_type, hosts_expr)
            cmdline.run(report, ignored)

    elif audit_type == 'root':
        filesaudit = FilesAuditor(hosts_expr, audit_type, prettyprint,
                                  show_sample_content, dirsizes,
                                  summary_report,
                                  depth, files_to_check, ignore_also,
                                  timeout, maxfiles, store_filepath, verbose)
        report, ignored = filesaudit.audit_hosts()
        if interactive:
            cmdline = CommandLine(store_filepath, timeout, audit_type, hosts_expr)
            cmdline.run(report, ignored)

    elif audit_type == 'homes':
        homesaudit = HomesAuditor(hosts_expr, audit_type, prettyprint,
                                  show_sample_content, dirsizes,
                                  summary_report,
                                  depth, files_to_check, ignore_also,
                                  timeout, maxfiles, store_filepath, verbose)
        report, ignored = homesaudit.audit_hosts()
        if interactive:
            cmdline = CommandLine(store_filepath, timeout, audit_type, hosts_expr)
            cmdline.run(report, ignored)

if __name__ == '__main__':
    main()
