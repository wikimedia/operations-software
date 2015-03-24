import os
import time
import re
import json
import gzip
import calendar
import datetime
import stat

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
