import re

class Status(object):
    '''
    manage statuses (good, problem, etc) of files/dirs
    '''

    status_expr = r"^\s*'%s'\s*:\s*\[\s*(\],?)?\s*$"
    status_cf = {'good': ['G', re.compile(status_expr % 'good')],
                 'problem': ['P', re.compile(status_expr % 'problem')],
                 'recheck': ['R', re.compile(status_expr % 'recheck')],
                 'unreviewed': ['U', re.compile(status_expr % 'unreviewed')]}

    STATUSES = [status_cf[key][0] for key in status_cf]
    STATUS_TEXTS = [key for key in status_cf]

    @staticmethod
    def status_to_text(abbrev):
        for key in Status.status_cf:
            if Status.status_cf[key][0] == abbrev:
                return key
        return None

    @staticmethod
    def text_to_status(abbrev):
        for key in Status.status_cf:
            if key == abbrev:
                return Status.status_cf[key][0]
        return None

    @staticmethod
    def get_statuses_prompt(separator):
        return separator.join(["%s(%s)" %
                               (key, Status.status_cf[key][0])
                               for key in Status.status_cf])
