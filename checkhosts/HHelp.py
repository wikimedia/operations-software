import os
import sys

"""All methods in this file return help message strings
with the exception of usage() and extendedUsage()
which both display usage messages and exit with a non-zero
exit code."""

def getCriteriaHelp():
    return """
A criterion is the string on the right side of an assertion.  Hosts from the
source list will be checked against the criterion to see if they match.
""" + getCriteriaKnown()

def getCriteriaValuesHelp():
    return """
A criterion value is a fixed string (as opposed to '*') which may or may
not be preceded by a '!'
""" + getCriteriaValuesKnown()

def getCriteriaKnown():
    return """
The following criteria are understood:

*         -- host is present in source list
value     -- host is present with specified value in source list
!*        -- host is absent from source list
!value    -- host is present in source list but does not have specified value
""" + getCriteriaValuesKnown()

def getCriteriaValuesKnown():
    return """
Known values:

For source 'salt': 'ping' matches hosts that respond to test.ping
For source 'dsh':  a dsh group filename matches hosts found in that file [only that one?]
For source 'logpuppet':
   'ok'        -- the latest full puppet run completed with no issues
   'nocatalog' -- the host failed to retrieve the puppet catalog
   'err'       -- puppet ran with errors
   'disabled'  -- puppet is administratively disabled on that host
   'unknown'   -- there is not enough information to determine the run status
For source 'puppet':
   fact:value  -- match only hosts with the specified fact having the given value
                  you can check the possibilities by running 'facter' at the command line
                  note that keys, passwords are excluded from this list
"""

def getSourcesHelp(knownSources):
    return """
A source is the string on the left side of an assertion.  Hosts from this
source will be checked to see if they match the assertion criteria.

Available sources are:
""" + " ".join(sorted(knownSources)) + "\n"

def getFilterHelp(knownSources):
    return """
A filter is a comma-separated list of assertions, where each assertion is of the form

<source>=<criterion>

<source> must be one of the following:
""" + " ".join(sorted(knownSources)) + "\n" + getCriteriaKnown()

def getReportHelp(knownSources):
    return """
A report showing a table of hosts with their attributes can be generated
based on a comma-separated list of requirements.

A requirement is used to determine which values for an attribute of
a host to display in a report.  It is of the form

<source>=<expr>;<expr><xpr>...  or
<source>!=<expr>;<expr><xpr>... or
<source>

where <expr> may be a string, requiring a complete match, or may have one glob
(*) which matches in the expected fashion.

If the first form is given, a value that matches any of the expressions will be displayed.
If the second form is given, only values that match none of the expressions will be displayed.
If the third form is supplied, all values will be displayed.
""" + """
Available sources are:
""" + " ".join(sorted(knownSources))

def getExamplesHelp():
    return """
Example usage (do not copy-paste, these hosts are not valid)

all mw hosts known to salt but not in mediawiki-installation dsh file:
python check-hosts.py --filter ''salt=*,dsh=!mediawiki-installation' \\
            --dsh fenari.wikimedia.org,/usr/local/dsh/groups

all hosts decommed in racktables but still in dns
python check-hosts.py --filter ''decomracktables=*,dns=*' \\
            --dns dobson.wikimedia.org,/etc/powerdns/zones

all hosts in dhcp but not responsive in puppet
python check-hosts.py -f 'dhcp=*,puppet=!*' \\
            --puppet localhost.localdomain,/etc/puppet/yaml/facts

all pmtpa.wmnet hosts in dns, and decommed in puppet, but not in dhcp
using default config file
python check-hosts.py --filter 'dns=*,dhcp=!*,decompuppet=*'

all mw hosts that claim to be administratively disabled in puppet, using
default config file
python check-hosts.py --filter 'logpuppet=disabled'

all mw host ip addresses except mgmt ones, using default config file
python check-hosts.py --report 'dns!=10.65*;10.1.*;10.128.*;10.1.*' -H 'mw*'
"""

