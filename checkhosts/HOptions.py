def getOptions(value, names):
    value = value.strip()
    pieces = value.split(",", len(names) -1)
    opts = {}
    if not len(names):
        return opts
    for i in range(0, len(pieces)):
        opts[names[i]] = pieces[i]
    for i in range(len(pieces), len(names)):
        opts[names[i]] = None
    return opts

def mergeDefaults(defaults, settings):
    """given default settings, merge them into the
    new settings passed in and return the merged ones"""

    if not settings:
        return defaults

    for item in settings:
#        if settings[item] == None or settings[item] == '':
        if not settings[item]:  # empty list, empty string, None, etc
            if item in defaults:
                settings[item] = defaults[item]
    for item in defaults:
        if item not in settings:
            settings[item] = defaults[item]
    return settings
