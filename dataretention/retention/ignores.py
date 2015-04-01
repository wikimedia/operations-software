import os
import sys
import runpy

sys.path.append('/srv/audits/retention/scripts/')

from retention.status import Status
import retention.remotefileauditor
import retention.utils
import retention.fileutils
import retention.ruleutils
import retention.cliutils

class Ignores(object):
    '''
    collection of files and directories ignored by the audit
    on a given host
    '''

    def __init__(self, cdb):
        self.cdb = cdb
        self.perhost_rules_from_file = None
        self.hosts = self.cdb.store_db_list_all_hosts()
        self.perhost_ignores = {}
        self.perhost_ignores_from_rules = {}
        self.perhost_rules_from_store = {}
        self.get_perhost_cf_from_file()

    def get_perhost_from_rules(self, hosts=None):
        if hosts == None:
            hosts = self.hosts
        for host in hosts:
            self.perhost_rules_from_store = retention.ruleutils.get_rules(
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

    def get_perhost_cf_from_file(self):
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
