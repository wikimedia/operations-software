'''
This script is around primarily for three reasons:

1. I want to see which hosts have X of prod/labs/beta and
   am too lazy to hop over there to look

2. I want to do an ssh or scp loop on that set of hosts from
   here (laptop at home).

3. I want to do some action on all salt non-responsive hosts,
   also ssh from laptop.

Here's an example of the stuff I want to be able to do:

ssh bastion-restricted.wmflabs.org ssh -l root \
     -o 'StrictHostKeyChecking=no' somehost \
     "ls -lt /var/log/salt/minion"
'''

import sys
import getopt
from subprocess import Popen, PIPE
import ast


MASTERS = {'prod': 'neodymium.eqiad.wmnet',
           'labs': 'labcontrol1001.wikimedia.org',
           'beta': 'deployment-saltmaster.deployment-prep.eqiad.wmnet',
           'mine': 'salt-jessie.salt.eqiad.wmflabs'}


DEBUG = True


def get_saltmaster(realm):
    '''
    get and return the fqdn of the saltmaster
    for the specified realm
    '''
    if realm in MASTERS:
        return MASTERS[realm]
    else:
        return None


def get_target_args(target, target_type):
    '''
    turn the target and target type into salt args
    and return them
    '''
    if target_type == 'glob' or target_type == 'mia':
        return ["'" + target + "'"]
    elif target_type == 'grain':
        return ['-G', target]
    elif target_type == 'list':
        return ['-L', target]
    elif target_type == 'facter':
        return ["'*'"]
    else:
        return None


def get_target_command(target, target_type):
    '''
    assemble salt command to get the returns we
    want, based on target and target_type
    '''
    if target_type == 'facter':
        command = ['cmd.run', "'facter %s'" % target.split(':')[0]]
    elif target_type == 'grain':
        command = ['test.ping']
        command.extend(target.split(':'))
    elif (target_type == 'list' or target_type == 'glob' or
          target_type == 'mia'):
        command = ['test.ping']
        if target_type == 'mia':
            command.append('-v')
    else:
        command = None
    return command


def get_salt_responders(output, match_value=None, match_start=None):
    '''
    if there is a match_string supplied in the form name:value
    then only those hostnames responding with that value
    in the response will be reported

    otherwise all hosts that responded will be reported
    '''
    if DEBUG:
        print output
    lines = output.splitlines()
    minions_good = []
    for line in lines:
        if not line.startswith('{'):
            # there might be header lines with the JID
            continue
        entry = ast.literal_eval(line)
        minions = entry.keys()
        for minion in minions:
            if (match_value is not None and
                    isinstance(entry[minion], basestring) and
                    entry[minion] == match_value):
                minions_good.append(minion)
            elif (match_start is not None and
                  isinstance(entry[minion], basestring) and
                  entry[minion].startswith(match_start)):
                minions_good.append(minion)
            elif match_value is None and match_start is None:
                minions_good.append(minion)
    return minions_good


def get_target_list(target, target_type, realm):
    '''
    given target string (host expr), target type (glob, list, etc)
    and realm (labs, prod, etc) get the list of responsive
    hosts that match, or in the case where target type is 'mia'
    get hosts that don't respond
    '''
    command = ['ssh', get_saltmaster(realm), "sudo", "salt"]
    command.extend(get_target_args(target, target_type))
    command.extend(["--out", "raw"])
    command.extend(get_target_command(target, target_type))

    if DEBUG:
        print command
    proc = Popen(command, stderr=PIPE, stdout=PIPE)
    output, error = proc.communicate()
    if proc.returncode:
        sys.stderr.write("failed to retrieve target list,"
                         " retcode %d\n" % proc.returncode)
        sys.stderr.write("command run was ")
        sys.stderr.write(" ".join(command))
        sys.stderr.write("\n")

        if error is not None:
            sys.stderr.write(error)
            sys.stderr.write("\n")
        if output is not None:
            sys.stderr.write(output)
            sys.stderr.write("\n")
        sys.exit(1)
    if target_type == 'facter':
        match_value = target.split(':')[1]
        results = get_salt_responders(output, match_value=match_value)
    elif target_type == 'mia':
        results = get_salt_responders(
            output, match_start='Minion did not return')
    else:
        results = get_salt_responders(output)
    return results


