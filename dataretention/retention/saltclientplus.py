import salt.client
import salt.utils
import time

class LocalClientPlus(salt.client.LocalClient):
    '''
    extend the salt LocalClient module with methods for showing
    list of known minions that match the specified expression,
    and for copying file content to a newly created remote file
    '''

    @staticmethod
    def condition_kwarg(arg, kwarg):
        '''
        Return a single arg structure for caller to use
        '''
        if isinstance(kwarg, dict):
            kw_ = []
            for key, val in kwarg.items():
                kw_.append('{0}={1}'.format(key, val))
            return list(arg) + kw_
        return arg

    def cmd_expandminions(self, tgt, fun, arg=(), timeout=30,
                          expr_form='glob', ret='',
                          kwarg=None, **kwargs):
        '''
        return an expanded list of minions, assuming that the expr form
        is glob or list or some other such thing that can be expanded
        and not e.g. grain based

        this is wasteful because we actually run the job but it's less
        wasteful than
          salt "$hosts" -v --out raw test.ping |
          grep '{' | mawk -F"'" '{ print $2 }'
        '''
        arg = LocalClientPlus.condition_kwarg(arg, kwarg)
        job = self.run_job(tgt, fun, arg, expr_form, ret,
                           timeout, **kwargs)

        if not job:
            print "WARNING: failed to get any valid minions from", tgt
            return []
        else:
            time.sleep(3)
            hosts = []
            returned = self.get_cli_returns(job['jid'], set(job['minions']))
            for resp in returned:
                for host in resp:
                    hosts.append(host)
            return list(set(hosts))
