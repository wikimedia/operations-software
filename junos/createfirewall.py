#!/usr/bin/python

"""Convert exported Puppet resources into JunOS SLAX a firewall filter.

<More details go here>

"""

import os
import sys
import csv
import os.path
import datetime
import filters

# version 1.0;
# ns junos = "http://xml.juniper.net/junos/*/junos";
# ns xnm = "http://xml.juniper.net/xnm/1.1/xnm";
# ns jcs = "http://xml.juniper.net/junos/commit-scripts/1.0";
# import "../import/junos.xsl";

#file parameters defined here
outputfile = "test.slax"
sourcedir = "/Users/lcarr/firewall_python/test"
standard_headers = [
    '# This file should live in /var/db/scripts.',
    'version 1.0;',
    ''
    'ns junos = "http://xml.juniper.net/junos/*/junos";',
    'ns xnm = "http://xml.juniper.net/xnm/1.1/xnm";',
    'ns jcs = "http://xml.juniper.net/junos/commit-scripts/1.0";',
    'import "../import/junos.xsl";']


def file_header():
    timestamp = datetime.datetime.now()
    return '\n'.join(
        ['# File automatically created at ' + str(timestamp)] +
        standard_headers) + '\n'

# The standard opening directives for the SLAX firewall configuraation:
SLAX_DIRECTIVES = ('match configuration',
              '<change>')

def slax_header():
    # Assumptions:
    # - every line needs to end in a "{"
    # - every line must be indented an additional tab. (first = none).
    parts = []
    tabs = 0
    for line in SLAX_DIRECTIVES:
        parts.append('\t' * tabs + line + ' {')
        tabs += 1
    return parts, tabs


def slax_footer():
    # Assumptions:
    # - everything in SLAX_DIRECTIVES needs a closing "}"
    # - every line must be indented a descending number of tabs 
    parts = []

    # This should end at 0, not 1, so substract 1 to start.
    tabs = len(SLAX_DIRECTIVES) - 1
    for line in reversed(SLAX_DIRECTIVES):
        parts.append('\t' * tabs + '}')
        tabs -= 1
    return parts


def main(args):
    """Generate junos firewall rules from a sourcedir.

    Args:
        output file: str, filename to write the rules into.
        source dir: str, directory to read inputs from.
    """
    if len(args) >= 2:
        sourcedir = args[1]

    if len(args) >= 1:
        outputfile = args[0]

    # First write the generic information to the top of the file
    try:
        output = open(outputfile, 'w', 0)
        output.write(file_header())
    except IOError, e:
        print('output file (%s) has problems: %s.' % (outputfile, e))
        return 1

    # Then we start the actual code bits
    header, tab_depth = slax_header()
    output.write('\n'.join(header) + '\n')

    # Now we need to take the various inputs in the directory and make them
    # into slax terms
    try:
        files = os.listdir(sourcedir)
    except OSError, e:
        print('Error reading directory %s: %s' % (sourcedir, e))

    firewall = filters.Firewall()
    fw_filter = filters.Filter('inbound-auto')
    firewall.filters.append(fw_filter)
    
    for f in files:
        fh = open(os.path.join(sourcedir, f))
        name, ip, port = fh.readlines()[0].rstrip().split(',')
        term = filters.Term('%s_%s' % (name, port))
        term.destination_addr.append(ip)
        term.destination_port.append(port)
        fw_filter.terms.append(term)

    parts = filters.TabExtend(firewall.GetRuleParts(), tab_depth)
    output.write('\n'.join(parts) + '\n')

    # Now we complete and close our configuration bit
    output.write('\n'.join(slax_footer()) + '\n')

    # At the very very end, close the file
    output.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        args = []
    sys.exit(main(args))
