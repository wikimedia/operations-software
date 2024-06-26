import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime


def run(command):
    print(datetime.fromtimestamp(time.time()), command)
    if '--run' not in sys.argv and 'show slave' not in command:
        return ''
    if command.startswith('dbctl '):
        return run_dbctl(command)
    return _run_internal(command).output


def run_dbctl(command):
    if '--run' not in sys.argv:
        return ''
    # Make sure you get a clean dbctl before changing config
    if not command.startswith('dbctl config '):
        # dbctl config diff returns non-zero status on diff.
        while _run_internal('dbctl config diff').returncode != 0:
            print('Waiting for dbctl to clear up')
            time.sleep(5)
    res = _run_internal(command)
    # Show config
    if not command.startswith('dbctl config '):
        run_dbctl('dbctl config diff')
    return res.output


@dataclass
class _Result:
    output: str
    returncode: int


def _run_internal(command):
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
    return _Result(output=output, returncode=res.returncode)
