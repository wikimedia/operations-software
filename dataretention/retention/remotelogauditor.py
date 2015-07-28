import json

from clouseau.retention.fileinfo import LogInfo
from clouseau.retention.utils import JsonHelper
from retention.remotefileauditor import RemoteFilesAuditor


class RemoteLogsAuditor(RemoteFilesAuditor):
    def __init__(self, hosts_expr, audit_type, confdir=None, prettyprint=False,
                 oldest=False,
                 show_content=False, show_system_logs=False,
                 dirsizes=False, summary_report=False, depth=2,
                 to_check=None, ignore_also=None,
                 timeout=60, maxfiles=None, store_filepath=None,
                 verbose=False):
        super(RemoteLogsAuditor, self).__init__(hosts_expr, audit_type,
                                                confdir, prettyprint,
                                                show_content, dirsizes,
                                                summary_report, depth,
                                                to_check, ignore_also, timeout,
                                                maxfiles, store_filepath, verbose)
        self.oldest_only = oldest
        self.show_system_logs = show_system_logs
        if self.show_system_logs:
            self.ignores.ignored['files'].pop("/var/log")
        self.display_from_dict = LogInfo.display_from_dict

    def get_audit_args(self):
        # fixme check if locallogauditor wants the oldest_only param
        audit_args = [self.confdir,
                      self.oldest_only,
                      self.show_sample_content,
                      self.show_system_logs,
                      self.dirsizes,
                      self.depth - 1,
                      self.to_check,
                      ",".join(self.ignore_also) if self.ignore_also is not None else None,
                      self.timeout,
                      self.MAX_FILES]
        return audit_args

    def display_summary(self, audit_results):
        logs = {}
        hosts_count = 0
        all_hosts = audit_results.keys()
        hosts_count = len(all_hosts)

        for host in all_hosts:
            output = None
            if audit_results[host]:
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
            if output is None:
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
            RemoteLogsAuditor.display_variance_info(old_count, hosts_count,
                                                    logs[logname]['old'],
                                                    'old', logname)
            RemoteLogsAuditor.display_variance_info(maybe_old_count, hosts_count,
                                                    logs[logname]['maybe_old'],
                                                    'maybe old', logname)
            RemoteLogsAuditor.display_variance_info(unrot_count, hosts_count,
                                                    logs[logname]['unrot'],
                                                    'unrotated', logname)
            RemoteLogsAuditor.display_variance_info(notifempty_count, hosts_count,
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


