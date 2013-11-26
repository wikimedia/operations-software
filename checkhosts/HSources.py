import os
import sys
import re
import getpass
import subprocess
import json
import signal
import salt.client
import salt.key
import salt.config
import HOptions
import HPassPlugins

class Source(object):
    """Base class for host sources

    To implement a subclass, add your subclass to this file,
     override the following class variable:
       options
    override the following attributes:
       displayHostsHeader
    provide the following methods:
       getSourceName, getHosts
    call the parent constructor as the first thing in your constructor
    call getHosts() as the last thing in your constructor
    add any command line config options to the main entry point for your script
    add the appropriate info to the help classes

    NOTE: subclassing a subclass will not work properly, due to
    getKnownSources()
    """

    options = {}

    # for now we only accept multiple hostnames (e.g. we might look for
    # certs on multiple puppet cas, or for puppet facts on multiple
    # puppetmasters
    optionAllowsMultiple = ['host', 'pluginparams']

    def __init__(self, params, timeout, verbose=False):
        """
        Args:

        params -- config info, a dict of opt name and value
        verbose -- whether or not to display extra processing info to the screen and how much
                   this is a numeric value
        """
        self.timeout = timeout
        self.verbose = verbose
        self.params = params
        # this header will be shown in displayHosts()
        self.displayHostsHeader = "Host list"
        # hosts that are in the source
        self.hosts = {}
        # for salt commands, for all sources where the files or info
        # don't reside on the local host, and for the salt source
        self.client = None
        # whether the host with the source info is the local host
        self.hostIsLocal = None
        # a function to retrieve a password for database access,
        # from a file or other means
        self.passwordCallback = None

    #
    # override these methods in your subclass always
    #
    @classmethod
    def getSourceName(cls):
        """
        args:    none
        returns: string
          a name of this source, must be
          unique across all Hosts subclasses"""

        return "hosts"

    def getHosts(self):
        """populate self.hosts with hosts that are
        in this source and their attribute values

        args:    none
        returns: nothing"""

        return

    #
    # these methods should be used as is, no override needed
    #
    @classmethod
    def parseOptionMultiples(cls, o, value):
        if o in Source.optionAllowsMultiple:
            if value and len(cls.options[o]) > 3 and cls.options[o][3]:
                return value.split(cls.options[o][3])
            else:
                return [value]
        else:
            return value

    @classmethod
    def getConfig(cls, conf, section="sources"):
        """get option values out of a given section of a
        configuration file, and return them

        args:    ConfigParser object
                 section name in the conf file

        returns: dict of option, value, possibly including:
                 'host'     -- source host(s)
                 'path'     -- path to file or files on source host
                 'db'       -- name of db for source
                 'user'     -- user name for db connection
                 'password' -- password for db connection
                 or other options particular to a given source
               """

        retrieved = {}
        for o in cls.options:
            if conf.has_option(section, cls.options[o][1]):
                retrieved[o] = cls.parseOptionMultiples(
                    o, conf.get(section, cls.options[o][1]))
            else:
                retrieved[o] = None

        return retrieved

    @classmethod
    def getConfigDefaults(cls):
        """return default values for configuration opts for
        this source

        args:    none
        returns: dict of option names as they appear in the
                 config file, and their default values"""

        defaults = {}
        for o in cls.options:
            defaults[cls.options[o][1]] = cls.options[o][2]
        return defaults

    @classmethod
    def getArgs(cls, arg):
        """turn a comma-separated set of values into opts
        and values that can be merged with other configuration
        opts, and return it

        args:    a string possibly containing commas
        returns: dict of option, value where the options may include:
                 'host'     -- source host(s)
                 'path'     -- path to file or files on source host
                 'db'       -- name of db for source
                 'user'     -- user name for db connection
                 'password' -- password for db connection
                 or other options particular to a given source
        """

        result = HOptions.getOptions(
            arg, sorted(cls.options,
                        key=lambda optName: cls.options[optName][0]))
        for opt in result:
            result[opt] = cls.parseOptionMultiples(opt, result[opt])
        return result

    @staticmethod
    def getKnownSources():
        """
        args:    none
        returns: a list of known sources, based on the source names
                 of all the Hosts subclasses. Note that this doesn't work
                 if any subclass is itself subclassed, so don't do that."""

        return [c.getSourceName() for c in Source.__subclasses__()]

    def displayHosts(self):
        """display the hosts from this source and their attributes

        args:    none
        returns: nothing"""

        print self.displayHostsHeader
        print self.hosts

    def _readFileViaSalt(self, f=None):
        """read the contents of a file on a remote host
        using salt

        args:    the full path to the file
        returns: the contents, or the empty string on failure
        """

        if not self.client:
            self.client = salt.client.LocalClient()
        result = self.client.cmd(self.params['host'], "cmd.run_all",
                                 ["cat " + f], expr_form='list', timeout=self.timeout)
        # choose the first host with contents
        for h in result:
            if (not result[h]['retcode']):
                return result[h]['stdout']
        if self.verbose:
            sys.stderr.write("no good reads of file from any host\n")
        return ""

    def _readFile(self, f=None):
        """read the contents of a file, either on the local filesystem
        or remotely on another host

        args:    full path to the file
        returns: the contents, or the empty string on failure
        """

        if not f:
            f = self.params['path']
        if not self.params['host'] or not f:
            return ""

        if self.hostIsLocal is None:
            self.hostIsLocal = self.isLocalHostname(self.params['host'])

        if self.hostIsLocal:
            fd = open(f, "r")
            if not fd:
                return ""
            result = fd.read()
            return result
        else:
            return self._readFileViaSalt(f)

    def _doCommandLocally(self, command, shell=False):
        """execute a command on the local host

        args:    a list consisting of the command name and its args,
                 if shell is False, or a string of the name and args,
                 if shell is True
        returns: the output from the command
        """

        return subprocess.check_output(command, shell=shell)

    def _doCommandViaSalt(self, command):
        """execute a command on a remote host via salt

        args:    a string of the command name and its args
        returns: the output from the command, or None on error
        """

        if not self.client:
            self.client = salt.client.LocalClient()
        result = self.client.cmd(self.params['host'], "cmd.run_all",
                                 [command], expr_form='list', timeout=self.timeout)
        return result  # don't attempt to parse, let the caller figure it out

    def _listDir(self, recent=False):
        """list a directory, either on the local filesystem
        or remotely via salt

        args: recent -- list only files more recent than 7 days ago
        returns:  list of the basenames of the directory entries
                  which are files, or None on error

        if self.params['host'] is a list of hosts, this will return
        the union of all files in the specified directory on all hosts
        """

        if not self.params['host'] or not self.params['path']:
            return None

        if self.hostIsLocal is None:
            self.hostIsLocal = self.isLocalHostname(self.params['host'])

        command = ["find", self.params['path'],
                   "-maxdepth", "1", "-type", "f"]
        if recent:
            command.extend(["-mtime", "-7"])

        if self.hostIsLocal:
            result = self._doCommandLocally(command)
            if result:
                result = [os.path.basename(l) for l in result.splitlines()]
        else:
            command = " ".join(command)
            saltOutput = self._doCommandViaSalt(command)
            result = []
            for h in saltOutput:
                if not saltOutput[h]['retcode'] and 'stdout' in saltOutput[h]:
                    # good output, merge it in
                    result.extend(
                        [os.path.basename(l)
                         for l in saltOutput[h]['stdout'].splitlines()])
            if result:
                # toss the dups
                result = list(set(result))

        if not result:
            return None
        else:
            return result

    def _findRecentFiles(self):
        """convenience wrapper for listDir"""
        return self._listDir(True)

    def _grepContentFromFiles(self, grepArg, recent=False, egrep=False):
        """if we have a pile of files on a remote host, it's wasteful
        to open and read each one via salt.  Instead, grep for the contents
        we want, using one salt command total.

        args:    grepArg - what to grep for
                 egrep   - whether we are grepping for an expression or not
        returns: a list of lines where each line is prefixed with the filename
                 and a colon

        if there are multiple source hosts, do this same grep on each one
        and return a union of all grepped lines
        """

        if not self.params['host'] or not self.params['path']:
            return None

        if self.hostIsLocal is None:
            self.hostIsLocal = self.isLocalHostname(self.params['host'])

        command = ["find", self.params['path'], "-maxdepth",
                   "1", "-type", "f"]
        if recent:
            command.extend(["-mtime", "-7"])
        command.extend(["|", "xargs", "grep"])
        if egrep:
            command.append("-E")
        command.extend(["-H", "'" + grepArg + "'"])
        command = " ".join(command)

        if self.hostIsLocal:
            result = self._doCommandLocally(command, shell=True)
            if result:
                result = result.splitlines()
        else:
            saltOutput = self._doCommandViaSalt(command)
            # we'll concat all the results together and let the caller deal
            result = []
            for h in saltOutput:
                if not saltOutput[h]['retcode'] and saltOutput[h]['stdout']:
                    result.extend(saltOutput[h]['stdout'].splitlines())
        if not result:
            return None
        else:
            return result

    def doMysqlCommand(self, query):
        for h in self.params['host']:

            mysqlCommand = ["mysql", "-h", h]
            if self.params['user']:
                mysqlCommand.extend(["-u", self.params['user']])
            if self.params['password']:
                mysqlCommand.append("-p" + self.params['password'])
            else:
                mysqlCommand.append("-p")

            mysqlCommand.extend(["-e", query, self.params['db']])
            try:
                result = subprocess.check_output(mysqlCommand)
            except subprocess.CalledProcessError as err:
                continue
            lines = result.splitlines()
            return lines

        # none of our mysql hosts worked out, whine
        sys.stderr.write("Problem retrieving host info" +
                         "from %s with return code %d\n"
                         % (self.getSourceName(), err.returncode))
        sys.stderr.write("First 240 chars of output from failed command: ")
        sys.stderr.write(err.output[0:240])
        sys.stderr.write("\n")
        return None

    def _basename(self, hostname):
        """get first part of a hostname

        args:    the hostname, short or fqdn
        returns: the hostname minus domain name
        """

        return hostname.split(".")[0]

    def update(self, option, value, emptyOk=False):
        """update the source's config options
        with a new option/value pair,
        potentially flushing the list of hosts
        in this source if it has been invalidated
        by the option change

        args: option - the name of the option
              (host, path, db, user, etc)
        returns: None if no update was done, True
                 otherwise
        """

        if not emptyOk:
            if not option or not value:
                return None

        # FIXMEEEEEE
        if option not in self.knownOptions:
            return None
        else:
            self.flushOnChange(option, value)
            self.params[option] = self.parseOptionMultiples(option, value)
            return True

    def flushOnChange(self, option, new):
        """determine whether changing the given option invalidates
        the list of hosts for this source and if so flush it

        args:    option - name of option
                 new    - new value
        returns: nothing
        """

        if option not in self.params or self.params[option] != new:
            self.hosts = {}
            if option == 'host':
                # changing the host value means that the new name needs
                # to be checked to see if it's the local host, before it's used
                # but don't do it now, the user may change it again
                self.hostIsLocal = None

    class Alarm(Exception):
        pass

    def alarm_handler(self, signum, frame):
        raise self.Alarm

    def isLocalHostname(self, hostnames):
        """check if the given hostname is one of the names of the local host

        args:   list of hostnames to check (fqdn)
        returns: True if the list consists of one entry and it
                 resolves to ip addr on local host, False if not
                 and None on error"""

        if len(hostnames) > 1:
            return False

        ipExpr = '\s*inet(6?)\s+([^/]+)'

        result = None
        # horrible hack to avoid hanging for half a minute if
        # hostname doesn't resolve etc
        arg = ("import sys, socket, json\n" +
               "json.dump(socket.getaddrinfo('%s', None),sys.stdout)"
               % hostnames[0])
        cmd = ["python", "-c", arg]
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        signal.signal(signal.SIGALRM, self.alarm_handler)
        signal.alarm(5)
        try:
            stdoutdata, stderrdata = proc.communicate()
            signal.alarm(0)  # reset the alarm
            if proc.returncode:
                sys.stderr.write("%s\n" % stderrdata)
                return None
            elif stdoutdata:
                result = json.loads(stdoutdata)
        except self.Alarm:
            sys.stderr.write("Timed out trying to get hostname" +
                             "information for %s\n"
                             % hostnames[0])
            try:
                # cleanup: shoot the hung process
                proc.kill()
            except:
                pass
            return None

        # choose any of the addresses returned
        addr = result[0][4][0]
        command = ["ip", "addr", "list"]
        result = subprocess.check_output(command)
        if not result:
            return None

        for l in result.splitlines():
            ip = re.match(ipExpr, l)
            if ip and ip.group(2) == addr:
                return True
        return False

