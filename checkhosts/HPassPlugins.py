class HPassPlugins(object):
    """plugins for scrounging passwords from various
    configuration files, because we are bored of
    typing them in or grepping for them from the
    command line

    if you want other plugins add them to the hash 'plugins'
    and make sure they return the password on success or
    None on error"""

    def __init__(self):
        self.plugins = {'getpwdfromfile': self.getNameValueFromFile}

    def getNameValueFromFile(self, args):
        """this will ignore tabs and spaces, it will strip
        double and single quotes around the value (so hope
        your password doesn't start or end with one)"""

        if len(args) != 2:
            raise ValueError("this passplugin requires two parameters," +
                             "but %d was/were provided\n" % len(args))
        fileName = args[0]
        name = args[1]
        fd = open(fileName, "r")
        if not fd:
            return None
        result = fd.read().splitlines()
        fd.close()
        for l in result:
            l = l.strip()
            if l.startswith(name):
                if '=' in l:
                    option, value = l.split('=', 1)
                    if option.strip() == name:
                        return value.strip("'\" \t")
        return None
