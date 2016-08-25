import sys


def get_hostinfo(lines):
    '''
    split up the pile of lines of text
    into separate lists of lines, one
    for each host
    '''
    hosts = []
    hostinfo = []
    for line in lines:
        if line.startswith("doing "):
            if hostinfo:
                hosts.append(hostinfo)
            hostinfo = [line]
        else:
            hostinfo.append(line)
    return hosts


def get_date(line):
    '''
    from a line of ls -lt, get the date
    '''
    fields = line.split()
    return " ".join([fields[index] for index in range(5, 8)])


def get_salt_version(line):
    '''
    from a dpkg-l line, get the version info
    '''
    fields = line.split()
    for field in fields:
        if field.startswith("20"):
            return field
    return ""


def get_process(line):
    '''
    dig out the date and command from a ps line
    '''
    # root       361  0.0  0.9  69932 19768 ?        Ss   Aug19   0:00
    # /usr/bin/python /usr/bin/salt-minion'
    line.strip()
    if not line:
        return ""
    fields = line.split()
    if len(fields) < 8:
        return ""
    return " ".join(fields[8:])


def get_host_data(hostinfo):
    '''
    from list of lines for a host, dig
    out the info we want and return it
    in a tuple
    '''
    hostdata = {}
    hostdata['processes'] = []
    hostdata['masters'] = []
    for item in ['hostname', 'issue', 'salt_id', 'keysize', 'puppet_rundate',
                 'minion_logdate', 'salt_version', 'minion_errors']:
        hostdata[item] = ""

    want_master = False
    for line in hostinfo:
        if line.startswith("Debian") or line.startswith("Ubuntu"):
            hostdata['issue'] = line
        elif line.startswith("doing"):
            hostdata['hostname'] = line[6:]
        elif line.startswith("id:"):
            hostdata['salt_id'] = line[4:]
        elif line.startswith("master:"):
            if not line[8:]:
                '''
                master:
                - labs-puppetmaster-eqiad.wikimedia.org
                - labs-puppetmaster-codfw.wikimedia.org
                and this terminates as soon as we see a line with non
                whitespace first char.
                '''
                want_master = True
            else:
                hostdata['masters'].append(line[8:])
        elif line.startswith("keysize:"):
            hostdata['keysize'] = line[9:]
        elif "/var/log/puppet.log" in line:
            hostdata['puppet_rundate'] = get_date(line)
        elif "/var/log/salt/minion" in line:
            hostdata['minion_logdate'] = get_date(line)
        elif "/usr/bin/salt-minion" in line:
            process = get_process(line)
            if process:
                hostdata['processes'].append(process)
        elif "salt-common" in line:
            hostdata['salt_version'] = get_salt_version(line)
        elif line.startswith("AuthenticationError"):
            hostdata['minion_errors'] = line
        elif want_master:
            stripped = line.lstrip()
            if stripped and stripped[0] == '-':
                master_name = stripped[1:].lstrip()
                hostdata['masters'].append(master_name)
            else:
                want_master = False
    return hostdata


def show(hostdata):
    '''
    given some extracted data about a host, display it
    '''
    # yeah. it's cheap. so what.
    keys = sorted(hostdata.keys())
    for key in keys:
        if hostdata[key]:
            print key, hostdata[key]
    print


def show_ec2id_salt_ids(summaries):
    '''
    given nicely formatted host info summaries,
    show all the hostnames where the salt id is i-000 something
    plus show the ids too
    '''
    print "hosts with ec2id salt ids"
    for summary in summaries:
        if summary['salt_id'].startswith('i-000'):
            print("{} {} last puppet run: {}".format(
                summary['hostname'], summary['salt_id'],
                summary['puppet_rundate']))
    print


def show_oldstyle_salt_ids(summaries):
    '''
    given nicely formatted host info summaries,
    show all the hostnames where the salt id is the old-style
    hostname (three parts without the project name)
    plus show the ids too
    '''
    print "hosts with old style salt ids"
    for summary in summaries:
        if summary['salt_id']:
            if len(summary['salt_id'].split(".")) != 4:
                print summary['hostname'], summary['salt_id']
    print


def show_salt_errors(summaries):
    '''
    given nicely formatted host info summaries,
    show all the hostnames where we had the authentication error
    for salt
    '''
    print "hosts with the authentication minion error"
    for summary in summaries:
        if summary['minion_errors']:
            print summary['hostname']
    print


def show_salt_bad_versions(summaries):
    '''
    given nicely formatted host info summaries,
    show all the hostnames where the salt version is not 2014.7.5
    plus show the versions
    '''
    print "hosts with bad salt versions"
    for summary in summaries:
        if summary['salt_version']:
            if not summary['salt_version'].startswith('2014.7.5'):
                print summary['hostname'], summary['salt_version'], summary['issue']
    print


def show_salt_other_masters(summaries):
    '''
    given nicely formatted host info summaries,
    show all the hostnames where the salt master is not the
    standard labs master, plus show the master names
    '''
    print "hosts with other salt masters"
    for summary in summaries:
        if summary['masters']:
            for master in summary['masters']:
                if (not master == 'labs-puppetmaster-eqiad.wikimedia.org' and
                    not master == 'labs-puppetmaster-codfw.wikimedia.org' and
                        not master == 'labcontrol2001.wikimedia.org'):
                    print summary['hostname'], summary['masters']
                    break
    print


def show_salt_correct_masters(summaries):
    '''
    given nicely formatted host info summaries,
    show all the hostnames where the salt master is only
    standard labs masters
    '''
    print "hosts with correct salt master(s)"
    for summary in summaries:
        if summary['masters']:
            problem = False
            for master in summary['masters']:
                if not (master == 'labs-puppetmaster-eqiad.wikimedia.org' or
                        master == 'labs-puppetmaster-codfw.wikimedia.org' or
                        master == 'labcontrol2001.wikimedia.org'):
                    problem = True
                    break
            if not problem:
                print summary['hostname'], summary['masters']
    print


def show_salt_no_processes(summaries):
    '''
    show all hosts where no salt minion is running
    '''
    print "hosts with no mininon running"
    for summary in summaries:
        if not summary['processes']:
            print summary['hostname']
    print


def show_salt_too_many_processes(summaries):
    '''
    show all hosts where more than one salt minion is running
    plus the process information
    '''
    print "hosts with more than one minion running"
    for summary in summaries:
        if len(summary['processes']) > 1:
            print summary['hostname'], summary['processes']
    print


def show_salt_no_keysize(summaries):
    '''
    show all hosts where keysize has not been set
    '''
    print "hosts with no keysize specified"
    for summary in summaries:
        if summary['masters'] and not summary['keysize']:
            print("{} last puppet run: {}".format(
                summary['hostname'], summary['puppet_rundate']))
    print


def main():
    summaries = []
    inputfp = sys.stdin
    content = inputfp.read()
    lines = content.splitlines()
    hostinfo = get_hostinfo(lines)
    for host in hostinfo:
        results = get_host_data(host)
        show(results)
        summaries.append(results)
    show_ec2id_salt_ids(summaries)
    show_salt_errors(summaries)
    show_salt_bad_versions(summaries)
    show_salt_other_masters(summaries)
#    show_salt_correct_masters(summaries)
    show_salt_no_processes(summaries)
    show_salt_too_many_processes(summaries)
    show_salt_no_keysize(summaries)

if __name__ == "__main__":
    main()