class DecomPuppet(Source):
    """hosts that are listed in decommissioned.pp on source
    host (should be host with current puppet repo)"""

    # note that hosts in this file do not have fqdn
    # (well and those that do won't be decommed properly,
    # see the code in the decom cleanup script

    options = {'host': [0, 'decompuppet_host',
                        'puppetserver.localdomain', ';'],
               'path': [1, 'decompuppet_path',
                        '/var/lib/puppet/decommissioning.pp']}

    def __init__(self, params, timeout, verbose):
        super(DecomPuppet, self).__init__(params, timeout, verbose)
        self.displayHostsHeader = "Puppet decommissioned hosts:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "decompuppet"

    def getHosts(self):
        # look for and get the value of $::decommissioned_servers
        self.hosts = {}
        text = self._readFile()
        if not text:
            sys.stderr.write("failed to read file of " +
                             "puppet decommissioned servers\n")
            return
        if self.verbose > 1:
            print "read from file"
            print text
        lines = [l.split("#", 1)[0] for l in text.splitlines()
                 if (l and not l.startswith("#"))]
        text = " ".join(lines)
        decomPattern = "\$decommissioned_servers\s*=\s*\[\s*([^\]]*)\s*\]"
        result = re.search(decomPattern, text)
        if not result:
            sys.stderr.write("failed to find puppet decommissioned" +
                             "servers in file content\n")
            return []
        names = result.group(1)
        if "," in names:
            names = names.split(",")
        else:
            names = [names]
        for n in names:
            n = n.strip("'\" \t")
            if n:
                self.hosts[self._basename(n.strip("'\" \t"))] = [True]

