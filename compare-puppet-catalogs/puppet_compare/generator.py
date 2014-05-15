from . import app, parser, diff2html, nodegen, threads
import os
import subprocess
import shlex
from collections import defaultdict
from subprocess import CalledProcessError
from jinja2 import Environment, PackageLoader
import requests
import logging
import json
import sys

log = logging.getLogger('puppet_compare')

env = Environment(loader=PackageLoader('puppet_compare', 'templates'))


def run(cmd, sudo=False, sudo_user='root', capture=True):
    env = os.environ.copy()
    if sudo:
        cmd = "sudo -E -u %s '%s'" % (sudo_user, cmd)

    cmdlist = shlex.split(cmd)

    if capture:
        method = subprocess.check_output
    else:
        # This just works in python 2.7. Wrap this again?
        method = subprocess.check_call

    return method(cmdlist, env=env)


def ruby(cmd, **kwdargs):
    return run(cmd, **kwdargs)


def get_nodes():
    log.info("Walking dir %s", app.config.get('NODE_DIR'))
    for subdir in os.walk(app.config.get('NODE_DIR')):
        nodelist = subdir[2]
        for node in nodelist:
            log.debug('Processing  node %s' % node)
            yield node.replace('.yaml', '')


def diff_save(fname, diff):
    with open(fname + '.formatted', 'w') as f:
        for (resource_diff, content_diff) in diff:
            f.write("-- \n\n")
            f.write(resource_diff)
            if content_diff != '':
                f.write("\nContent Diff:\n")
                f.write(content_diff)


class NodeDiffPuppetVersions(object):

    """
    Computes the catalog diff for the production branch between puppet 2.7
    and puppet 3
    """

    def __init__(self, args):
        self.compiled_dir = app.config.get('COMPILE_OUTPUT_DIR')
        self.html_dir = app.config.get('HTML_DIR')
        self.diff_dir = app.config.get('DIFF_DIR')
        self.compile_versions = app.config.get('PUPPET_VERSIONS')
        self.nodes = args.nodes
        self.nodelist = defaultdict(set)
        self.count = 0
        self.change = None
        self.site_pp = os.path.join(app.config.get('BASEDIR'),
                                    'external/puppet/manifests/site.pp')
        self.tp_size = args.numthreads
        self.mode = 'versions'

    def node_compile(self, nodename, version, branch):
        log.info("Compiling node %s under puppet %s branch %s",
                 nodename, version, branch)
        # Compile
        cmd = '{} {} {} {} {}'.format(
            app.config.get('COMPILE_SCRIPT'),
            version,
            nodename,
            self.compiled_dir,
            branch
        )

        log.debug('Compile command: %s', cmd)
        ruby(cmd)

    def node_diff(self, nodename):
        log.info("Building diffs for node %s" % nodename)
        old_termination = 'puppet_catalogs_%s_%s' % self.compile_versions[0]
        new_termination = 'puppet_catalogs_%s_%s' % self.compile_versions[1]
        old_dir = os.path.join(self.compiled_dir, old_termination)
        new_dir = os.path.join(self.compiled_dir, new_termination)
        cmd = '{} {} {} {} {}'.format(
            app.config.get('DIFF_SCRIPT'),
            nodename,
            self.diff_dir,
            old_dir,
            new_dir
        )
        ruby(cmd)
        return os.path.join(self.diff_dir, nodename + '.diff')

    def update_index(self):
        t = env.get_template('index.jinja2')
        with open(os.path.join(self.html_dir, 'index.html'), 'w') as f:
            f.write(t.render(nodes=self.nodelist))

    def _write_node_page(self, nodename, txt, is_error=False, is_ok=False):
        template = 'htmldiff.jinja2'
        output = None
        html = os.path.join(self.html_dir, nodename + '.html')

        if is_error:
            template = 'compile_error.jinja2'
        elif is_ok:
            template = 'node_ok.jinja2'
        else:
            output = diff2html.parse_input(txt, html, True)

        t = env.get_template(template)
        change = self.change and self.change or 'production'
        with open(html, 'w') as fh:
            fh.write(
                t.render(
                    lang=diff2html.lang,
                    charset='utf-8',
                    fqdn=nodename,
                    data=output,
                    change=change,
                    mode=self.mode
                )
            )

    def node_generator(self):
        if self.nodes is not None:
            return [n for n in self.nodes.split(',')]
        else:
            with open(self.site_pp, 'r') as f:
                n = nodegen.NodeFinder(f)
                return n.match_physical_nodes(get_nodes())

    def on_node_compiled(self, msg):
        node = msg['data'][0][0]
        self.count += 1
        if not self.count % 5:
            log.info('Updating index.html')
            self.update_index()
        log.info("Nodes: %s OK %s DIFF %s FAIL" % (
            len(self.nodelist['OK']),
            len(self.nodelist['DIFF']),
            len(self.nodelist['ERROR'])
        ))

    def node_output(self, node):
        if node in self.nodelist['ERROR']:
            log.info('Node %s had compilation problems', node)
            self._write_node_page(node, '', is_error=True,)
            return

        filename = self.node_diff(node)
        p = parser.DiffParser(filename)
        diff = p.run()

        # If compilation is successful and no diffs, go on.
        if not diff:
            log.info("No differences for node %s", node)
            self._write_node_page(node, '', is_ok=True)
            self.nodelist['OK'].add(node)
            return

        # If diff is present, render it.
        self.nodelist['DIFF'].add(node)
        diff_save(filename, diff)
        # Also save the html rendering
        text_diff = "\n".join([a + b for (a, b) in diff])
        self._write_node_page(node, text_diff)

    def _run_node(self, node):
        for (puppet_version, branch) in self.compile_versions:
            try:
                self.node_compile(node, puppet_version, branch)
            except Exception as e:
                log.error("Error in compilation on node %s", node)
                log.error("Exception was: %s", str(e))
                self.nodelist['ERROR'].add(node)
        self.node_output(node)

    def run(self):
        threadpool = threads.ThreadOrchestrator(self.tp_size)
        for node in self.node_generator():
            threadpool.add(self._run_node, node)

        threadpool.fetch(self.on_node_compiled)
        self.update_index()


