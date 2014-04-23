from . import app, parser, diff2html
import os
import subprocess
import shlex
from collections import defaultdict
from subprocess import CalledProcessError


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
    print "Building diffs for node %s" % nodename
    diff_cmd = '{} {} {} {}'.format(
        app.config.get('DIFF_SCRIPT'),
        nodename,
        app.config.get('COMPILE_OUTPUT_DIR'),
        app.config.get('DIFF_DIR')
    )

    ruby(diff_cmd)
    return os.path.join(app.config.get('DIFF_DIR'), nodename + '.diff')


def main(node=None):
    if node is not None:
        gen = lambda: [n for n in node.split(',')]
    else:
        gen = get_nodes
    nodelist = defaultdict(list)
    for node in gen():
        print "Doing node {}".format(node)
        try:
            filename = compile_and_diff_node(node)
            p = parser.DiffParser(filename)
            diff = p.run()
        except CalledProcessError as e:
            print "Error running on node %s" % node
            nodelist['ERROR'].append(node)
            continue
        if not diff:
            print "No differences for node %s" % node
            nodelist['OK'].append(node)
            continue
        nodelist['DIFF'].append(node)
        with open(filename + '.formatted', 'w') as f:
            for (resource_diff, content_diff) in diff:
                f.write("-- \n\n")
                f.write(resource_diff)
                if content_diff != '':
                    f.write("\nContent Diff:\n")
                    f.write(content_diff)
        # Also save the html rendering
        text_diff = "\n".join([a + b for (a, b) in diff])
        html = os.path.join(app.config.get('HTML_DIR'), node + '.html')
        diff2html.stream_parse(
            txt=text_diff,
            output_file_name=html,
            enc='utf-8',
            show_cr=True,
            show_hunk_infos=True,
            fqdn=node
        )
    print "###\nRUN RESULTS:"
    for (k,v) in nodelist.items():
        print "%s => %d" % (k, len(v))


if __name__ == '__main__':
    main()