class DecomRackTables(Source):
    """hosts that are listed as in the 'decommissioned'
    row in rackspace on source host (should be host with
    racktables db)
    """

    # note that entries in rackspace are not fqdn.

    options = {'host': [0, 'decomracktables_host',
                        'racktablesdb.localdomain', ';'],
               'db': [1, 'decomracktables_db', 'racktables'],
               'user': [2, 'decomracktables_user', 'racktables'],
               'password': [3, 'decomracktables_password', ''],
               'plugin': [4, 'decomracktables_plugin', 'getpwdfromfile'],
               'pluginparams': [5, 'decomrackables_pluginparams',
                                '/puppet/passwords/manifests/init.pp;' +
                                '$racktablespass',
                                ';']}

    def __init__(self, params, timeout, verbose):
        super(DecomRackTables, self).__init__(params, timeout, verbose)
        if self.params['user'] and not self.params['password']:
            if self.params['plugin']:
                hp = HPassPlugins.HPassPlugins()
                self.params['password'] = hp.plugins[self.params['plugin']](
                    self.params['pluginparams'])
            if not self.params['password']:
                self.params['password'] = getpass.getpass(
                    "Racktables password: ")
        self.displayHostsHeader = "Racktables decommissioned hosts:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "decomracktables"

    def getHosts(self):
        if not self.params['host'] or not self.params['db']:
            return

        query = ("SELECT RackObject.name FROM RackObject,Rack,RackSpace,Row "
                 "WHERE RackObject.id = RackSpace.object_id "
                 "AND RackSpace.rack_id = Rack.id "
                 "AND Row.id = Rack.row_id AND Row.name = \"decommissioned\" ;")

        lines = self.doMysqlCommand(query)
        if not lines:
            return
        for l in lines[1:]:  # skip header
            # skip entries like 'ELD1 CKT19 A' (what is that?)
            if l and not l.startswith("#") and not " " in l:
                self.hosts[self._basename(l)] = [True]