def getOptionsHelp(knownSources):
    return """
Options:

--filter           (-f): filter hosts according to a set of assertions
                         This option, 'cli' and 'report' are mutually exclusive
--cli              (-C): prompt for and read filters from user, displaying matching
                         hosts for each criterion before prompting for the next one
                         This option, 'report' and 'filter' are mutually exclusive
--report           (-R): report host attributes according to a set of requirements
                         This option, 'cli' and 'filter' are mutually exclusive
--dhcp             (-d): fqdn of host with dhcp files and full path to directory on
                         that host with the files, separated by a comma
                         default: dhcp.localdomain,/etc/dhcp3
--dsh              (-D): fqdn of host with dsh group files and full path to directory
                         on that host with the files, separated by a comma
                         by a comma
                         default: dshgroups.localdomain,/etc/dsh/group
--decomracktables  (-r): fqdn of racktables db server, dbname, db user, db password,
                         password retrieval plugin,plugin params, separated by a comma
                         default: racktablesddb.localdomain,racktables,racktables,,getpwdfromfile,
                                  /puppet/passwords/manifests/init.pp;$racktablespass
                         (no password, the password will be retrieved from a file)
                         NOTE: password will be visible in the process list on the host
                         where this script is run and and on the racktables db host
--decompuppet      (-p): fqdn of host with puppet decommissioned servers list and
                         path to the file (the file should comtain a declaration
                         "$decommissioned_servers = [ ... ]" across several lines),
                         separated by a comma
                         default: puppetserver.localdomain,/var/lib/puppet/decommissioning.pp
--puppet           (-P): fqdn of host with puppet facts files for currentnodes,
                         and path to the files, separated by a comma
                         default: puppetserver.localdomain,/var/lib/puppet/yaml/facts
--dns              (-n): fqdn of host with dns files and path to the files
                         default: dnsserver.localdomain,/etc/gdnsd/zones
--logpuppet        (-l): path to puppet log on each puppet client host
                         default: /var/log/puppet.log
--storedconfigs    (-s): fqdn of host with puppet stored configs, db name, db user, db
                         password,password retrieval plugin, plugin params, separated by a comma
                         default: puppetdb.localdomain,puppet,puppet,,getpwdfromfile,
                                  /etc/puppet/puppet.conf;puppetpassword
                         (no password, the password will be retrieved from a file)
--puppetcerts      (-Q): fqdn of host with puppet client certs, and full path to directory
                         on that host with the certs, separated by a comma
                         default: puppetserver.localdomain,/var/lib/puppet/server/ssl/ca/signed
--hosts            (-H): comma-separated list of expressions (short hostnames, not fqdn) to
                         check hostnames against, each expression either a fixed string, in
                         which case that specific host will be reported if it matches the
                         filters, or a string with a glob (*) in it
--config           (-c): path to configfile
                         default: checkhosts.conf
--timeout          (-t): timeout in seconds for remote commands to complete
--help             (-h): display a short usage message and exit
--extendedhelp     (-e): display extended help and exit
--verbose          (-v): display various progress messages
--version          (-V): display the program's version and exit
"""

def getShortUsageHelp():
    return """
Usage: python check-hosts.py --filter filterstring|--cli|--report <sourcelist>
                 [--dhcp <host>,<path>] [--dsh <host>,<path>]
                 [--decomracktables <host>,<db>,<user>,<password>]
                 [--decompuppet <host>,<path>] [--puppet <host>,<path>]
                 [--dns <host>,<path>] [--logpuppet <path>]
                 [--storedconfigs <host>,<db>,<user>,<password>]
                 [--puppetcerts <host>,<path>]
                 [--config filename] [--timeout <numsecs>]
                 [--help] [--extendedhelp] [--verbose] [--version]

This script retrieves lists of hosts known to e.g. dhcp, dsh, salt, puppet decommissioned
list, racktable decommissioned list, and displays all hosts that meet the specified filter
assertions, or displays attributes of hosts that meet the specified report requirements.
"""

def usage(message):
    """Arguments:
    message   -- display this message, with newline added, before
    the standard help output."""
    if message:
        sys.stderr.write(message)
        sys.stderr.write("\n")
        sys.stderr.write(getShortUsageHelp())
        sys.stderr.write("For more detailed help, run this script with the --extendedhelp option.\n")
        sys.exit(1)

def extendedUsage(knownSources):
    """Display extended help on all options to stderr and exit."""

    usageMessage = getShortUsageHelp() + getFilterHelp(knownSources) + """
Hosts must meet all assertions to be displayed (assertions are 'anded').

Note that if you specify a bunch of '<source>=!*' with no other assertions, this
script will give you an empty list.  It must have at least *one* sourcelist from
which some hosts are selected, before it can check them to see if they are not
present elsewhere.
""" + getReportHelp(knownSources) + "\n" + getOptionsHelp(knownSources) + getExamplesHelp()

    sys.stderr.write(usageMessage)
    sys.exit(1)
