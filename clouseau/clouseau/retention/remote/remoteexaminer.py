import json

from salt.client import LocalClient
from clouseau.retention.utils.utils import JsonHelper
from clouseau.retention.utils.fileinfo import EntryInfo

class RemoteFileExaminer(object):
    '''
    retrieval and display of file contents on remote host
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
        client = LocalClient()
        module_args = [self.path,
                       self.num_lines]

        result = client.cmd([self.host],
                            "retentionaudit.examine_file",
                            module_args, expr_form='list',
                            timeout=self.timeout)

        if self.host in result:
            if not self.quiet:
                print result[self.host]
            return result[self.host]


class RemoteDirExaminer(object):
    '''
    retrieval and display of directory contents on remote host
    '''
    def __init__(self, path, host, batchno=1, batchsize=300, timeout=20,
                 prettyprint=False):
        self.path = path
        self.stat = None
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

        while True:
            client = LocalClient()
            module_args = [self.path, self.batchno,
                           self.batchsize, quiet]

            result = client.cmd([self.host],
                                "retentionaudit.examine_dir",
                                module_args, expr_form='list',
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
