import os
import sys
import ConfigParser
from HSources import Source


class CheckHostsConfig(object):
    """
    this class handles all aspects of configuration
    files and options defaults
    """

    def __init__(self, configFile=False):
        home = os.path.dirname(sys.argv[0])
        if (not configFile):
            configFile = "checkhosts.conf"
        self.files = [
            os.path.join(home, configFile),
            "/etc/checkhosts.conf",
            os.path.join(os.getenv("HOME"), ".checkhosts.conf")]
        self.defaults = {}
        for c in Source.__subclasses__():
            self.mergeDefaults(c.getConfigDefaults())

        self.conf = ConfigParser.SafeConfigParser(self.defaults)
        self.conf.read(self.files)
        self.conf.options = self.parseConfFile()

    def mergeDefaults(self, toMerge):
        for d in toMerge:
            self.defaults[d] = toMerge[d]

    def parseConfFile(self):
        if not self.conf.has_section('sources'):
            self.conf.add_section('sources')

        configInfo = {}
        for c in Source.__subclasses__():
            configInfo[c.getSourceName()] = c.getConfig(self.conf, "sources")

        if not self.conf.has_section('globals'):
            self.conf.add_section('globals')

        configInfo['globals'] = c.getConfig(self.conf, "globals")

        return configInfo
