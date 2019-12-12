#!/usr/bin/python3
import json
import os
import sys
import urllib.request
from subprocess import call, run, PIPE

from script_utils import Colors, p, check_yes_no, check_command

PORT_KEY = "port"
INPUT_PATH_KEY = "input_dir"
OUTPUT_PATH_KEY = "output_dir"
USER_KEY = "user"
CONTAINER_NAME_KEY = "container_name"
PERSIST_KEY = "persist"
DARKSKY_TOKEN_KEY = "darksky_token"

CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), '.uv-server.conf')
FNULL = open(os.devnull, 'w')


def save_config(port, input_path, output_path, user, container_name, persist, darksky_token):
    config = {
        PORT_KEY: port,
        INPUT_PATH_KEY: input_path,
        OUTPUT_PATH_KEY: output_path,
        USER_KEY: user,
        CONTAINER_NAME_KEY: container_name,
        PERSIST_KEY: persist,
        DARKSKY_TOKEN_KEY: darksky_token
    }
    with open(CONFIG_FILE_PATH, 'w') as config_file:
        json.dump(config, config_file)
    print(f"Config file saved to '{CONFIG_FILE_PATH}'.")
    print()


def load_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        return {}

    print("* A config file was found from a previous install. Do you want to reuse its values? (Y/n)")
    if check_yes_no():
        with open(CONFIG_FILE_PATH, 'r') as config_file:
            config = json.load(config_file)
            print("* Config loaded")
            return config
    else:
        return {}


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


def check_darksky_token(token):
    return token.strip()


def check_version(value, versions):
    index = int(value)
    if index < 0 or index > len(versions):
        raise ValueError(f"The value must be between 0 and {len(versions)}")
    return index


def run_installer():
    print()
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
    print()

    prev_config = load_config()

    if PORT_KEY in prev_config:
        port = prev_config[PORT_KEY]
        print(f" Using port {port}")
    else:
        print("* On which port do you want the application to listen? (Default: 8080)")
        port = input_check(int, "Port must be a number", 8080)
        print()

    if CONTAINER_NAME_KEY in prev_config:
        container_name = prev_config[CONTAINER_NAME_KEY]
        print(f" Using container name {container_name}")
    else:
        print("* Docker container name (the local name for the container - Default: buvic):")
        container_name = input_check(check_container_name, default_value="buvic")
        print()

    if INPUT_PATH_KEY in prev_config:
        input_path = prev_config[INPUT_PATH_KEY]
        print(f" Using input path {input_path}")
    else:
        print("* Absolute path to the raw measurement files:")
        input_path = input_check(check_path_exists)
        print()

    if OUTPUT_PATH_KEY in prev_config:
        output_path = prev_config[OUTPUT_PATH_KEY]
        print(f" Using output path {output_path}")
    else:
        print("* Absolute path for the output files:")
        output_path = input_check(check_path_exists)
        print()

    if USER_KEY in prev_config:
        user = prev_config[USER_KEY]
        print(f" Using user id {user}")
    else:
        print("* User which will write the output files: (Default: not defined. In most cases this will default to root)")
        user = input_check(check_user, none_default=True)
        print()

    if PERSIST_KEY in prev_config:
        persist = prev_config[PERSIST_KEY]
        print(f" Start at boot: {persist}")
    else:
        print("* Do you want the container to start automatically at boot? (Y/n)")
        persist = check_yes_no()

    if DARKSKY_TOKEN_KEY in prev_config:
        darksky_token = prev_config[DARKSKY_TOKEN_KEY]
        if darksky_token is None:
            print(f" darksky token: None")
        else:
            print(f" darksky token: ****")
    else:
        print("* Your 'darksky.net' api token?")
        darksky_token = input_check(check_darksky_token, none_default=True)
    print()

    link = "https://registry.hub.docker.com/v1/repositories/pmodwrc/buvic/tags"
    with urllib.request.urlopen(link) as url:
        data = json.loads(url.read().decode())

    print("* Which version do you want to install?")
    print(" 0: Local copy (Default)")
    for index, version in enumerate(data):
        print(f" {index + 1}: {version['name']}")
    version_index = input_check(lambda value: check_version(value, data), default_value=0)
    if version_index == 0:
        version = ""
    else:
        version = ":" + data[version_index - 1]["name"]

    if version == ":latest":
        must_pull = True
    elif not check_command(f"docker image inspect pmodwrc/buvic{version} >/dev/null 2>&1 || exit 1"):
        print(f"* Docker image pmodwrc/buvic{version} does not exist locally")
        must_pull = True
    else:
        must_pull = False

    if must_pull:
        print("* Pulling docker image")
        print(Colors.LIGHTGRAY, end='', flush=True)
        result = call(["docker", "pull", f"pmodwrc/buvic{version}"])
        print(Colors.ENDC, end='', flush=True)
        if result != 0:
            p("ERROR: An error occurred while pulling image!", Colors.ERROR)
            print("Exiting")
            sys.exit(1)

    print()

    if check_command(f"docker ps -a | grep -q \" {container_name}$\""):
        print(f"* A container with the name {container_name} already exist. Do you want to replace it? (Y/n)")
        if check_yes_no():
            print()
            print(f"* Stopping container {container_name}")
            run(f"docker stop {container_name}", shell=True, stdout=FNULL)
            print()
            print(f"* Removing container {container_name}")
            run(f"docker rm {container_name}", shell=True, stdout=FNULL)
        else:
            print("Chose to not replace previous container.")
            print("Cancelling")
            sys.exit()
    print()

    print("* Starting server")
    docker_command = ["docker", "run", "--init", "-d", f"-p {port}:4444", f"-v {input_path}:/data", f"-v {output_path}:/out"]
    if user is not None:
        docker_command.extend(["--user", f"{user}"])

    if persist:
        docker_command.append("--restart always")

    if darksky_token is not None:
        docker_command.extend([f"-e DARKSKY_TOKEN={darksky_token}"])

    docker_command.extend(["-e PORT=4444", f"--name {container_name}", f"pmodwrc/buvic{version}"])
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

    save_config(port, input_path, output_path, user, container_name, persist, darksky_token)


try:
    run_installer()
except KeyboardInterrupt:
    print(Colors.ENDC)
