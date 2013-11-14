import sys
from HSources import Source

class HostFilter(object):
    """
    display a list of hosts in given sources, or with attribute
    values meeting certain assertions for those sources
    hosts appear in the list with the short name because some sources do
    not have the fqdn
    """

    def __init__(self, hostOpts, hostExprs, verbose):
        self.sources = {}
        self.filteredHosts = {}
        self.hostOpts = hostOpts
        if hostExprs and ',' in hostExprs:
            self.hostExprs = [h.strip() for h in hostExprs.split(',')]
        elif hostExprs:
            self.hostExprs = [hostExprs]
        else:
            self.hostExprs = None
        self.verbose = verbose
        self.sourcesClasses = {}
        for c in Source.__subclasses__():
            self.sourcesClasses[c.getSourceName()] = c
        self.filters = None

    def updateSources(self):
        for s in self.filters:
            # make sure all sources the caller wants are set up
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

    def mustBePresent(self, possibleHosts):
        for s in self.filters:
            # format of filter expression:
            # *  -- it's present
            # any other value -- it's present in the dict with
            #                    the specific value
            # starts with !   -- it's not (whatever the rest of
            #                    the expression says)
            # note that leading/trailing whitespace around expression
            # (and after !) will be stripped)

            if self.filters[s] == "*":
                if possibleHosts is None:
                    possibleHosts = {}
                    for h in self.sources[s].hosts:
                        possibleHosts[h] = True
                else:
                    for h in possibleHosts.keys():
                        if h not in self.sources[s].hosts:
                            possibleHosts.pop(h, None)
            return possibleHosts

    def mustHaveValue(self, possibleHosts):
        for s in self.filters:
            if (not self.filters[s] == "*" and
                    not self.filters[s].startswith("!")):

                if possibleHosts is None:
                    possibleHosts = {}
                    for h in self.sources[s].hosts:
                        if self.filters[s] in self.sources[s].hosts[h]:
                            possibleHosts[h] = True
                else:
                    for h in possibleHosts.keys():
                        if ((not h in self.sources[s].hosts) or
                            (h in self.sources[s].hosts and
                             self.filters[s] not in self.sources[s].hosts[h])):
                            possibleHosts.pop(h, None)
        return possibleHosts

    def mustNotHaveValue(self, possibleHosts, s, expr):
        if possibleHosts is None:
            possibleHosts = {}
            for h in self.sources[s].hosts:
                if expr not in self.sources[s].hosts[h]:
                    possibleHosts[h] = True
        else:
            for h in possibleHosts.keys():
                if ((not h in self.sources[s].hosts) or
                    (h in self.sources[s].hosts and
                     expr in self.sources[s].hosts[h])):
                    possibleHosts.pop(h, None)
        return possibleHosts

    def mustBeAbsent(self, possibleHosts, s):
        if possibleHosts is not None:
            for h in possibleHosts.keys():
                if h in self.sources[s].hosts:
                    possibleHosts.pop(h, None)
        return possibleHosts

    def filterByHostExprs(self, possibleHosts):
        self.filteredHosts = {}
        # we do or, not and, for the hostExprs
        for e in self.hostExprs:
            if not '*' in e:
                # no glob, strict match
                if e in possibleHosts:
                    self.filteredHosts[e] = True
            else:
                # first * is the glob, if you have more than one you lose.
                first, last = e.split('*', 1)
                for h in possibleHosts.keys():
                    if (h.startswith(first) and h.endswith(last) and
                            len(h) >= len(e) - 1):
                        self.filteredHosts[h] = True

    def filterHosts(self):
        self.updateSources()
        if not self.sources:
            return

        self.filteredHosts = {}
        possibleHosts = None

        # first go through all the 'must be present' checks
        possibleHosts = self.mustBePresent(possibleHosts)
        # now do all the 'must have specified value' checks
        possibleHosts = self.mustHaveValue(possibleHosts)

        for s in self.filters:
            if self.filters[s].startswith("!"):
                expr = self.filters[s][1:].strip()

                if expr != "*":
                    # now do all the 'must not be this value' checks
                    possibleHosts = self.mustNotHaveValue(possibleHosts,
                                                          s, expr)
                else:
                    # now do the 'must be absent' checks
                    possibleHosts = self.mustBeAbsent(possibleHosts, s)

        if self.hostExprs:
            self.filteredHosts = self.filterByHostExprs(possibleHosts)
        else:
            self.filteredHosts = possibleHosts

    def displayHosts(self):
        if not self.filteredHosts:
            print "No hosts match filter"
            return

        print "Filter results:"
        for h in sorted(self.filteredHosts):
            print "  ", h

    def processFilterArg(self, filterExpr):
        result = {}

        if "," in filterExpr:
            assertions = [f.strip() for f in filterExpr.split(",")]
        else:
            assertions = [filterExpr.strip()]
        for a in assertions:
            if not '=' in a:
                print "Bad format for assertion %s\n" % a
                self.filters = None
                return
            sourceName, criterion = a.split("=", 1)
            sourceName = sourceName.strip()
            criterion = criterion.strip()

            if sourceName not in self.sourcesClasses:
                print "Unknown source for assertion %s" % a
                self.filters = None
                return
            result[sourceName] = criterion
        self.filters = result
