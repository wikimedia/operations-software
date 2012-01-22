#!/usr/bin/python

class Error(Exception):
    pass

def TabExtend(parts, depth=1):
    """Prepend a tab to every item in parts, and return it."""
    return ['\t' * depth + p for p in parts]

class JunosSlaxBase(object):
    def GenerateRules(self):
        return '\n'.join(self.GetRuleParts())
    

class Firewall(JunosSlaxBase):
    """Shell class to represent JunOS firewall rules.

    Append Filter objects into the filters attribute.
    """
    def __init__(self):
        self.filters = []

    def GetRuleParts(self):
        parts = []
        if self.filters:
            for level in ('firewall', 'family', 'inet'):
                parts.append('\t' * len(parts) + '<%s> {' % (level))

            tab_depth = len(parts)
            for f in self.filters:
                parts.extend(TabExtend(f.GetRuleParts(), tab_depth))

            for i in xrange(tab_depth, 0, -1):
                parts.append('\t' * (i - 1) + '}')
        return parts


class Filter(JunosSlaxBase):
    """Pretty trivial Filter definition for Junos SLAX firewall rules.

    Append Term objects into the "terms" attribute.
    """
    def __init__(self, name):
        self.name = name
        self.terms = []

    def GetRuleParts(self):
        parts = []
        if self.terms:
            parts.append('<filter> "%s" {' % (self.name))
            for term in self.terms:
                parts.extend(TabExtend(term.GetRuleParts()))
            parts.append('}')
        return parts

    def GenerateRules(self):
        return '\n'.join(self.GetRuleParts())


class Term(JunosSlaxBase):
    def __init__(self, name):
        self.name = name
        self.established = False
        self.source_addr = []
        self.source_port = []
        self.destination_addr = []
        self.destination_port = []
        self.protocol = None
        self.actions = []
    
    def GetRuleParts(self):
        parts = []

        from_parts = []

        # These two helpers adjust "from_parts" from the outer scope.
        def _GenAddrs(endpoint, addrs):
            if addrs:
                from_parts.append('<%s-address> {' % endpoint)
                for ip in addrs:
                    from_parts.append('\t%s/32;' % ip)
                from_parts.append('}')

        def _GenPorts(endpoint, ports):
            if ports:
                if len(ports) > 1:
                    port = '[%s]' % ' '.join(ports)
                else:
                    port = '%s' % ' '.join(ports)
                from_parts.append('<%s-port> %s;' % (endpoint, ports[0]))

        # What type of traffic are filtering:
        _GenAddrs('source', self.source_addr)
        _GenPorts('source', self.source_port)
        _GenAddrs('destination', self.destination_addr)
        _GenPorts('destination', self.destination_port)
        if self.protocol:
            from_parts.append('<protocol> %s;' % (self.protocol))
        
        if self.established:
            if self.protocol != 'tcp':
                raise Error(
                    'Setting an established rule without TCP is invalid.')
            from_parts.append('<tcp-established>;')

        if from_parts:
            parts.append('<from> {')
            parts.extend(TabExtend(from_parts))
            parts.append('}')  # end of from

        # What do we do with it?
        parts.append('<then> {')
        actions = []
        if self.established:
            actions.append('<count> established;')
            actions.append('<accept>;')
        for action in self.actions:
            actions.append(action + ';')
        if not actions:
            actions.append('<accept>;')
        parts.extend(TabExtend(actions))
        parts.append('}')

        return ['<term> { "%s"' % self.name] + TabExtend(parts) + ['}']

    def GenerateRules(self):
        return '\n'.join(self.GetRuleParts())


if __name__ == '__main__':
    # Example firewall generation:
    firewall = Firewall()
    filter = Filter('imafilter')
    firewall.filters.append(filter)

    term = Term('example')
    term.source_addr.append('10.0.0.2')
    term.destination_port.append('22')
    term.protocol = 'tcp'
    filter.terms.append(term)
    
    term = Term('established')
    term.established = True
    term.protocol = 'tcp'
    filter.terms.append(term)
    
    term = Term('other')
    term.actions.append('discard')
    filter.terms.append(term)
    
    print firewall.GenerateRules()
