def get_hosts_expr_type(hosts_expr):
    '''
    return the type of salt host expr and stash
    the converted expression as well
    '''

    if hosts_expr.startswith('grain:'):
        hosts = hosts_expr[6:]
        return hosts, 'grain'
    elif hosts_expr.startswith('pcre:'):
        hosts = hosts_expr[5:]
        return hosts, 'pcre'
    elif hosts_expr.startswith('list:'):
        hosts = hosts_expr[5:].split(',')
        return hosts, 'list'
    else:
        hosts = hosts_expr
        return hosts, 'glob'  # default


class JsonHelper(object):
    # adapted from
    # http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-ones-from-json-in-python
    @staticmethod
    def decode_list(data):
        result = []
        for item in data:
            if isinstance(item, unicode):
                item = item.encode('utf-8', 'replace')
            elif isinstance(item, list):
                item = JsonHelper.decode_list(item)
            elif isinstance(item, dict):
                item = JsonHelper.decode_dict(item)
            result.append(item)
        return result

    @staticmethod
    def decode_dict(data):
        result = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8', 'replace')
            elif isinstance(value, list):
                value = JsonHelper.decode_list(value)
            elif isinstance(value, dict):
                value = JsonHelper.decode_dict(value)
            result[key] = value
        return result
