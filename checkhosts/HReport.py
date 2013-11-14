import sys
import HHelp
from HSources import Source

class HostReport(object):
    """
    display a table showing hosts with the attributes they have from some
    list of source names; the host must be in at least one of the sources to
    appear in the table, and if requirements are placed on the attributes
    then a host's attribute will only be displayed if it meets the requirements

    hosts are displayed with short name instead of fqdn because some sources
    do not have the fqdn
    """

    def __init__(self, hostOpts, hostExprs, verbose):
        self.sourcesClasses = {}
        for c in Source.__subclasses__():
            self.sourcesClasses[c.getSourceName()] = c

        self.sources = {}
        self.hostOpts = hostOpts
        self.valueExprs = None
        if hostExprs and ',' in hostExprs:
            self.hostExprs = [h.strip() for h in hostExprs.split(',')]
        elif hostExprs:
            self.hostExprs = [hostExprs]
        else:
            self.hostExprs = None
        self.verbose = verbose
        self.toReport = []
        self.reportSourceNames = []

    def updateSources(self):
        for s in self.reportSourceNames:
            # make sure all sources have been set up (yes,
            # reports are expensive)
            if s not in self.sources:
                if s in self.sourcesClasses and s in self.hostOpts:
                    self.sources[s] = self.sourcesClasses[s](self.hostOpts[s],
                                                             self.verbose)
                else:
                    sys.stderr.write("unknown source encountered: %s\n" % s)

    def addSources(self, moreSources):
        for s in moreSources:
            if s not in self.sources:
                self.sources[s] = moreSources[s]

    def reportHosts(self):
        self.updateSources()
        for s in self.reportSourceNames:
            if s in self.sources and self.sources[s].hosts:
                for h in self.sources[s].hosts:
                    if self.checkHostMatchesHostExpr(h):
                        self.toReport.append(h)

        self.toReport = sorted(list(set(self.toReport)))

    def checkHostMatchesHostExpr(self, host):
        if self.hostExprs:
            # or, not and of the hostExprs
            for e in self.hostExprs:
                if not '*' in e:
                    # no glob, strict match
                    if e == host:
                        return True
                else:
                    # first * is the glob, if you have more than one you lose.
                    first, last = e.split('*', 1)
                    if (host.startswith(first) and host.endswith(last) and
                            len(host) >= len(e) - 1):
                        return True
            return False
        else:
            return True

    def displayHosts(self):
        if not self.toReport:
            print "No hosts to report"
            return

        snames = sorted(self.reportSourceNames)

        # header
        reportLines = []
        reportLines.append(["hosts"] + snames)

        # spacer
        reportLines.append(["" for i in range(0, len(snames) + 1)])

        # host report entries
        for h in self.toReport:
            reportLines.append([h] + [self.getReportValue(h, s)
                                      for s in snames])

        fieldSizes = {}
        for i in range(0, len(reportLines[0])):
            fieldSizes[i] = max([len(l[i]) for l in reportLines])

        print "Hosts report:"

        for l in reportLines:
            for i in range(0, len(l)):
                print l[i].rjust(fieldSizes[i]),
            print

    def matchValueExpr(self, value, valueExpr, negate):
        # these are going to be the list of expr after we split on ;
        # this is an OR list: matches one of a or b or c: display
        # with negative of list:  matches one of a or b or c: don't display
        for e in valueExpr:
            if '*' in e:
                # only one and we take the first one, any later * are
                # considered literal characters
                first, last = e.split('*', 1)
                if (value.startswith(first) and
                    value.endswith(last) and
                        len(value) >= len(e) - 1):
                    match = True
                else:
                    match = False
            else:
                if e == value:
                    match = True
                else:
                    match = False

            # any affirmative match means true (we will show the item)
            if match and not negate:
                return match

            # any affirmative match with a negated list = fail
            # (we will not show the item)
            if match and negate:
                return False

        if negate:
            # did not match any exluded value
            return True
        else:
            # did not match any desired value
            return False

    def filterReportValues(self, values, sourceName):
        if self.valueExprs and sourceName in self.valueExprs:
            return list(set([v for v in values
                             if self.matchValueExpr(v, self.valueExprs[sourceName]['values'],
                                                    self.valueExprs[sourceName]['negate'])]))
        return values

    def getReportValue(self, host, sourceName):
        if (sourceName in self.sources and
            self.sources[sourceName].hosts and
                host in self.sources[sourceName].hosts):
            toDisplay = self.filterReportValues(
                self.sources[sourceName].hosts[host],sourceName)
            count = len(toDisplay)
            if count == 0:
                return "-"
            if count > 1:
                return "count:%s" % count
            elif toDisplay[0] is True:
                return "true"
            else:
                return toDisplay[0]
        else:
            return "-"

    def setValueExprs(self, s):
        if not self.valueExprs:
            self.valueExprs = {}
        if s.endswith('!'):
            s = s[:-1]
            if s not in self.valueExprs:
                self.valueExprs[s] = {}
            self.valueExprs[s]['negate'] = True
        else:
            if s not in self.valueExprs:
                self.valueExprs[s] = {}
            self.valueExprs[s]['negate'] = False

    def processReportArg(self, arg):
        # dns!=10.65*;10.1.*;10.128.*;10.1.*  as an example
        # for one reportSourceName after the split on commas
        if not arg:
            return None
        elif arg == "*":
            return self.sourcesClasses.keys()
        elif "," in arg:
            reportSourceNames = [r.strip() for r in arg.split(',')]
        else:
            reportSourceNames = [arg.strip()]

        self.reportSourceNames = []
        for s in reportSourceNames:
            if '=' in s:
                s, valueExpr = self.getValueExprs(s)
                if not valueExpr or not s:
                    continue

                self.setValueExprs(s)

                # this is a list of exprs
                self.valueExprs[s]['values'] = valueExpr
            self.reportSourceNames.append(s)

        if self.reportSourceNames:
            unknowns = []
            for s in self.reportSourceNames:
                if s not in self.sourcesClasses:
                    sys.stderr.write("unknown source encountered: %s\n" % s)
                    unknowns.append(s)
            self.reportSourceNames = list(set(self.reportSourceNames) -
                                          set(unknowns))

    def getValueExprs(self, sourceNameAndValues):
        if '=' not in sourceNameAndValues:
            sourceName = sourceNameAndValues
            values = None
        else:
            sourceName, values = sourceNameAndValues.split('=', 1)
            values = [v for v in values.split(';') if v]
            if not len(values):
                values = None
        if sourceName[-1] == '!':
            realSourceName = sourceName[:-1]
        else:
            realSourceName = sourceName
        # fixme do we still need this?
        if realSourceName not in self.sourcesClasses:
            print HHelp.usage("Unknown source %s for report\n" % realSourceName)
            return None, None
        else:
            return sourceName, values
