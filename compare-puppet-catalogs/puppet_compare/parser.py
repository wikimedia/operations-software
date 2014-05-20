import os
import subprocess
import json
from tempfile import NamedTemporaryFile
import logging
import re

log = logging.getLogger('puppet_compare')


def contains(haystack, needle):
    return (haystack.find(needle) >= 0)


class DiffParser(object):

    def __init__(self, filename, nodename):
        self.results = []
        self.nodename = nodename
        with open(filename, 'r') as fh:
            self._diffs = json.load(fh)[nodename]
        log.debug('Loaded the diff json file.')
        self.tmpfile = {}

    def run(self):
        for (resource, new_content) in self._diffs['differences_in_new'].items():
            log.debug("looking at resource %s", resource)
            self._get_diffs(
                resource,
                self._diffs['differences_in_old'][resource],
                new_content)

        if self._diffs['only_in_old']:
            self._get_diffs('old_missing', [], self._diffs['only_in_old'])
        if self._diffs['only_in_new']:
            self._get_diffs('new_missing', self._diffs['only_in_new'], [])

        return self.results

    def _generate_diff(self, oldfile, newfile):
        try:
            # Ugly hack to workaround subprocess.check_output limitations
            cmd = 'diff -ar -U 1000 {} {} || (if [ "x$?" = "x1" ]; then exit 0; else exit $?; fi;)'.format(
                oldfile,
                newfile,
            )
            log.debug(cmd)
            return subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            # TODO: logging!
            log.error('Could not create the diffs; command was %s', cmd)
            return ''

    def _write_to_tmp(self, sfx, content):
        f = NamedTemporaryFile(
            suffix=sfx,
            delete=False
        )
        f.write(json.dumps(content, indent=4))
        # Avoid the 'no newline at the end of file' error from diff
        f.write("\n")
        f.close()
        return f.name

    def _get_diffs(self, name, old, new):
        sfx = re.sub('[\/]', '-', name)

        if isinstance(old, dict) and 'content' in old['parameters']:
            del old['parameters']['content']['content']
        old_file = self._write_to_tmp(sfx + '.old', old)

        if isinstance(new, dict) and 'content' in new['parameters']:
            del new['parameters']['content']['content']
        new_file = self._write_to_tmp(sfx + '.old', new)

        diffres = self._generate_diff(old_file, new_file)
        # If there are content differences...
        content = self._diffs['content_differences'].get(name, '')
        self.results.append((name, diffres, content))
        os.unlink(old_file)
        os.unlink(new_file)
