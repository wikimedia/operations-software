import sys
import getopt
import HHelp
import HOptions
import HCli
from HSources import Source, DecomPuppet, DecomRackTables, Dsh, Dhcp
from HSources import Dns, Puppet, PuppetCerts, LogPuppet, PuppetStoredConfigs
import HFilter
import HReport
import HConfig

# document classes, main functions
# maybe rename some functions with _ so polite people don't use 'em

if __name__ == '__main__':
    """Generate lists of hosts that belong to different sources, or
    show the attributes of the hosts in various sources; lists that
    can be generated are e.g. all hosts in dns, dhcp but having no
    pupet certs; or, show all the mw* hosts and whether they are
    decommed in racktables, are known to salt, are in dns."""

    configfile = "checkhosts.conf"
    configInfo = {}     # arguments and values collected from configuration
                        #  files as well as from command line

    filterExpr = None   # show a list of hosts that are present in the named
                        # sources or with attributes that match these
    reportArg = None    # instead, show a report of host attributes, displaying
                        # only attributes that match these
    hostExprs = None    # limit list or report to these hostnames

    timeout = None      # timeout in seconds for remote commands

    verbose = 0
    cli = False         # enter command line mode (prompt for and process
                        # commands)
    version = "0.0.1"

    # these options set parameters for a specific Source subclass
    optsToClasses = {"-d": Dhcp, "--dhcp": Dhcp,
                     "-D": Dsh, "--dsh": Dsh,
                     "-r": DecomRackTables,
                     "--decomracktables": DecomRackTables,
                     "-p": DecomPuppet,
                     "--decompuppet": DecomPuppet,
                     "-P": Puppet,
                     "--puppet": Puppet,
                     "-l": LogPuppet,
                     "--logpuppet": LogPuppet,
                     "-Q": PuppetCerts,
                     "--puppetcerts": PuppetCerts,
                     "-s": PuppetStoredConfigs,
                     "--storedconfigs": PuppetStoredConfigs,
                     "-n": Dns, "--dns": Dns}

    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "f:CR:d:D:r:p:P:n:l:Q:s:H:c:t:vVhe",
            ["filter=","report=","cli","dhcp=", "dsh=",
             "decomracktables=", "decompuppet=", "puppet=",
             "dns=", "logpuppet=", "puppetcerts=",
             "storedconfigs=", "hosts=", "config=", "timeout=",
             "verbose","version","help", "extendedhelp",
             "debug"])
    except getopt.GetoptError as err:
        HHelp.usage("Unknown option specified: " + str(err))

    for (opt, val) in options:
        if opt in ["-f", "--filter"]:
            filterExpr = val
        elif opt in ["-C", "--cli"]:
            cli = True
        elif opt in ["-R", "--report"]:
            reportArg = val
        elif opt in optsToClasses:
            configInfo[optsToClasses[opt].getSourceName()] = (
                optsToClasses[opt].getArgs(val))
        elif opt in ["-H", "--hosts"]:
            hostExprs = val
        elif opt in ["-c", "--config"]:
            configfile = val
        elif opt in ["-t", "--timeout"]:
            if not val.isdigit():
                HHelp.usage("Timeout option requires a positive integer")
            timeout = int(val)
        elif opt in ["-v", "--verbose"]:
            verbose = 1
        elif opt in ["--debug"]:
            verbose = 2
        elif opt in ["-V", "--version"]:
            print "check-hosts.py %s" % version
            sys.exit(0)
        elif opt in ["-h","--help"]:
            HHelp.usage("Help message")
        elif opt in ["-e", "--extendedhelp"]:
            HHelp.extendedUsage(Source.getKnownSources())
        else:
            HHelp.usage("Unknown option specified: %s" % opt)

    if len(remainder) > 0:
        HHelp.usage("Unknown option specified: <%s>" % remainder[0])

    mainOptsSet = 0
    for opt in [filterExpr, cli, reportArg]:
        if opt:
            mainOptsSet += 1
    if not mainOptsSet:
        HHelp.usage("You must choose one of 'filter', 'report' or 'cli'")
    if mainOptsSet > 1:
        HHelp.usage("You may choose only one of 'filter', 'report' or 'cli'")

    # handle configuration file processing
    hc = HConfig.CheckHostsConfig(configfile)
    hc.parseConfFile()
    configInfoFromFiles = hc.conf.options

    # merge in any config options we got from the command line
    for t in list(set(configInfoFromFiles.keys() + configInfo.keys())):
        if t in configInfo:
            configInfo[t] = HOptions.mergeDefaults(configInfoFromFiles[t],
                                                   configInfo[t])
        else:
            configInfo[t] = HOptions.mergeDefaults(configInfoFromFiles[t],
                                                   None)
    if timeout is None:
        if hc.conf.has_option('globals', 'timeout'):
            timeout = hc.conf.get('globals', 'timeout')

    if verbose:
        print "running with configuration:"
        print configInfo

    # list of hosts in sources
    if filterExpr:
        hf = HFilter.HostFilter(configInfo, hostExprs, timeout, verbose)
        hf.processFilterArg(filterExpr)
        if hf.filters:
            hf.filterHosts()
            hf.displayHosts()

    # chart of hosts and attributes
    elif reportArg:
        hr = HReport.HostReport(configInfo, hostExprs, timeout, verbose)
        hr.processReportArg(reportArg)
        if hr.reportSourceNames:
            hr.reportHosts()
            hr.displayHosts()

    # cli
    else:
        hf = HFilter.HostFilter(configInfo, hostExprs, timeout, verbose)
        hr = HReport.HostReport(configInfo, hostExprs, timeout, verbose)
        c = HCli.Cli(hf, hr, Source.getKnownSources())
        c.runCli()
