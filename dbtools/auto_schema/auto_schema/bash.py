import re
import subprocess
import sys
import time
from datetime import datetime


def run(command):
    print(datetime.fromtimestamp(time.time()), command)
    if '--run' not in sys.argv and 'show slave' not in command:
        return ''
    if command.startswith('dbctl '):
        return run_dbctl(command)
    return run_internal(command)


def run_dbctl(command):
    if '--run' not in sys.argv:
        return ''
    # Make sure you get a clean dbctl before changing config
    if not command.startswith('dbctl config '):
        diff_res = 'Something'
        while diff_res:
            diff_res = run_dbctl('dbctl config diff')
            if diff_res:
                print(diff_res)
                print('Waiting for dbctl to clear up')
                time.sleep(5)
    res = run_internal(command)
    # Show config
    if not command.startswith('dbctl config '):
        run_dbctl('dbctl config diff')
    return res


def run_internal(command):
    """Do not call this function directly."""
    res = subprocess.run(command, capture_output=True, shell=True)
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
