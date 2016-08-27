import os
import glob
import socket
import time
import clouseau.retention.utils.utils
import clouseau.retention.utils.config
from clouseau.retention.utils.fileinfo import LogInfo, LogUtils
from clouseau.retention.local.localfileaudit import LocalFilesAuditor
import clouseau.retention.utils.fileutils
import clouseau.retention.utils.magic


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


def get_rotated_keep(line):
    fields = line.split()
    if len(fields) == 2:
        keep = fields[1]
    else:
        keep = None
    return keep


def get_logs(line):
    if not line:
        return []
    # path may be in double quotes
    if line.startswith('"') and line.endswith('"'):
        line = line[1:-1]
    # ignore paths that start with ~, skip anything not a path
    if not line.startswith('/'):
        # probably a directive or a blank line
        return []
    # wildcard allowed in path
    if '*' in line:
        return (glob.glob(
            os.path.join(clouseau.retention.utils.config.conf['rotate_basedir'], line)))
    else:
        return [line]


def get_logrotate_defaults():
    contents = open(clouseau.retention.utils.config.conf['rotate_mainconf']).read()
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
        tmp_freq = get_rotated_freq(line)
        if tmp_freq:
            freq = tmp_freq
            continue
        elif line.startswith('rotate'):
            tmp_keep = get_rotated_keep(line)
            if tmp_keep:
                keep = tmp_keep
    return freq, keep


def find_rotated_logs(confdir):
    '''
    gather all names of log files from logrotate
    config files
    '''
    rotated_logs = {}
    default_freq, default_keep = get_logrotate_defaults()
    parser = LogRotParser(confdir, default_freq, default_keep)
    rotated_logs.update(parser.parse(
        open(clouseau.retention.utils.config.conf['rotate_mainconf']).read()))
    for fname in os.listdir(clouseau.retention.utils.config.conf['rotate_basedir']):
        pathname = os.path.join(clouseau.retention.utils.config.conf['rotate_basedir'], fname)
        if os.path.isfile(pathname):
            rotated_logs.update(parser.parse(open(pathname).read()))
    return rotated_logs


def get_mysqldir_ignores(hostname):
    # we can skip all bin logs, relay logs, and pid files in this
    # directory. anything else should get looked at.
    ignore_these = [hostname + '-bin', hostname + '-relay-bin',
                    hostname + '.pid', hostname + '-bin.index',
                    hostname + '-relay-bin.index']
    # add these files to ignore list; a one line report on
    # mysql log expiry configuration is sufficient
    file_ignores = ignore_these
    dir_ignores = ['*']
    return file_ignores, dir_ignores


def get_datadir(line):
    datadir = None
    fields = line.split('=', 1)
    fields = [field.strip() for field in fields]
    if fields[0] == 'datadir' and fields[1].startswith('/'):
        datadir = fields[1]
        # strip trailing slash if needed
        if len(datadir) > 1 and datadir.endswith('/'):
            datadir = datadir[:-1]
            if not datadir:
                datadir = None
    return datadir


def get_expire_days(line, filename):
    found = False
    text = None
    if line.startswith('expire_logs_days'):
        fields = line.split('=', 1)
        fields = [field.strip() for field in fields]
        if fields[0] == 'expire_logs_days' and fields[1].isdigit():
            found = True
            if int(fields[1]) > clouseau.retention.utils.config.conf['cutoff'] / 86400:
                text = ('WARNING: some mysql logs expired after %s days in %s'
                        % (fields[1], filename))
    return found, text


class LogRotParser(object):
    def __init__(self, confdir, default_freq='-', default_keep='-'):
        self.confdir = confdir
        self.default_freq = default_freq
        self.default_keep = default_keep
        self.freq = None
        self.keep = None
        self.notifempty = None
        self.log_group = None
        self.clear()

    def clear(self):
        self.freq = self.default_freq
        self.keep = self.default_keep
        self.notifempty = '-'
        self.log_group = []

# fixme too many branches 16/12
# we have a lot of dup code now. pull out somehow

    def get_logrot_directives(self, line):
        if line.startswith('rotate'):
            tmp_keep = get_rotated_keep(line)
            if tmp_keep:
                self.keep = tmp_keep
        elif line == 'notifempty':
            self.notifempty = 'T'
        else:
            tmp_freq = get_rotated_freq(line)
            if tmp_freq:
                self.freq = tmp_freq

    def parse(self, contents):
        # state indicates the string we look for next
        clouseau.retention.utils.config.set_up_conf(self.confdir)
        lines = contents.split('\n')
        state = '{'
        self.clear()
        logs = {}
        log_group = []
        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if state == '{':
                # looking for lines like '/var/account/pacct {'
                # or '/var/log/syslog { }'
                if line.endswith('{'):
                    state = '}'
                    line = line[:-1].strip()
                    log_group.extend(get_logs(line))
                elif line.endswith('}'):
                    if line[:-1].rstrip().endswith('{'):
                        line = line[:-1].rstrip()
                        log_group.extend(get_logs(line))
                        state = '{'
                        for log in log_group:
                            logs[log] = [self.freq, self.keep, self.notifempty]
                        self.clear()
            elif state == '}':
                if line.endswith('}'):
                    state = '{'
                    for log in log_group:
                        logs[log] = [self.freq, self.keep, self.notifempty]
                    self.clear()
                else:
                    self.get_logrot_directives(line)
        return logs


