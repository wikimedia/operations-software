'''
this script checks the status of salt on a box
and does some fixups; used primarily in labs
because things get out of hand there really fast
'''

import os
import sys
import getopt
import time
from subprocess import Popen, PIPE

# any minion older than 30 minutes was not just
# spawned for a job now.
OLD_PROC = 1800

# logs older than 90 minutes can be ignored
OLD_LOG = 5400

LOGFILE = "/var/log/salt/minion"

UPSTART = "/sbin/start"
SYSTEMCTL = "/bin/systemctl"
SALT_VERSION = "2014.7.5"
MASTERS = ['labs-puppetmaster-eqiad.wikimedia.org',
           'labs-puppetmaster-codfw.wikimedia.org',
           'labcontrol2001.wikimedia.org']
SALTCONF = "/etc/salt/minion"
SALT_KEYSIZE = "2048"
SALT_MINION_KEY = "/etc/salt/pki/minion/minion.pem"
SALT_MINION_PUB = "/etc/salt/pki/minion/minion.pub"

PUPPET_MASTER = 'labs-puppetmaster-eqiad.wikimedia.org'
PUPPETCONF = "/etc/puppet/puppet.conf"


def check_master():
    '''
    make sure all masters listed in
    salt config are actually masters
    '''
    masters = get_masters()
    if not masters:
        return False
    for entry in masters:
        if entry not in MASTERS:
            return False
    return True


def get_masters():
    '''
    extract a list of salt masters that the minion will respond to,
    from its salt config file
    '''
    contents = open(SALTCONF, "r").read()
    lines = contents.splitlines()
    masters = []
    want_master = False
    for line in lines:
        if line.startswith("master:"):
            if not line[8:]:
                # master:
                # - labs-puppetmaster-eqiad.wikimedia.org
                # - labs-puppetmaster-codfw.wikimedia.org
                # and this terminates as soon as we see a line with non
                # whitespace first char.
                want_master = True
            else:
                masters.append(line[8:])
        elif want_master:
            stripped = line.lstrip()
            if stripped and stripped[0] == '-':
                master_name = stripped[1:].lstrip()
                masters.append(master_name)
            else:
                return masters
    return masters


def restart_salt():
    '''
    shoot all minions and start one
    '''
    shoot_salt_processes()
    start_salt_process()


def check_salt_auth_error():
    '''
    see if the salt minion log ends with the
    dreaded Authentication Error, usually a
    sign that the minion is hung
    '''
    if os.path.exists(LOGFILE):
        if time.time() - os.stat(LOGFILE).st_mtime > OLD_LOG:
            # not that current a message, whatever is in the log
            return False
        # now check contents
        contents = open(LOGFILE, "r").read()
        if not contents:
            return False
        lines = contents.splitlines()
        if lines[-1].startswith("AuthenticationError: "):
            return True
    return False


def apt_update(verbose):
    '''
    apt-get update and display the results
    returns True on success, False on error

    ignores errors starting with W: (warnings)
    '''
    return get_popen_output(["apt-get", "update"], "W:", display=verbose)


def apt_install_dryrun(verbose):
    '''
    apt-get install dryrun for minion and display the results
    returns True on success, False on error
    '''
    return get_popen_output(["apt-get", "-y", "--simulate", "-o",
                             "DPkg::Options::=--force-confold",
                             "-o", "Apt::Get::AllowUnauthenticated=true",
                             "install", "salt-common", "salt-minion"],
                            display=verbose)


def apt_install(verbose):
    '''
    install salt minion package and deps via apt
    '''
    return get_popen_output(["apt-get", "-y", "--force-yes",
                             "-o", "DPkg::Options::=--force-confold",
                             "-o", "Apt::Get::AllowUnauthenticated=true",
                             "install", "salt-common", "salt-minion"],
                            display=verbose)


def fix_salt_version(verbose):
    '''
    kill all minions, try apt-get update and install of minion,
    start a minion afterwards if needed.
    if any step fails, will not proceed
    '''
    shoot_salt_processes()
    if apt_update(verbose):
        if apt_install_dryrun(verbose):
            apt_install(verbose)
    salt_processes = get_salt_processes()
    if not salt_processes:
        start_salt_process()


def get_popen_output(command, ignore=None, display=False, skipretcode=False):
    '''
    given a list with command and arguments,
    run it via Popen, returning lines of output
    on error, show errors and return None
    '''
    proc = Popen(command, stderr=PIPE, stdout=PIPE)
    output, error = proc.communicate()
    if not skipretcode and proc.returncode:
        print "Command:", command
        print "Errors:", error
        print "Output:", output
        return None

    if error and ignore is not None and not error.startswith(ignore):
        print error
        return None

    if display:
        print "INFO:", command, output
    return output.splitlines()