class Salt(Source):
    """hosts which are known to salt, those which respond to test ping
    will be so marked"""

    # hosts in this list are initially retrieved with fqdn

    def __init__(self, params, timeout, verbose):
        super(Salt, self).__init__(params, timeout, verbose)
        self.displayHostsHeader = "Hosts known to salt"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "salt"

    def getHosts(self):
        # first get all the known minions
        opts = salt.config.master_config(None)
        key = salt.key.Key(opts)
        keys = key.list_keys()
        for minionGroup in keys.keys():
            if minionGroup != "minions_rejected":
                for h in keys[minionGroup]:
                    self.hosts[self._basename(h)] = [True]

        # now see which hosts ping
        if not self.client:
            self.client = salt.client.LocalClient()
        result = self.client.cmd("*", "test.ping", timeout=self.timeout)
        if not result:
            sys.stderr.write("failed to retrieve salt status of hosts\n")
            return
        for h in result:
            self.hosts[self._basename(h)] = ["ping"]

class Dsh(Source):
    """hosts in any dsh group file on the source host (should be
    host where dsh files are maintained and current)"""

    # hosts from this source do not have fqdn

    options = {'host': [0, 'dsh_host', 'dshgroups.localdmain', ';'],
               'path': [1, 'dsh_path', '/etc/dsh/group']}

    def __init__(self, params, timeout, verbose):
        super(Dsh, self).__init__(params, timeout, verbose)
        self.displayHostsHeader = "Hosts in dsh groups:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "dsh"

    def getHosts(self):
        if not self.params['host'] or not self.params['path']:
            return

        content = self._grepContentFromFiles("^[^#]", egrep=True)
        if not content:
            sys.stderr.write("failed to get contents of dsh files\n")
            return

        for l in content:
            if ':' not in l:
                # bogus format line
                continue
            fileName, dshInfo = l.split(':', 1)
            fileName = os.path.basename(fileName.strip())
            h = self._basename(dshInfo.strip())
            if h not in self.hosts:
                self.hosts[h] = [fileName]
            # possible if we have replies from more than one host
            elif fileName not in self.hosts[h]:
                self.hosts[h].append(fileName)

