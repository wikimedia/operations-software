#!/usr/bin/python

"""Convert exported Puppet resources into JunOS SLAX a firewall filter.

Authors: Ryan Anderson <ryan@michonline.com>, Leslie Carr <lcarr@wikimedia.org>
Copyright (c) 2012 Wikimedia Foundation
License: Released under the GPL v2 or later.
For a full description of the license, please visit http://www.gnu.org/licenses/gpl-2.0.html
"""

import os
import sys
import os.path
import datetime
import filters
import argparse

# version 1.0;
# ns junos = "http://xml.juniper.net/junos/*/junos";
# ns xnm = "http://xml.juniper.net/xnm/1.1/xnm";
# ns jcs = "http://xml.juniper.net/junos/commit-scripts/1.0";
# import "../import/junos.xsl";

#file parameters defined here
standard_headers = [
    '/* This file should live in /var/db/scripts/commit */',
    'version 1.0;',
    ''
    'ns junos = "http://xml.juniper.net/junos/*/junos";',
    'ns xnm = "http://xml.juniper.net/xnm/1.1/xnm";',
    'ns jcs = "http://xml.juniper.net/junos/commit-scripts/1.0";',
    'import "../import/junos.xsl";']

def file_header():
    timestamp = datetime.datetime.now()
    return '\n'.join(
        ['/* # File automatically created at ' + str(timestamp) + '*/'] +
        standard_headers) + '\n'

# The standard opening directives for the SLAX firewall configuraation:
SLAX_DIRECTIVES = ('match configuration',
                   '<change>')

def slax_header():
    # Assumptions:
    # - every line needs to end in a "{"
    # - every line must be indented an additional level. (first = none).
    parts = []
    indent_level = 0
    for line in SLAX_DIRECTIVES:
        parts.append(' ' * indent_level * 2 + line + ' {')
        indent_level += 1
    return parts, indent_level


def slax_footer():
    # Assumptions:
    # - everything in SLAX_DIRECTIVES needs a closing "}"
    # - every line must be indented a descending number of double spaces
    parts = []

    # This should end at 0, not 1, so substract 1 to start.
    indent_level = len(SLAX_DIRECTIVES) - 1
    for line in reversed(SLAX_DIRECTIVES):
        parts.append(' ' * indent_level * 2 + '}')
        indent_level -= 1
    return parts


def main():
    """Generate junos firewall rules from a sourcedir.

    Args:
        source dir: str, directory to read inputs from.
        output file: str, filename to write the rules into.
    """
    parser = argparse.ArgumentParser(description=
                                     'Converts puppet resources to junos SLAX')
    parser.add_argument('sourcedir', help='Source directory with files')
    parser.add_argument('outputfile', help='Output SLAX file')

    args = parser.parse_args()

    # First write the generic information to the top of the file
    try:
        output = open(args.outputfile, 'w', 0)
        output.write(file_header())
    except IOError, e:
        print('output file (%s) has problems: %s.' % (args.outputfile, e))
        return 1

    # Then we start the actual code bits
    header, indent_depth = slax_header()
    output.write('\n'.join(header) + '\n')

    # Now we need to take the various inputs in the directory and make them
    # into slax terms
    try:
        files = os.listdir(args.sourcedir)
    except OSError, e:
        print('Error reading directory %s: %s' % (args.sourcedir, e))

    firewall = filters.Firewall()
    fw_filter = filters.Filter('inbound-auto')
    firewall.filters.append(fw_filter)

    # Map (port, protocol) -> [list of ip]
    by_port_protocol = {}

    for f in files:
        fh = open(os.path.join(args.sourcedir, f))
        # TODO: A CSV parser might be reasonable here.
        for line in fh.readlines():
            name, ip, protocol, port = line.rstrip().split(',')
            by_port_protocol.setdefault((port, protocol), []).append(ip)
        fh.close()

    for (port, protocol), ips in by_port_protocol.iteritems():
        term = filters.Term('port_%s_%s_v4' % (port, protocol))
        for ip in ips:
            term.destination_addr.append(ip)
        term.destination_port.append(port)
        term.protocol = protocol
        fw_filter.terms.append(term)

    parts = filters.IndentExtend(firewall.GetRuleParts(), indent_depth)
    output.write('\n'.join(parts) + '\n')

    # Now we complete and close our configuration bit
    output.write('\n'.join(slax_footer()) + '\n')

    # At the very very end, close the file
    output.close()


if __name__ == '__main__':
    sys.exit(main())