class NodeDiffChange(NodeDiffPuppetVersions):

    """
    Computes the catalog diff between the production branch and a changeset
    in puppet 2.7
    """

    def __init__(self, args):
        super(NodeDiffChange, self).__init__(args)
        self.change = args.change
        basedir = os.path.join(
            app.config.get('OUTPUT_DIR'), 'change', str(self.change))
        self.compiled_dir = os.path.join(basedir, 'compiled')
        self.html_dir = os.path.join(basedir, 'html')
        self.diff_dir = os.path.join(basedir, 'diff')
        self.compile_versions = [('2.7', 'production'), ('2.7', self.change)]
        self.site_pp = os.path.join(
            app.config.get('BASEDIR'),
            'external/change/%d/puppet/manifests/site.pp' % self.change)
        self.mode = 'diffchanges'

    def run(self):
        self.prepare_change()
        super(NodeDiffChange, self).run()

    def prepare_change(self):
        # First, get info on the change.

        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json; charset=UTF-8'}
        change = requests.get(
            'https://gerrit.wikimedia.org/r/changes/%d?o=CURRENT_REVISION' % self.change, headers=headers)
        if change.status_code != 200:
            raise ValueError(
                "Got a %s status code from the server, check your change id" %
                change.status_code
            )
        # Workaround the broken gerrit response...
        json_data = change.text.split("\n")[-2:][0]
        res = json.loads(json_data)
        revision = res["revisions"].values()[0]["_number"]
        cmd = "{} {} {}".format(
            app.config.get('FETCH_CHANGE'), self.change, int(revision))
        log.info(
            'Downloading patch for change %s, revision %s', self.change, revision)
        run(cmd)


class NodeVersionsChange(NodeDiffChange):

    """
    Computes the catalog diff for a changeset between different puppet versions
    """

    def __init__(self, args):
        super(NodeVersionsChange, self).__init__(args)
        self.compile_versions = [('2.7', self.change), ('3', self.change)]
        self.mode = 'versions'

if __name__ == '__main__':
    main()