class Dhcp(Source):
    """hosts with entries in dhcp on source host (should be
    dhcp server)"""

    # hosts from this source are initially retrieved with fqdn

    options = {'host': [0, 'dhcp_host', 'dhcp.localdomain', ';'],
               'path': [1, 'dhcp_path', '/etc/dhcp3']}

    def __init__(self, params, timeout, verbose):
        super(Dhcp, self).__init__(params, timeout, verbose)
        self.displayHostsHeader = "Hosts in dhcp files:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "dhcp"

    def getHosts(self):
        if not self.params['host'] or not self.params['path']:
            return

        content = self._grepContentFromFiles("fixed-address")
        if not content:
            sys.stderr.write("failed to get contents of dhcp files\n")
            return

        for l in content:
            if ':' not in l:
                # bogus format line
                continue
            fileName, dhcpInfo = l.split(':', 1)
            fileName = os.path.basename(fileName.strip())
            # expect lines of format
            #     fixed-address cam1-a-b-eqiad.eqiad.wmnet;
            # where there may be tabs or spaces
            h = dhcpInfo.strip().split(" ", 1)[1].rstrip(";")
            # skip ip addresses
            if not h[0].isdigit():
                h = self._basename(h)
                if h not in self.hosts:
                    self.hosts[h] = [fileName]
                # possible if we get files from multiple hosts
                elif fileName not in self.hosts[h]:
                    self.hosts[h].append(fileName)

class Dns(Source):
    """hosts with IN A entries in dns on source host (should
    be dns master, or if worried about performance impact then
    a secondary); ip addresses are collected as attributes

    Note that AAAA records don't presently get returned"""

    # note that hosts retrieved from this source do not have fqdn
    # a host in there with multiple origins will get multiple ip
    # addresses in the attributes

    options = {'host': [0, 'dns_host', 'dnsserver.localdomain', ';'],
               'path': [1, 'dns_path', '/etc/gdnsd/zones']}

    def __init__(self, params, timeout, verbose):
        super(Dns, self).__init__(params, timeout, verbose)
        self.displayHostsHeader = "Hosts in dns:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "dns"

    def getHosts(self):
        if not self.params['host'] or not self.params['path']:
            return

        content = self._grepContentFromFiles("\s+IN\s+A+\s+", egrep=True)
        if not content:
            sys.stderr.write("failed to get contents of dns files\n")
            return

        for l in content:
            if ':' not in l:
                # bogus format line
                continue
            junk, dnsInfo = l.split(':', 1)
            # expect lines of format
            #     hostname   1H(or something)    IN   A   ipaddr   ; comments...
            # where there may be tabs or spaces
            dnsInfo = dnsInfo.strip().split(";")[0]
            pieces = dnsInfo.split()
            if len(pieces) > 3 and pieces[2] == "IN" and pieces[3] == "A":
                h = pieces[0]
                # stuff the addr in there, maybe someone will want it
                if self._basename(h) not in self.hosts:
                    self.hosts[self._basename(h)] = [pieces[4].strip()]
                else:
                    addr = pieces[4].strip()
                    # could already be there from same file, or from other file
                    # if we get dns info from multiple hosts
                    if addr not in self.hosts[self._basename(h)]:
                        self.hosts[self._basename(h)].append(pieces[4].strip())

