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
                oldfile.name,
                newfile.name,
            )
            log.debug(cmd)
            return subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            # TODO: logging!
            log.error('Could not create the diffs; command was %s', cmd)
            return ''

    def _get_diffs(self, name, old, new):
        sfx = re.sub('[\/]', '-', name)
        oldf = NamedTemporaryFile(
            suffix=sfx + '.old',
            delete=False)
        if 'content' in old['parameters']:
            log.debug('remoove ')
            del(old['parameters']['content']['content'])
        oldf.write(json.dumps(old, sort_keys=True, indent=4))
        oldf.write("\n")
        oldf.close()
        newf = NamedTemporaryFile(
            suffix=sfx + '.new',
            delete=False)
        if 'content' in new['parameters']:
            del(new['parameters']['content']['content'])
        newf.write(json.dumps(new, sort_keys=True, indent=4))
        newf.write("\n")
        newf.close()
        diffres = self._generate_diff(oldf, newf)
        content = self._diffs['content_differences'].get(name, '')
        self.results.append((name, diffres, content))
        os.unlink(oldf.name)
        os.unlink(newf.name)