class MySqlCfParser(object):
    def __init__(self, confdir):
        self.confdir = confdir

    def check_mysqlconf(self):
        '''
        check how long mysql logs are kept around
        '''
        clouseau.retention.utils.config.set_up_conf(self.confdir)
        mysql_ignores = clouseau.retention.utils.ignores.init_ignored()

        # note that I also see my.cnf.s3 and we don't check those (yet)
        hostname = socket.getfqdn()
        if '.' in hostname:
            hostname = hostname.split('.')[0]
        output = ''
        for filename in clouseau.retention.utils.config.conf['mysqlconf']:
            expires = False
            datadir = None
            try:
                contents = open(filename).read()
            except:
                # file or directory probably doesn't exist
                continue
            lines = contents.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                result = get_datadir(line)
                if result is not None:
                    datadir = result
                    file_ignores, dir_ignores = get_mysqldir_ignores(hostname)
                    for igntype in 'files', 'dirs':
                        if datadir not in mysql_ignores[igntype]:
                            mysql_ignores[igntype][datadir] = []

                    mysql_ignores['files'][datadir].extend(file_ignores)
                    mysql_ignores['dirs'][datadir].extend(dir_ignores)
                    continue
                result, message = get_expire_days(line, filename)
                if message is not None:
                    if output:
                        output = output + '\n'
                    output = output + message
                if result is not None:
                    expires = result

                if expires and (datadir is not None):
                    break

        return mysql_ignores, output


class LocalLogsAuditor(LocalFilesAuditor):
    def __init__(self, audit_type, confdir=None,
                 oldest=False,
                 show_content=False, show_system_logs=False,
                 dirsizes=False, depth=2,
                 to_check=None, ignore_also=None,
                 maxfiles=None):
        super(LocalLogsAuditor, self).__init__(audit_type, confdir,
                                               show_content, dirsizes,
                                               depth, to_check, ignore_also,
                                               maxfiles)

        self.oldest_only = oldest
        self.show_system_logs = show_system_logs
        if self.show_system_logs:
            for path in clouseau.retention.utils.config.conf['systemlogs']:
                self.ignored['files'].pop(path, None)

        self.display_from_dict = LogInfo.display_from_dict

    # fixme this name no good after 'find_all_files' right?
    def get_all_files(self, cutoff, open_files, rotated):
        all_files = {}
        files = self.find_all_files()

        magic = clouseau.retention.utils.magic.magic_open(clouseau.retention.utils.magic.MAGIC_NONE)
        magic.load()
        today = time.time()
        for (fname, stat) in files:
            all_files[fname] = LogInfo(fname, magic, stat)
            all_files[fname].load_file_info()
            all_files[fname].load_extra_file_info(today, cutoff, open_files)
            all_files[fname].get_rotated(rotated)
        return all_files

    def do_local_audit(self):
        '''
        note that no summary report is done for a  single host,
        for logs we summarize across hosts
        '''
        mysqlcfparser = MySqlCfParser(self.confdir)
        mysql_ignores, mysql_issues = mysqlcfparser.check_mysqlconf()
        self.ignored = self.ignores.merge([self.ignored, mysql_ignores])

        result = []
        if mysql_issues:
            result.append(mysql_issues)

        open_files = clouseau.retention.utils.fileutils.get_open_files()
        rotated = find_rotated_logs(self.confdir)

        all_files = self.get_all_files(clouseau.retention.utils.config.conf['cutoff'],
                                       open_files, rotated)

        all_files_sorted = sorted(all_files,
                                  key=lambda f: all_files[f].path)
        last_log_normalized = ''
        last_log = ''
        age = 0

        if all_files:
            max_name_length = max([len(all_files[fname].path)
                                   for fname in all_files]) + 2
            max_norm_length = max([len(all_files[fname].normalized)
                                   for fname in all_files]) + 2

        for fname in all_files_sorted:
            fage = all_files[fname].get_age()
            if clouseau.retention.utils.fileutils.contains(
                    all_files[fname].filetype,
                    clouseau.retention.utils.config.conf['ignored_types']):
                continue

            if (self.oldest_only and
                    all_files[fname].normalized == last_log_normalized):
                # still doing the same group of logs
                if fage > age:
                    age = fage
                    last_log = fname
            else:
                if last_log:
                    result.append(all_files[last_log].format_output(
                        self.show_sample_content,
                        False, max_name_length, max_norm_length))

                # starting new set of logs (maybe first set)
                last_log_normalized = all_files[fname].normalized
                last_log = fname
                age = fage

        if last_log:
            result.append(all_files[last_log].format_output(
                self.show_sample_content,
                False, max_name_length, max_norm_length))
        output = "\n".join(result) + "\n"
        return output

    def normalize(self, fname):
        return LogUtils.normalize(fname)