class Puppet(Source):
    """hosts with current (less than 7 days old) facts files on the
    source host (should be a puppet master); all facts are read and
    stored as attributes except keys/ssh-related facts"""

    # note that hosts from this source are initially retrieved with fqdn

    options = {'host': [0, 'puppet_host', 'puppetserver.localdomain', ';'],
               'path': [1, 'puppet_path', '/var/lib/puppet/yaml/facts']}

    def __init__(self, params, timeout, verbose):
        super(Puppet, self).__init__(params, timeout, verbose)
        self.displayHostsHeader = "Hosts with recent puppet runs:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        # id001 and so on get stashed here
        self.factIdRefs = {}
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "puppet"

    def getHosts(self):
        if not self.params['host'] or not self.params['path']:
            return

        content = self._grepContentFromFiles(":", recent=True)
        if not content:
            sys.stderr.write("failed to get contents of puppet facts files\n")
            return

        self.factIdRefs = {}
        for l in content:
            if ':' not in l:
                sys.stderr.write("unknown output format from" +
                                 "puppet fact file: %s\n" % l)
                continue
            fileName, fact = l.split(':', 1)
            fileName = fileName.strip()
            fileName = self._basename(os.path.basename(fileName))
            if fileName not in self.factIdRefs:
                self.factIdRefs[fileName] = {}
            if fileName not in self.hosts:
                self.hosts[fileName] = []
            fact = fact.strip()
            if (not fact or fact.startswith('#') or
                    '!ruby' in fact or not ':' in fact):
                continue
            parsed = self.parseFact(fact)
            # could already be there if we got facts file from multiple hosts
            # NOTE that if we have multiple fact files for a puppet client
            # with varying fact values, they will all show up in this list!
            if parsed and parsed not in self.hosts[fileName]:
                self.hosts[fileName].append(parsed)
        return

    def parseFact(self, fact):
        name, value = fact.split(":", 1)
        name = name.strip()
        if 'key' in name or 'pass' in name:
            # might be private, don't even bother
            return None

        toReturn = None

        value = value.strip()
        if value.startswith('&id'):
            if not ' ' in value:
                sys.stderr.write("Unknown fact format %s\n" % fact)
                toReturn = None
            else:
                ref, value = value.split(' ', 1)
                value = value.strip('"')
                self.factIdRefs[ref.strip()[1:]] = value
                toReturn = name + ":" + value
        elif value.startswith('*id'):
            if ' ' in value:
                sys.stderr.write("Unknown fact format %s\n" % fact)
                toReturn = None
            else:
                ref = value.strip()[1:]
                if not ref in self.factIdRefs:
                    sys.stderr.write("Unknown fact format %s\n" % fact)
                    toReturn = None
                else:
                    toReturn = name + ":" + self.factIdRefs[ref]
        else:
            toReturn = name + ":" + value.strip('"')

        return toReturn

class PuppetCerts(Source):
    """hosts with existing puppet certs on source host (should
    be puppet ca host)"""

    # hosts from this source are initially retrieved with fqdn

    options = {'host': [0, 'puppetcerts_host',
                        'puppetserver.localdomain', ';'],
               'path': [1, 'puppetcerts_path',
                        '/var/lib/puppet/server/ssl/ca/signed']}

    def __init__(self, params, timeout, verbose):
        super(PuppetCerts, self).__init__(params, timeout, verbose)
        self.displayHostsHeader = "Hosts with puppet certs:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "puppetcerts"

    def getHosts(self):
        if not self.params['host'] or not self.params['path']:
            return None

        files = self._listDir()
        if not files:
            sys.stderr.write("failed to get list of puppet cert files\n")
            return
        if self.verbose:
            print "puppet cert files:", files
        for f in files:
            shortName = self._basename(f)
            if shortName not in self.hosts:
                self.hosts[shortName] = []
            self.hosts[shortName].append(f)

