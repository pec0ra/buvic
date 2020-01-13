#!/usr/bin/env python3
#
# Copyright (c) 2020 Basile Maret.
#
# This file is part of BUVIC - Brewer UV Irradiance Calculator
# (see https://github.com/pec0ra/buvic).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import json
import os
import re
import sys
import urllib.request
from subprocess import call, run, PIPE

PORT_KEY = "port"
INSTR_PATH_KEY = "instr_dir"
UV_DATA_PATH_KEY = "uvdata_dir"
OUTPUT_PATH_KEY = "output_dir"
USER_KEY = "user"
CONTAINER_NAME_KEY = "container_name"
PERSIST_KEY = "persist"
DARKSKY_TOKEN_KEY = "darksky_token"

CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".buvic.conf")
FNULL = open(os.devnull, "w")


class Colors:
    HEADER = "\x1b[37;44m"
    LIGHTGRAY = "\x1b[37m"
    OKBLUE = "\x1b[34m"
    ERROR = "\x1b[31m"
    WARNING = "\x1b[33m"
    ENDC = "\x1b[0m"


def p(text, color):
    print(color + text + Colors.ENDC)


def save_config(port, instr_path, uvdata_path, output_path, user, container_name, persist, darksky_token):
    config = {
        PORT_KEY: port,
        INSTR_PATH_KEY: instr_path,
        UV_DATA_PATH_KEY: uvdata_path,
        OUTPUT_PATH_KEY: output_path,
        USER_KEY: user,
        CONTAINER_NAME_KEY: container_name,
        PERSIST_KEY: persist,
        DARKSKY_TOKEN_KEY: darksky_token,
    }
    with open(CONFIG_FILE_PATH, "w") as config_file:
        json.dump(config, config_file)
    print(f"Config file saved to '{CONFIG_FILE_PATH}'.")
    print()


def load_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        return {}

    print("* A config file was found from a previous install. Do you want to reuse its values? (Y/n)")
    if check_yes_no():
        with open(CONFIG_FILE_PATH, "r") as config_file:
            config = json.load(config_file)
            print("* Config loaded")
            return config
    else:
        return {}


def check_yes_no():
    print(Colors.OKBLUE, end="")
    value = input()
    print(Colors.ENDC, end="")
    if value.lower() == "n" or value.lower() == "no":
        return False
    else:
        return True


def run_command(command, show_std_err=False, pipe_stdout=True):
    print(Colors.LIGHTGRAY, end="", flush=True)
    stderr = None if show_std_err else FNULL
    stdout = PIPE if pipe_stdout else None
    result = run(command, stdout=stdout, stderr=stderr, shell=True)
    print(Colors.ENDC, end="", flush=True)
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


def input_check(check_value, error_message=None, default_value=None, none_default=False):
    while True:
        print(Colors.OKBLUE, end="")
        value = input()
        print(Colors.ENDC, end="")
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
    if " " in name:
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

    if INSTR_PATH_KEY in prev_config:
        instr_path = prev_config[INSTR_PATH_KEY]
        print(f" Using instr path {instr_path}")
    else:
        print("* Absolute path to the instrument files (arf and uvr files):")
        instr_path = input_check(check_path_exists)
        print()

    if UV_DATA_PATH_KEY in prev_config:
        uvdata_path = prev_config[UV_DATA_PATH_KEY]
        print(f" Using uvdata path {uvdata_path}")
    else:
        print("* Absolute path to the raw measurement files (uv and b files):")
        uvdata_path = input_check(check_path_exists)
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

    if "DOCKER_REPOSITORY" in os.environ:
        # If the environment variable `DOCKER_REPOSITORY` is defined, we use it as registry
        docker_repository = os.path.join(os.environ["DOCKER_REPOSITORY"], "")
        link = f"https://{docker_repository}v2/pmodwrc/buvic/tags/list"
        with urllib.request.urlopen(link) as url:
            data = json.loads(url.read().decode())
        tags = data["tags"]
    else:
        docker_repository = ""
        link = "https://registry.hub.docker.com/v1/repositories/pmodwrc/buvic/tags"
        with urllib.request.urlopen(link) as url:
            data = json.loads(url.read().decode())
        tags = [d["name"] for d in data]

    if "SHOW_DOCKER_PRERELEASES" not in os.environ:
        tag_regex = re.compile(r"^v([0-9.]+)$")
        tags = [t for t in tags if tag_regex.match(t) is not None]

    print("* Which version do you want to install?")
    print(" 0: Local copy (Default)")
    for index, tag in enumerate(tags):
        print(f" {index + 1}: {tag}")
    version_index = input_check(lambda value: check_version(value, tags), default_value=0)
    if version_index == 0:
        version = ""
    else:
        version = ":" + tags[version_index - 1]

    if version == ":latest":
        must_pull = True
    elif not check_command(f"docker image inspect {docker_repository}pmodwrc/buvic{version} >/dev/null 2>&1 || exit 1"):
        print(f"* Docker image {docker_repository}pmodwrc/buvic{version} does not exist locally")
        must_pull = True
    else:
        must_pull = False

    if must_pull:
        print("* Pulling docker image")
        print(Colors.LIGHTGRAY, end="", flush=True)
        result = call(["docker", "pull", f"{docker_repository}pmodwrc/buvic{version}"])
        print(Colors.ENDC, end="", flush=True)
        if result != 0:
            p("ERROR: An error occurred while pulling image!", Colors.ERROR)
            print("Exiting")
            sys.exit(1)

    print()

    if check_command(f'docker ps -a | grep -q " {container_name}$"'):
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

    if not check_command(f"docker volume inspect buvic-settings >/dev/null 2>&1 || exit 1"):
        print("* Creating volume for settings")
        print(Colors.LIGHTGRAY, end="", flush=True)
        result = run("docker volume create --name buvic-settings", shell=True)
        print(Colors.ENDC, end="", flush=True)
        if result.returncode != 0:
            p("ERROR: An error occurred while creating the buvic settings volume!", Colors.ERROR)
            print("Exiting")
            sys.exit(1)
        print()

    print("* Starting server")
    docker_command = [
        "docker",
        "run",
        "--init",
        "-d",
        f"-p {port}:4444",
        f"-v {instr_path}:/instr",
        f"-v {uvdata_path}:/uvdata",
        f"-v {output_path}:/out",
        "-v buvic-settings:/settings",
    ]

    if user is not None:
        docker_command.extend(["--user", f"{user}"])

    if persist:
        docker_command.append("--restart always")

    if darksky_token is not None:
        docker_command.extend([f"-e DARKSKY_TOKEN={darksky_token}"])

    docker_command.extend(["-e PORT=4444", f"--name {container_name}", f"{docker_repository}pmodwrc/buvic{version}"])
    print(" ".join(docker_command))
    print(Colors.LIGHTGRAY, end="", flush=True)
    result = run(" ".join(docker_command), shell=True)
    print(Colors.ENDC, end="", flush=True)
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

    save_config(port, instr_path, uvdata_path, output_path, user, container_name, persist, darksky_token)


try:
    run_installer()
except KeyboardInterrupt:
    print(Colors.ENDC)
