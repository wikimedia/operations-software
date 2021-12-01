import re
import subprocess
import sys
import time
from datetime import datetime


def run(command):
    print(datetime.fromtimestamp(time.time()), command)
    if '--run' in sys.argv or 'show slave' in command:
        if command.startswith(
                'dbctl ') and not command.startswith('dbctl config '):
            diff_res = 'Something'
            while diff_res:
                diff_res = run('dbctl config diff')
                if diff_res:
                    print(diff_res)
                    print('Waiting for the dbctl to clear up')
                    time.sleep(5)
        res = subprocess.run(command, capture_output=True, shell=True)
        if command.startswith(
                'dbctl ') and not command.startswith('dbctl config '):
            run('dbctl config diff')
        stderr = res.stderr.decode('utf-8')
        stderr_cleaned = re.sub(r'\s', '', stderr)
        if stderr_cleaned:
            print('ERROR: ')
            print('--------')
            print(stderr)
            print('--------')
        else:
            stderr = ''
        stdout = res.stdout.decode('utf-8')
        print('STDOUT')
        stdout_cleaned = re.sub(r'\s', '', stdout)
        if stdout_cleaned:
            print(stdout)
        else:
            stdout = ''

        output = stdout
        if stderr_cleaned:
            output += '\nerror:\n' + stderr
        return output
    return ''