class LogPuppet(Source):
    """all hosts known to salt (sorry) with current puppet runs,
    whether complete, with errors, etc; the status of the run
    will be saved as a host attribute"""

    # hosts from this source are initially retrieved with fqdn

    options = {'path': [0, 'logpuppet_path', '/var/log/puppet.log']}

    def __init__(self, params, timeout, verbose):
        super(LogPuppet, self).__init__(params, timeout, verbose)
        self.displayHostsHeader = "Hosts with various puppet log entries:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "logpuppet"

    def getHosts(self):
        if not self.params['path']:
            return

        logs = self.getPuppetLogsViaSalt()
        if not logs:
            sys.stderr.write("failed to get puppet log entries for hosts\n")
            return
        for h in logs:
            result = self.parseLog(logs[h])
            if result is None:
                # no log entry, probably failure to retrieve it, skip this host
                continue
            else:
                self.hosts[self._basename(h)] = result

    def parseLog(self, logInfo):
        if not 'stdout' in logInfo:
            return None
        lines = logInfo['stdout'].splitlines()

        if not lines:
            return None

        if 'administratively disabled' in lines[-1]:
            return ['disabled']

        endFound = 0
        startFound = 0
        toReturn = None
        for l in reversed(lines):
            if 'err: Could not retrieve catalog' in l:
                toReturn = ['nocatalog']
            elif 'err: ' in l:
                toReturn = ['err']
            elif 'notice: Finished catalog run' in l:
                endFound = 1
            elif 'info: Retrieving plugin' in l:
                if endFound:
                    toReturn = ['ok']
                elif startFound:
                    toReturn = ['unknown']
                else:
                    startFound = 1
            if toReturn:
                return toReturn
        return 'unknown'

    def getPuppetLogsViaSalt(self):
        # unfortunately some log files have color coding chars at the start
        # of the line so just look for the string somewhere in the line
        egrepExpr = ("^.{0,10}(err:|notice:*administratively disabled" +
                     "|notice: Finished catalog run" +
                     "|err: Could not retrieve catalog" +
                     "|info: Retrieving plugin)")
        if not self.client:
            self.client = salt.client.LocalClient()
        return self.client.cmd('*', "cmd.run_all",
                               ["egrep " + "'" + egrepExpr + "' " +
                                self.params['path'] + '| tail -20'],
                               timeout=self.timeout)

class PuppetStoredConfigs(Source):
    """hosts with entries in hosts table of the puppet db
    where exported resources are kept, source host should be
    the host with the puppet db"""

    # note that hosts from this source are initially retrieved with fqdn

    options = {'host': [0, 'storedconfigs_host', 'puppetdb.localdmain', ';'],
               'db': [1, 'storedconfigs_db', 'puppet'],
               'user': [2, 'storedconfigs_user', 'puppet'],
               'password': [3, 'storedconfigs_password', ''],
               'plugin': [4, 'storedconfigs_plugin', 'getpwdfromfile'],
               'pluginparams': [5, 'storedconfigs_pluginparams',
                                '/etc/puppet/puppet.conf;' +
                                'puppetpassword',
                                ';']}

    def __init__(self, params, timeout, verbose):
        super(PuppetStoredConfigs, self).__init__(params, timeout, verbose)
        if self.params['user'] and not self.params['password']:
            if self.params['plugin']:
                hp = HPassPlugins.HPassPlugins()
                self.params['password'] = hp.plugins[self.params['plugin']](
                    self.params['pluginparams'])
            if not self.params['password']:
                self.params['password'] = getpass.getpass(
                    "Puppet StoredConfigs password: ")
        self.displayHostsHeader = "Hosts in Puppet StoredConfigs:"
        if self.verbose:
            print "retrieving host info from source", self.getSourceName()
        self.getHosts()

    @classmethod
    def getSourceName(cls):
        return "storedconfigs"

    def getHosts(self):
        if not self.params['host'] or not self.params['db']:
            return

        query = "SELECT name FROM hosts;"
        lines = self.doMysqlCommand(query)
        if not lines:
            return
        for l in lines[1:]:  # skip header
            self.hosts[self._basename(l)] = [True]
