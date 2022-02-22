import os
import sys
import time
from datetime import datetime


class Logger(object):
    def __init__(self, ticket):
        if '--run' in sys.argv:
            file_name = ticket + '.log'
        else:
            file_name = ticket + '-dry.log'
        self.file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'logs',
            file_name
        )

    def log(self, msg):
        print(datetime.fromtimestamp(time.time()), msg)

    def log_file(self, msg):
        print(msg)
        mode = 'w' if not os.path.exists(self.file_path) else 'a'
        with open(self.file_path, mode) as f:
            f.write(str(datetime.fromtimestamp(time.time())) + ' ' + msg + '\n')
