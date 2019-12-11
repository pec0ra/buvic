import os
from subprocess import PIPE, run

FNULL = open(os.devnull, 'w')


class Colors:
    HEADER = '\x1b[37;44m'
    LIGHTGRAY = '\x1b[37m'
    OKBLUE = '\x1b[34m'
    ERROR = '\x1b[31m'
    WARNING = '\x1b[33m'
    ENDC = '\x1b[0m'


def p(text, color):
    print(color + text + Colors.ENDC)


def check_yes_no():
    print(Colors.OKBLUE, end='')
    value = input()
    print(Colors.ENDC, end='')
    if value.lower() == "n" or value.lower() == "no":
        return False
    else:
        return True


def run_command(command, show_std_err=False, pipe_stdout=True):
    print(Colors.LIGHTGRAY, end='', flush=True)
    stderr = None if show_std_err else FNULL
    stdout = PIPE if pipe_stdout else None
    result = run(command, stdout=stdout, stderr=stderr, shell=True)
    print(Colors.ENDC, end='', flush=True)
    return result


def check_command(command, show_std_err=False):
    try:
        result = run_command(command, show_std_err)
    except OSError:
        return False
    if result.returncode != 0:
        return False
    else:
        return True
