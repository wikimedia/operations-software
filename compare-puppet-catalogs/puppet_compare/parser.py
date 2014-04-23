import os
import subprocess
import shlex
from tempfile import NamedTemporaryFile


def contains(haystack, needle):
    return (haystack.find(needle) >= 0)


class DiffParser(object):
    OLD_RESOURCE = 'Old Resource:'
    NEW_RESOURCE = 'New Resource:'
    DIFF_BEGIN = 'Content diff:'
    DIFF_END = '--------------------------------------------------------------------------------'
    IN_OLD_RESOURCE = 'resource.old'
    IN_NEW_RESOURCE = 'resource.new'
    IN_DIFF = 'diff'

    def __init__(self, filename):
        self.diffs = []
        self.fname = filename
        self.tmpfile = {}
        self.diffdata = ''
        self.stopgap = True

    def generate_diff(self):
        if self.stopgap:
            return
        try:
            # Ugly hack to workaround subprocess.check_output limitations
            cmd = 'diff -ar -U 1000 {} {} || (if [ "x$?" = "x1" ]; then exit 0; else exit $?; fi;)'.format(
                self.tmpfile[self.IN_OLD_RESOURCE].name,
                self.tmpfile[self.IN_NEW_RESOURCE].name,
            )
            diff_resources = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            # TODO: logging!
            diff_resources = ''
            print e.output

        self.diffs.append((diff_resources, self.diffdata))
        for state, fh in self.tmpfile.items():
            os.unlink(fh.name)
            self.tmpfile[state] = None
        self.diffdata = ''

    def begin_resource(self, state):
        if state is None:
            return
        elif state == self.IN_DIFF:
            self.diffdata = ''
        else:
            self.tmpfile[state] = NamedTemporaryFile(
                suffix=state,
                delete=False)

    def end_resource(self, state):
        if state is None or state == self.IN_DIFF:
            return
        self.tmpfile[state].close()

    def add_line(self, state, line):
        if state is None:
            return
        elif state == self.IN_DIFF:
            self.diffdata += line
        else:
            self.tmpfile[state].write(line)

    def parse(self, filehandle):
        """
        shamefully inefficient parser of the output of puppet-diff
        """
        state = None

        for line in filehandle:
            if not line.rstrip() and state != self.IN_DIFF:
                # skip empty lines
                continue
            if contains(line, self.OLD_RESOURCE):
                self.end_resource(state)
                self.generate_diff()
                self.stopgap = False
                state = self.IN_OLD_RESOURCE
                self.begin_resource(state)
            elif contains(line, self.NEW_RESOURCE):
                self.end_resource(state)
                state = self.IN_NEW_RESOURCE
                self.begin_resource(state)
            elif contains(line, self.DIFF_BEGIN):
                self.end_resource(state)
                state = self.IN_DIFF
                self.begin_resource(state)
            elif contains(line, self.DIFF_END):
                self.end_resource(state)
                state = None
            else:
                self.add_line(state, line)

    def run(self):
        with open(self.fname, 'r') as f:
            self.parse(f)
        return self.diffs


if __name__ == '__main__':
    # Ugly, just to do a quick test
    import sys
    filename = sys.argv[1]
    p = DiffParser(filename)
    for (resource_diff, content_diff) in p.run():
        print "## BEGIN RESOURCE"
        print resource_diff
        if content_diff:
            print '-- '
            print content_diff
        print "## END RESOURCE "
