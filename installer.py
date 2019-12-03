#!/usr/bin/python3
import os
import sys
from subprocess import call, run, PIPE

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


def input_check(check_value, error_message=None, default_value=None, none_default=False):
    while True:
        print(Colors.OKBLUE, end='')
        value = input()
        print(Colors.ENDC, end='')
        if not value and (default_value is not None or none_default):
            return default_value
        try:
            return check_value(value)
        except Exception as e:
            if error_message is None:
                p(str(e), Colors.WARNING)
            else:
                p(error_message, Colors.WARNING)


def run_command(command, show_std_err=False):
    stderr = None if show_std_err else FNULL
    return run(command, stdout=FNULL, stderr=stderr, shell=True)


def check_command(command, show_std_err=False):
    try:
        result = run_command(command, show_std_err)
    except OSError:
        return False
    if result.returncode != 0:
        return False
    else:
        return True


def check_container_name(name):
    if ' ' in name:
        raise ValueError("Container name cannot contain spaces")
    return name


def check_path_exists(path):
    if not os.path.isabs(path):
        raise ValueError("Path is not absolute")
    if not os.path.isdir(path):
        raise ValueError("Path does not exist")
    return path


def check_user(user):
    uid_res = run(f"id -u {user}", stdout=PIPE, stderr=FNULL, universal_newlines=True, shell=True)
    if uid_res.returncode != 0:
        raise ValueError("User does not exist")

    gid_res = run(f"id -g {user}", stdout=PIPE, stderr=FNULL, universal_newlines=True, shell=True)
    if gid_res.returncode != 0:
        raise ValueError("User does not exist")
    return uid_res.stdout.rstrip() + ":" + gid_res.stdout.rstrip()


def check_yes_no(value):
    if value.lower() == "n" or value.lower() == "no":
        return False
    else:
        return True


def run_installer():
    p("                                                                    ", Colors.HEADER)
    p("                   Irradiance calculator installer                  ", Colors.HEADER)
    p("                                                                    ", Colors.HEADER)
    print()
    print("* Checking requirements...")

    if not check_command(["docker", "-v"]):
        print()
        p("ERROR: Docker is not installed or doesn't work correctly!", Colors.ERROR)
        print("Exiting")
        sys.exit(1)

    print("* On which port do you want the application to listen? (Default: 8080)")
    port = input_check(int, "Port must be a number", 8080)
    print()

    print("* Docker container name (the local name for the container - Default: uv-server):")
    container_name = input_check(check_container_name, default_value="uv-server")
    print()

    print("* Absolute path to the raw measurement files:")
    input_path = input_check(check_path_exists)
    print()

    print("* Absolute path for the output files:")
    output_path = input_check(check_path_exists)
    print()

    print("* User which will write the output files: (Default: not defined. In most cases this will default to root)")
    user = input_check(check_user, none_default=True)
    print()

    print("* Pulling required docker image")
    print(Colors.LIGHTGRAY, end='', flush=True)
    result = call(["docker", "pull", "pec0ra/uv-server"])
    print(Colors.ENDC, end='', flush=True)
    if result != 0:
        p("ERROR: An error occurred while pulling image!", Colors.ERROR)
        print("Exiting")
        sys.exit(1)

    print()

    print("* Checking container name availability")
    if check_command(f"docker ps -a | grep -q \" {container_name}$\""):
        print(f"A container with the name {container_name} already exist. Do you want to remove it? (Y/n)")
        print(Colors.OKBLUE, end='')
        value = input()
        print(Colors.ENDC, end='')
        if check_yes_no(value):
            print()
            print(f"* Stopping container {container_name}")
            run(f"docker stop {container_name}", shell=True, stdout=FNULL)
            print()
            print(f"* Removing container {container_name}")
            run(f"docker rm {container_name}", shell=True, stdout=FNULL)
        else:
            print("Chose to not overwrite previous container.")
            print("Cancelling")
            sys.exit()
    print()

    print("* Starting server")
    docker_command = ["docker", "run", "-d", f"-p {port}:4444", f"-v {input_path}:/data", f"-v {output_path}:/out"]
    if user is not None:
        docker_command.extend(["--user", f"{user}"])

    docker_command.extend(["-e PORT=4444", f"--name {container_name}", "pec0ra/uv-server"])
    print(" ".join(docker_command))
    print(Colors.LIGHTGRAY, end='', flush=True)
    result = run(" ".join(docker_command), shell=True)
    print(Colors.ENDC, end='', flush=True)
    if result.returncode != 0:
        p("ERROR: An error occurred while starting the server!", Colors.ERROR)
        print("Exiting")
        sys.exit(1)

    print()
    p("                                                                    ", Colors.HEADER)
    p("                     Server started successfully.                   ", Colors.HEADER)
    p(f"         Application can be accessed at http://localhost:{str(port).ljust(5)}      ", Colors.HEADER)
    p("                                                                    ", Colors.HEADER)
    print()


try:
    run_installer()
except KeyboardInterrupt:
    print(Colors.ENDC)
