import threading
import logging
import time
try:
    # python 2.x
    import Queue as queue
except ImportError:
    # python 3.x
    import queue


class ThreadExecutor(threading.Thread):

    def __init__(self, queue, out_queue):
        super(ThreadExecutor, self).__init__()
        self.queue = queue
        self.out_queue = out_queue

    def run(self):
        logging.debug('Spawning a Thread executor')
        while True:
            # grab data from queue
            (payload, args, kwdargs) = self.queue.get()
            if payload == '__exit__':
                logging.debug('Stopping Thread')
                return
            logging.debug('Executing payload %s', payload)
            try:
                retval = payload(*args, **kwdargs)
                msg = {
                    'is_error': False, 'value': retval, 'data': (args, kwdargs)}
                self.out_queue.put(msg)
            except Exception as e:
                # TODO: log correctly
                logging.error("Error in payload")
                logging.debug(str(e))
                msg = {'is_error': True, 'value': e, 'data': (args, kwdargs)}
                self.out_queue.put(msg)
            finally:
                logging.debug('Execution terminated')
                self.queue.task_done()


class ThreadOrchestrator(object):

    def __init__(self, pool_size=4):
        self.pool_size = pool_size
        self._TP = []
        self._payload_queue = queue.Queue()
        self._incoming_queue = queue.Queue()
        for i in xrange(self.pool_size):
            t = ThreadExecutor(self._payload_queue, self._incoming_queue)
            # this thread will exit with the main program
            self._TP.append(t)
            t.start()

    def add(self, payload, *args, **kwdargs):
        self._payload_queue.put((payload, args, kwdargs))

    def fetch(self, on_error):
        # wait for all executions to terminate.
        self._payload_queue.join()

        count = ok = errors = 0
        while not self._incoming_queue.empty():
            count += 1
            res = self._incoming_queue.get(True)
            if res['is_error']:
                errors += 1
                on_error(res)
            else:
                ok += 1
            self._incoming_queue.task_done()
        for i in xrange(len(self._TP)):
            self._payload_queue.put(('__exit__', None, None))
        self._TP = []
        return (count, ok, errors)
