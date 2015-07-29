import os
import glob
import socket
import time

import clouseau.retention.utils
import clouseau.retention.config
from clouseau.retention.fileinfo import LogInfo, LogUtils
from clouseau.retention.localfileaudit import LocalFilesAuditor
import clouseau.retention.fileutils
import clouseau.retention.magic

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
            for path in clouseau.retention.config.conf['systemlogs']:
                self.ignored['files'].pop(path, None)

        self.display_from_dict = LogInfo.display_from_dict

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

    def parse_logrotate_contents(self, contents,
                                 default_freq='-', default_keep='-'):
        clouseau.retention.config.set_up_conf(self.confdir)
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
                        os.path.join(clouseau.retention.config.conf['rotate_basedir'], line)))
                else:
                    log_group.append(line)
            elif state == 'want_rbracket':
                tmp_freq = LocalLogsAuditor.get_rotated_freq(line)
                if tmp_freq:
                    freq = tmp_freq
                    continue
                elif line.startswith('rotate'):
                    tmp_keep = LocalLogsAuditor.get_rotated_keep(line)
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
        contents = open(clouseau.retention.config.conf['rotate_mainconf']).read()
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
            tmp_freq = LocalLogsAuditor.get_rotated_freq(line)
            if tmp_freq:
                freq = tmp_freq
                continue
            elif line.startswith('rotate'):
                tmp_keep = LocalLogsAuditor.get_rotated_keep(line)
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
        rotated_logs.update(self.parse_logrotate_contents(
            open(clouseau.retention.config.conf['rotate_mainconf']).read(),
            default_freq, default_keep))
        for fname in os.listdir(clouseau.retention.config.conf['rotate_basedir']):
            pathname = os.path.join(clouseau.retention.config.conf['rotate_basedir'], fname)
            if os.path.isfile(pathname):
                rotated_logs.update(self.parse_logrotate_contents(
                    open(pathname).read(), default_freq, default_keep))
        return rotated_logs

    def check_mysqlconf(self):
        '''
        check how long mysql logs are kept around
        '''
        mysql_ignores = clouseau.retention.ignores.init_ignored()

        # note that I also see my.cnf.s3 and we don't check those (yet)
        hostname = socket.getfqdn()
        output = ''
        for filename in clouseau.retention.config.conf['mysqlconf']:
            found = False
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
                if line.startswith('datadir'):
                    fields = line.split('=', 1)
                    fields = [field.strip() for field in fields]
                    if fields[0] != 'datadir':
                        continue
                    if not fields[1].startswith('/'):
                        continue
                    datadir = fields[1]
                    # strip trailing slash if needed
                    if len(datadir) > 1 and datadir.endswith('/'):
                        datadir = datadir[:-1]
                    # we can skip all bin logs, relay logs, and pid files in this
                    # directory. anything else should get looked at.
                    if '.' in hostname:
                        hostname = hostname.split('.')[0]
                    ignore_these = [hostname + '-bin', hostname + '-relay-bin',
                                    hostname + '.pid', hostname + '-bin.index',
                                    hostname + '-relay-bin.index']

                    # add these files to ignore list; a one line report on
                    # mysql log expiry configuration is sufficient

                    if datadir not in mysql_ignores['files']:
                        mysql_ignores['files'][datadir] = ignore_these
                    else:
                        mysql_ignores['files'][datadir].extend(ignore_these)
                    # skip the subdirectories in here, they will be full of mysql dbs
                    if datadir not in mysql_ignores['dirs']:
                        mysql_ignores['files'][datadir] = ['*']
                    else:
                        mysql_ignores['files'][datadir].append('*')

                if line.startswith('expire_logs_days'):
                    fields = line.split('=', 1)
                    fields = [field.strip() for field in fields]
                    if fields[0] != 'expire_logs_days':
                        continue
                    if not fields[1].isdigit():
                        continue
                    found = True
                    if int(fields[1]) > clouseau.retention.config.conf['cutoff']/86400:
                        if output:
                            output = output + '\n'
                        output = output + ('WARNING: some mysql logs expired after %s days in %s'
                                           % (fields[1], filename))
            if not found:
                if output:
                    output = output + '\n'
                output = output + 'WARNING: some mysql logs never expired in ' + filename

        self.ignored = self.ignores.merge([self.ignored, mysql_ignores])

        return output

    def do_local_audit(self):
        '''
        note that no summary report is done for a  single host,
        for logs we summarize across hosts
        '''
        mysql_issues = self.check_mysqlconf()
        result = []
        if mysql_issues:
            result.append(mysql_issues)

        open_files = clouseau.retention.fileutils.get_open_files()
        rotated = self.find_rotated_logs()

        all_files = {}
        files = self.find_all_files()

        magic = clouseau.retention.magic.magic_open(clouseau.retention.magic.MAGIC_NONE)
        magic.load()
        today = time.time()
        for (fname, stat) in files:
            all_files[fname] = LogInfo(fname, magic, stat)
            all_files[fname].load_file_info(today, clouseau.retention.config.conf['cutoff'],
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
            if clouseau.retention.fileutils.contains(all_files[fname].filetype,
                                                     clouseau.retention.config.conf['ignored_types']):
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
                        False, max_name_length, max_norm_length))

                # starting new set of logs (maybe first set)
                last_log_normalized = all_files[fname].normalized
                last_log = fname
                age = all_files[fname].age

        if last_log:
            result.append(all_files[last_log].format_output(
                self.show_sample_content,
                False, max_name_length, max_norm_length))
        output = "\n".join(result) + "\n"
        return output

    def normalize(self, fname):
        return LogUtils.normalize(fname)
