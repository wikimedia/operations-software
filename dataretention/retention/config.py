import os
import salt.utils.yamlloader

cf = {}

def set_up_conf():
    global cf

    if cf:
        return

    print "INFO: about to parse config yaml"
    if os.path.exists('/srv/salt/audits/retention/configs/config.yaml'):
        try:
            contents = open('/srv/salt/audits/retention/configs/config.yaml').read()
            yamlcontents = salt.utils.yamlloader.load(contents, Loader=salt.utils.yamlloader.SaltYamlSafeLoader)
            # fixme do I need this or will a direct assign get it?
            for key in yamlcontents:
                cf[key] = yamlcontents[key]
        except:
            raise