def get_command_prefix(realm, ssh=None):
    '''
    depending on realm, get the command prefix that
    sets up the right ssh proxying
    '''
    # FIXME get the right strings in here in the
    # right place in the command later toooooo
    prefix = None
    if ssh == 'scp':
        if realm == 'prod':
            prefix = []
        elif realm == 'labs' or realm == 'mine':
            prefix = []
        elif realm == 'beta':
            prefix = []
    elif ssh == 'ssh':
        if realm == 'prod':
            prefix = ['ssh']
        elif realm == 'labs' or realm == 'mine':
            prefix = ["ssh", "-A", "bastion-restricted.wmflabs.org"]
        elif realm == 'beta':
            prefix = ["ssh", "-A", "bastion-restricted.wmflabs.org",
                      "ssh", "-A", "deployment-bastion"]
    return prefix


def run_command(hostname, command, realm, dryrun):
    '''
    run command on remote host or print what
    would have been run
    '''
    full_command = get_command_prefix(realm, command[0])
    # ["ssh", "-A", "bastion-restricted.wmflabs.org"]

    command = [field if field != 'minion' else hostname for field in command]
    full_command.extend(command)

    if dryrun:
        print("on", hostname, "would run", full_command)
        return

    proc = Popen(full_command, stderr=PIPE, stdout=PIPE)
    output, error = proc.communicate()
    print "retcode:", proc.returncode
    if error is not None:
        print "error:", error
    if output is not None:
        print "output:", output
    return


def usage(message=None):
    '''
    display a helpful usage message with
    an optional introductory message first
    '''
    if message is not None:
        sys.stderr.write(message)
        sys.stderr.write("\n")
    usage_message = """
Usage: do-ssh-commands.py --target <string>
         [--type glob|list|facter|grain]
         [--realm prod|labs|beta] [--dryrun]
         command arg1 arg2....'minion' ...argn
OR     do-ssh-commands.py --help

The command that follows the regular arguments
must have the string 'minion' somewhere in it;
this will be replaced with the name of each host
as the command is executed.

If no command is specified, the target list will
be displayed.

Examples:

do_ssh_commands.py --target lsbdistcodename:precise
    --type facter --realm beta ssh minion uptime

do_ssh_commands.py --target 'bast*'
    --realm prod scp ~/.bashrc minion:/home/hardworker/.bashrc

do_ssh_commands.py --target 'mw*'
    --type mia --realm prod

Options:

  --target (-t): string identifying the hosts to be
                 targeted by the command. See --type
                 below.
  --type   (-T): glob:   the target is a string with a
                         possible wildcard in it
                         or regexp
                 list:   the target is a comma-separated
                         list of hosts
                 grain:  the target is of the form grainname:value
                 facter: the target is of the form factername:value
                 mia:    hosts that don't respond to test.ping
                         in this case the target must be a
                         string with a possible wildcard in it
                 (default: glob)
  --realm  (-r): which cluster to check. Known values: prod, labs, beta
                 (default: prod)
  --dryrun (-d): display the commands that would be run to produce
                 the output but don't actually run them
  --help    (-h):  display this message
"""
    sys.stderr.write(usage_message)
    sys.exit(1)


def main():
    '''
    entry point, does all the work
    '''
    target = None
    target_type = 'glob'
    realm = 'prod'
    dryrun = False
    command = None

    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "t:T:r:dh",
            ["target=", "type=", "realm=", "dryrun", "help"])
    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))
    for (opt, val) in options:
        if opt in ["-t", "--target"]:
            target = val
        elif opt in ["-T", "--type"]:
            target_type = val
        elif opt in ["-r", "--realm"]:
            realm = val
        elif opt in ["-d", "--dryrun"]:
            dryrun = True
        elif opt in ["-h", "--help"]:
            usage('Help for this script\n')
        else:
            usage("Unknown option specified: <%s>" % opt)

    if len(remainder):
        command = remainder

    if target is None:
        usage("Mandatory argument 'target' not specified")

    todo = get_target_list(target, target_type, realm)

    if command is None:
        print todo
        return

    for hostname in todo:
        run_command(hostname, command, realm, dryrun)


if __name__ == "__main__":
    main()
