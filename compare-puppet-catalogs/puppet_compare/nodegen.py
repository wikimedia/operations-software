import re
import logging

class NodeFinder(object):

    regexp_node = re.compile('^node\s+/([^/]+)/')
    exact_node = re.compile("node\s*\'([^\']+)\'")
    def __init__(self,sitepp):
        self.regexes = set()
        self.nodes = set()
        for line in sitepp.readlines():
            m = self.regexp_node.search(line)
            if m:
                logging.debug('Found regex in line %s', line.rstrip())
                self.regexes.add(re.compile(m.group(1)))
                continue
            m = self.exact_node.search(line)
            if m:
                logging.debug('Found node in line %s', line.rstrip())
                self.nodes.add(m.group(1))

    def match_physical_nodes(self, nodelist):
        nodes = []
        for node in nodelist:
            discarded=None
            if node in self.nodes:
                logging.debug('Found node %s', node)
                nodes.append(node)
                self.nodes.discard(node)
                continue
            for regex in self.regexes:
                # TODO: this may be very slow, should calculate this
                m = regex.search(node)
                if m:
                    logging.debug('Found match for node %s: %s', node, regex.pattern)
                    nodes.append(node)
                    discarded=regex
                    continue
            if discarded is not None:
                self.regexes.discard(discarded)

        return nodes