def get_salt_version():
    '''
    get the installed version of salt-minion via dpkg
    '''
    entries = get_popen_output(["dpkg", "-s", "salt-minion"])
    if not entries:
        return None
    for entry in entries:
        if entry.startswith("Version: "):
            return entry[9:]
    return None


def check_salt_version(version):
    '''
    check to be sure that the salt version
    passed to us is the version we expect
    on all hosts
    '''
    if version is None:
        return False
    if not version.startswith(SALT_VERSION):
        return False
    return True


def get_salt_processes():
    '''
    return list of pids of salt-minions running
    '''
    return get_popen_output(["pgrep", "salt-minion"], skipretcode=True)


def check_salt_processes(processes):
    '''
    if more than 1 such process that is
    not just now spawned to do a task,
    then more than one minion is running
    and processing requests, which we don't
    want

    return True if processes are all good
    return False if there's extra processes
    '''
    if len(processes) == 1:
        return True

    entries = get_popen_output(
        ["ps", "-p", ",".join(processes), "-o", "etimes="], skipretcode=True)
    for entry in entries:
        if int(entry) > OLD_PROC:
            return False
    return True


def do_popen(command):
    '''
    run a command, as a list, no shell, display
    output if any
    '''
    proc = Popen(command, stderr=PIPE, stdout=PIPE)
    output, error = proc.communicate()
    if error:
        print error
        return False
    if output:
        print output
    return True


def do_upstart():
    '''
    start salt-minion via upstart
    '''
    return do_popen([UPSTART, "salt-minion"])


def do_systemctl():
    '''
    start salt-minion via systemctl
    '''
    return do_popen([SYSTEMCTL, "start", "salt-minion.service"])


def start_salt_process():
    '''
    start a minion with upstart or systemctl
    accordingly
    '''
    if os.path.exists(UPSTART):
        do_upstart()
    elif os.path.exists(SYSTEMCTL):
        do_systemctl()
    else:
        print "failed to find startup command"


def shoot_salt_processes():
    '''
    shoot all salt-minion processes with prejudice
    '''
    do_popen(["pkill", "salt-minion"])
    time.sleep(1)
    salt_processes = get_salt_processes()
    if salt_processes is not None and len(salt_processes):
        print "hrm, still some processes around", salt_processes
        return False
    return True


def usage(message=None):
    '''
    display a helpful usage message with
    an optional introductory message first
    '''
    if message is not None:
        sys.stderr.write(message)
        sys.stderr.write("\n")
    usage_message = """
Usage: salt-fixups.py --actions actionlist
    --dryrun --help

Options:

  --actions (-a):  comma-separated list of actions which may
                   be one or more of the following:

                   autherror -- check and restart if minion is stuck with authentication error
                   version   -- check and fix if salt is wrong version
                   count     -- check and fix if there is not exactly one minion running
                   regenkey  -- if keysize is > 2048, set keysize to 2048 in minion config and regen
                                you will need to go to the master and delete the key from
                                pki/master/minions_denied and from pki/minions afterwards

  --dryrun  (-d):  display the commands that would be run to produce the output but
                   don't actually run them
  --verbose (-v):  display informational messages as this script runs
  --help    (-h):  display this message
"""  # noqa
    sys.stderr.write(usage_message)
    sys.exit(1)


def do_version(dryrun, verbose):
    '''
    if salt version isn't what we want,
    apt-get install it
    '''
    salt_version = get_salt_version()
    if not check_salt_version(salt_version):
        if dryrun:
            print "would fix salt version (bad)"
        else:
            if verbose:
                print "fixing salt version (bad)"
            fix_salt_version(verbose)
    elif dryrun or verbose:
        print "salt version is good"


def do_count(dryrun, verbose):
    '''
    if there is not exactly one salt minion running
    and handling requests (excluding any recently forked
    process that may be doing a request right now),
    start or shoot/restart minion(s) as needed
    '''
    salt_processes = get_salt_processes()
    if not salt_processes:
        if dryrun:
            print "would start a minion (none running)"
        else:
            if verbose:
                print "starting minion (none running)"
            start_salt_process()
    elif not check_salt_processes(salt_processes):
        # more than one such process, and not just
        # now spawned to do a job
        if dryrun:
            print "would shoot minions and start one (too many)"
        else:
            if verbose:
                print "shooting minions (too many)"
            shoot_salt_processes()
            if verbose:
                print "starting minion"
            start_salt_process()
    elif dryrun or verbose:
        print "salt minion count is good"


