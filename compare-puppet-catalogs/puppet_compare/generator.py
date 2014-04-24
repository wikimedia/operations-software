from . import app, parser, diff2html
import os
import subprocess
import shlex
from collections import defaultdict
from subprocess import CalledProcessError
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('puppet_compare', 'templates'))

def bootstrap():
    # initialize things here
    pass


def run(cmd, sudo=False, sudo_user='root', capture=True):
    if sudo:
        cmd = "sudo -u %s '%s'" % (sudo_user, cmd)

    cmdlist = shlex.split(cmd)

    if capture:
        method = subprocess.check_output
    else:
        # This just works in python 2.7. Wrap this again?
        method = subprocess.check_call

    return method(cmdlist)


def ruby(cmd, **kwdargs):
    return run(
        '/usr/local/rvm/bin/rvm {} do {}'.format(app.config.get('RUBY_VERSION', '1.8.7'), cmd), **kwdargs)


def get_nodes():
    print "Walking dir %s" % app.config.get('NODE_DIR')
    for subdir in os.walk(app.config.get('NODE_DIR')):
        nodelist = subdir[2]
        for node in nodelist:
            yield node.replace('.yaml', '')


def compile_and_diff_node(nodename):
    node_compile(nodename)
    return node_diff(nodename)


def node_compile(nodename):
    for puppet_version in app.config.get('PUPPET_VERSIONS'):
        print "Compiling node %s under puppet %s" % (nodename, puppet_version)
        # Compile
        cmd = '{} {} {} {}'.format(
            app.config.get('COMPILE_SCRIPT'),
            puppet_version,
            nodename,
            app.config.get('COMPILE_OUTPUT_DIR')
        )
        ruby(cmd)

def node_diff(nodename):
    print "Building diffs for node %s" % nodename
    diff_cmd = '{} {} {} {}'.format(
        app.config.get('DIFF_SCRIPT'),
        nodename,
        app.config.get('COMPILE_OUTPUT_DIR'),
        app.config.get('DIFF_DIR')
    )

    ruby(diff_cmd)
    return os.path.join(app.config.get('DIFF_DIR'), nodename + '.diff')

def update_index(nodelist):

    t = env.get_template('index.jinja2')
    with open(os.path.join(app.config.get('HTML_DIR'), 'index.html'), 'w') as f:
        f.write(t.render(nodes=nodelist))

def write_node_page(node, txt, is_error=False, is_ok=False, **kwdargs):
    html = os.path.join(app.config.get('HTML_DIR'), node + '.html')
    template = 'htmldiff.jinja2'
    output = None

    if is_error:
        template = 'compile_error.jinja2'
    elif is_ok:
        template = 'node_ok.jinja2'
    else:
        output = diff2html.parse_input(txt, html, True)

    t = env.get_template(template)
    with open(html, 'w') as fh:
        fh.write(
            t.render(
                lang=diff2html.lang,
                charset='utf-8',
                fqdn=node,
                data=output
            )
        )


def diff_save(fname, diff):
    with open(fname + '.formatted', 'w') as f:
        for (resource_diff, content_diff) in diff:
            f.write("-- \n\n")
            f.write(resource_diff)
            if content_diff != '':
                f.write("\nContent Diff:\n")
                f.write(content_diff)


def main(nodes=None):
    count = 0
    if nodes is not None:
        gen = lambda: [n for n in nodes.split(',')]
    else:
        gen = get_nodes
    nodelist = defaultdict(list)
    for node in gen():
        count += 1
        if not count % 10:
            update_index(nodelist)
        print "Doing node {}".format(node)
        # If compilation or diff fails, build a report page
        # for a node with errors.
        try:
            node_compile(node)
            filename = node_diff(node)
            p = parser.DiffParser(filename)
            diff = p.run()
        except CalledProcessError:
            print "Error in compilation on node %s" % node
            write_node_page(node, '', is_error=True)
            nodelist['ERROR'].append(node)
            continue

        # If compilation is successful and no diffs, go on.
        if not diff:
            print "No differences for node %s" % node
            write_node_page(node, '', is_ok=True)
            nodelist['OK'].append(node)
            continue

        # If diff is present, render it.
        nodelist['DIFF'].append(node)
        diff_save(filename, diff)
        # Also save the html rendering
        text_diff = "\n".join([a + b for (a, b) in diff])
        write_node_page(node, text_diff)

    print "###\nRUN RESULTS:"
    for (k,v) in nodelist.items():
        print "%s => %d" % (k, len(v))
    update_index(nodelist)

if __name__ == '__main__':
    main()
