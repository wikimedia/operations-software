import os
import sys
import stat
import json

sys.path.append('/srv/audits/retention/scripts/')

from retention.saltclientplus import LocalClientPlus
import retention.utils
from retention.utils import JsonHelper
from retention.fileinfo import FileInfo, EntryInfo


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
        client = LocalClientPlus()
        module_args = [self.path,
                       self.num_lines,
                       self.timeout]

        result = client.cmd([self.host],
                            "retentionaudit.examine_file",
                            module_args, expr_form='list',
                            timeout=self.timeout)

        if self.host in result:
            if not self.quiet:
                print result[self.host]
            return result[self.host]


class LocalFileExaminer(object):
    '''
    retrieval and display of file contents on local host
    '''
    def __init__(self, path, num_lines, timeout=20, quiet=False):
        self.path = path
        self.timeout = timeout
        self.num_lines = num_lines
        self.quiet = quiet

    def run(self):
        '''
        do all the work
        '''
        finf = FileInfo(self.path, None)
        if finf.get_is_binary(self.num_lines):
            result = "BINARY CONTENT\n"
        else:
            result = finf.start_content
        if not self.quiet:
            print result,
        return result


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

        if retention.utils.running_locally(self.host):
            dcont = DirContents(self.path, self.batchno, self.batchsize,
                                self.prettyprint)
            result = dcont.get_contents()
            if result != 'ok':
                print ('WARNING: failed to get directory contents'
                       'for <%s> (%s)'
                       % (self.path, result))
            else:
                dcont.get_batch_entryinfo()
                dcont.show_batch()
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


