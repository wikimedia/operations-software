import HHelp

class Cli(object):
    """
    command line interpreter: prompt for command
    and execute it, until user exits

    this class maintains source lists that are re-used
    when new filter or report commands are given

    if the user wants an updated list of hosts from a source,
    the 'flush' command is available to force the list
    to be regenerated
    """

    def __init__(self, hf, hr, knownSources):
        # argument: a hostFilter object
        self.hf = hf
        self.hr = hr
        self.knownSources = knownSources

    def runCli(self):
        while True:
            print ""
            command = raw_input("Command: ")
            result = self.cliCommand(command)
            if not result:
                # they want to exit the cli
                break

    def showSettings(self):
        # settings will be the same for both reports and filters
        # so just look at one
        if self.hf.verbose:
            print "verbose on"
        else:
            print "verbose off"
        print "timeout:", self.hf.timeout
        if self.hf.hostExprs:
            print "hosts:", self.hf.hostExprs
        else:
            print "hosts is unset"

        if not self.hf.hostOpts:
            return
        for source in self.hf.hostOpts:
            print source + ":"
            for option in self.hf.hostOpts[source]:
                print "    %s:" % option, self.hf.hostOpts[source][option]

    def cliHandleFilter(self, filterCommand):
        filterExpr = filterCommand.split()[1]
        self.hf.processFilterArg(filterExpr)
        if self.hf.filters:
            self.hf.updateSources()
            # update the report sources now too
            self.hr.addSources(self.hf.sources)
            self.hf.filterHosts()
            self.hf.displayHosts()

    def cliHandleReport(self, reportCommand):
        reportArg = reportCommand.split()[1]
        self.hr.processReportArg(reportArg)
        if self.hr.reportSourceNames:
            self.hr.updateSources()
            # update the filter sources now too
            self.hf.addSources(self.hr.sources)
            self.hr.reportHosts()
            self.hr.displayHosts()

    def cliDoSet(self, setCommand):
        sourceName = command.split()[1]
        if sourceName not in self.knownSources:
            print "Unknown source"
            print HHelp.getSourcesHelp(self.knownSources)
        else:
            setting = raw_input("setting: ")
            setting = setting.strip()
            if not ' ' in setting:
                print ("Bad setting format;" +
                       "expecting setting-name whitespace value")
            # fixme this and the below set of splits is inconsistent
            # and dangerous
            # update both the hf and hr sources
            elif (not self.hf.sources[sourceName].update(
                    setting.split(" ", 1))):
                print "Bad setting for source"
            elif (not self.hr.sources[sourceName].update(
                    setting.split(" ", 1))):
                print "Bad setting for source"
            else:
                print ("setting", setting.split()[0], "updated to",
                       setting.split()[1])

    def cliDoUnset(self, command):
        sourceName = command.split()[1]
        if sourceName not in self.knownSources:
            print "Unknown source"
            print HHelp.getSourcesHelp(self.knownSources)
        else:
            setting = raw_input("setting: ")
            setting = setting.strip()
            if ' ' in setting:
                print "Bad setting format; expecting setting-name"
            # update both hr and hf sources
            elif not self.hf.sources[sourceName].update(setting,
                                                        "", emptyOk=True):
                print "Bad setting for source"
            elif not self.hr.sources[sourceName].update(setting,
                                                        "", emptyOk=True):
                print "Bad setting for source"

    def cliCommand(self, command):
        if command == "exit" or command == "bye" or command == "quit":
            return False
        print ""
        if command == "settings":
            self.showSettings()
        elif command.startswith("filter "):
            self.cliHandleFilter(command)
        elif command.startswith("report "):
            self.cliHandleReport(command)
        elif command == "flush":
            self.hf.sources = {}
            self.hr.sources = {}
            print "all host lists flushed"
        elif command.startswith("hosts "):
            # set the hosts option
            hosts = command.split()[1].split(',')
            self.hf.hostExprs = hosts
            self.hr.hostExprs = hosts
            print "hosts expr set to", self.hf.hostExprs
        elif command == "nohosts":
            self.hf.hostExprs = None
            self.hr.hostExprs = None
            print "hosts expr unset"
        elif command == "timeout":
            timeout = command.split()[1]
            self.hf.timeout = int(timeout)
            self.hr.timeout = int(timeout)
            print "timeout set to", timeout
        elif command == "verbose":
            self.hf.verbose = True
            self.hr.verbose = True
            print "verbose set to on"
        elif command == "noverbose":
            self.hf.verbose = False
            self.hr.verbose = False
            print "verbose set to off"
        elif command.startswith("set "):
            self.cliDoSet(command)
        elif command.startswith("unset "):
            self.cliDoUnset(command)
        elif command == "help":
            self.cliHelp(None)
        elif command.startswith("help "):
            helpWanted = command.split()[1]
            self.cliHelp(helpWanted)
        else:
            self.cliHelp()
        return True

    def cliHelp(self, helpWanted=None):
        knownTopics = ("cli, criteria, filter, help," +
                       "report, sources, topics, values")
        basicHelp = ("Enter exit|quit|bye to quit,\n" +
                     "or help cli for how to use the cli")

        if helpWanted is None:
            print basicHelp
            return

        helpWanted = helpWanted.strip()
        if helpWanted == "cli":
            print "Enter one of the following:"
            print ""
            print "exit|quit|bye to quit,"
            print "filter <expr> where expr is a comma-separated list"
            print "   of assertions, to display a list of hosts matching"
            print "   the filter,"
            print "report <expr> where expr is a comma-separated list"
            print "   of reqirements, to display a report of hosts in those"
            print "   sources and values matching the requirement,"
            print "flush to discard all host source lists; they will be"
            print "   reloaded for the next filter or report"
            print "verbose to display various messages during processing,"
            print "noverbose to turn that off,"
            print "settings to show current settings,"
            print "hosts <expr> to change the value of the hosts option"
            print "   (applies to filters and reports),"
            print "nohosts to unset that,"
            print "set <sourcename> to set a setting for a source (you"
            print "   will be prompted for a setting, enter <setting> <value>"
            print "   for one of host, path, db, user, password,"
            print "   depending on what settings are valid for that source),"
            print "unset <sourcename> to set a setting for a source to"
            print "   '' (you will be prompted for a settingname, enter one"
            print "   of host, path, db, user, password, depending on what"
            print "   settings are valid for that source),"
            print "timeout <int> to set the timeout for remote commands to this"
            print "   many seconds (applies to filters and reports),"
            print "help <topicname> for detailed help on a topic."
            print ""
            print "Known help topics:"
            print knownTopics
        elif helpWanted == "filter":
            print HHelp.getFilterHelp(self.knownSources)
        elif helpWanted == "report":
            print HHelp.getReportHelp(self.knownSources)
        elif helpWanted == "sources":
            print HHelp.getSourcesHelp(self.knownSources)
        elif helpWanted == "criteria":
            print HHelp.getCriteriaHelp()
        elif helpWanted == "values":
            print HHelp.getCriteriaValuesHelp()
        elif helpWanted == "topics":
            print "Enter help <topicname> for detailed help on a topic."
            print "Known topics:"
            print knownTopics
        else:
            print "Unknown help topic <%s>.  Known topics:" % helpWanted
            print knownTopics