def do_autherror(dryrun, verbose):
    '''
    check if the salt log ends with a notification of an authentication
    error, this is usually a sign that the minion is out to lunch
    if so, restart the minion, this usually clears it up
    '''
    if check_salt_auth_error():
        if dryrun:
            print "would restart minion (auth error)"
        else:
            if verbose:
                print "restarting salt (auth error)"
            restart_salt()
    elif dryrun or verbose:
        print "no minion autherror"


def check_puppet_master():
    '''
    grab the puppet master named in the puppet
    config file and verify it's what we expect
    '''
    contents = open(PUPPETCONF, "r").read()
    lines = contents.splitlines()
    for entry in lines:
        if entry.startswith("server"):
            if PUPPET_MASTER in entry:
                return True
    return False


def fix_keysize_config(verbose):
    '''
    if salt minion keysize configuration is not set
    (defaut is 40967, tooooo big), add the correct
    setting
    '''
    # check current contents of config file
    contents = open(SALTCONF, "r").read()
    lines = contents.splitlines()
    index = 0
    has_keysize = False
    for entry in lines:
        index += 1
        if entry.startswith("keysize:"):
            if SALT_KEYSIZE in entry:
                return False  # no regen needed
            else:
                if verbose:
                    print "updating from", entry
                has_keysize = True
                break

    # remove old entry
    if has_keysize:
        if len(lines) > index + 1:
            rest = lines[index + 1:]
        else:
            rest = []
        lines = lines[0:index] + rest
    elif verbose:
        print "no old keysize, adding one"

    # add new entry
    lines.append("keysize: " + SALT_KEYSIZE)

    # write out the contents and move into place
    new_contents = "\n".join(lines) + "\n"
    new_config = SALTCONF + "tmp"
    new_config_fp = open(new_config, "w+")
    new_config_fp.write(new_contents)
    new_config_fp.close()
    os.rename(new_config, SALTCONF)
    return True


def remove_minion_key():
    '''
    remove salt minion pub and private key
    '''
    if os.path.exists(SALT_MINION_PUB):
        os.unlink(SALT_MINION_PUB)
    if os.path.exists(SALT_MINION_KEY):
        os.unlink(SALT_MINION_KEY)


def check_keysize():
    '''
    get the keysize of the current salt minion key
    and make sure it's what we expect
    '''
    if not os.path.exists(SALT_MINION_PUB):
        return False

    command = ["/usr/bin/openssl", "rsa", "-pubin",
               "-in", SALT_MINION_PUB, "-inform", "pem", "-text"]
    lines = get_popen_output(command)
    for entry in lines:
        if entry.startswith("Public-Key:"):
            if SALT_KEYSIZE in entry:
                return True
    return False


def do_regenkey(dryrun, verbose):
    '''
    if the salt key length is greater than 2048 bits,
    fix up the salt minion config and regenerate
    with the right size
    '''
    if not check_puppet_master():
        if dryrun or verbose:
            print "wrong puppet master, no regen"
        return

    if check_keysize():
        if dryrun or verbose:
            print "key size ok"
        return

    if dryrun:
        print "would regen key (wrong key size)"
        return

    if verbose:
        print "shooting minions"
    shoot_salt_processes()

    if fix_keysize_config(verbose):
        if verbose:
            print "keysize fixed up in config"
    elif verbose:
        print "keysize in config is ok"

    if verbose:
        print "removing minion key"
    remove_minion_key()

    if verbose:
        print "starting minion, don't forget to delete key on master"
    start_salt_process()


def do_actions(actions, dryrun, verbose):
    '''
    handle user-requested actions
    '''
    if "autherror" in actions:
        do_autherror(dryrun, verbose)

    if "version" in actions:
        do_version(dryrun, verbose)

    if "count" in actions:
        do_count(dryrun, verbose)

    if "regenkey" in actions:
        do_regenkey(dryrun, verbose)


def main():
    '''
    make sure salt version is correct
    make sure we are running exactly one minion
    if the dreaded authentication error is
       hanging the minion, restart it
    '''
    actions = None
    dryrun = False
    verbose = False

    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "a:dvh",
            ["actions=", "help", "verbose", "dryrun"])
    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))
    for (opt, val) in options:
        if opt in ["-a", "--actions"]:
            actions = val.split(",")
        elif opt in ["-d", "--dryrun"]:
            dryrun = True
        elif opt in ["-v", "--verbose"]:
            verbose = True
        elif opt in ["-h", "--help"]:
            usage('Help for this script\n')
        else:
            usage("Unknown option specified: <%s>" % opt)
    if len(remainder) > 0:
        usage("Unknown option(s) specified: <%s>" % remainder[0])

    if actions is None:
        usage("At least one action must be specified.")

    if check_master():
        if dryrun:
            print "master checks out, proceeding"
        do_actions(actions, dryrun, verbose)
    elif dryrun:
        print "wrong master encountered, stopping"


if __name__ == "__main__":
    main()
