import os
import salt.utils.yamlloader

conf = None

def set_up_conf(confdir):
    global conf

    if conf is not None:
        return

    configfile = os.path.join(confdir, 'config.yaml')
    if os.path.exists(configfile):
        conf = {}
        try:
            contents = open(configfile).read()
            yamlcontents = salt.utils.yamlloader.load(contents, Loader=salt.utils.yamlloader.SaltYamlSafeLoader)
            # fixme do I need this or will a direct assign get it?
            for key in yamlcontents:
                conf[key] = yamlcontents[key]
        except:
            raise
