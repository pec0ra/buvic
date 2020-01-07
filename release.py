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
import os
import sys
from subprocess import PIPE, run

FNULL = open(os.devnull, 'w')


def run_command(command, show_std_err=False, pipe_stdout=True):
    stderr = None if show_std_err else FNULL
    stdout = PIPE if pipe_stdout else None
    result = run(command, stdout=stdout, stderr=stderr, shell=True)
    return result


def make_release(new_version):
    print(f"* Will create a release for version {new_version}")
    print()

    print("* Checking branch state")
    res = run_command("git status --porcelain", show_std_err=True)
    if res.returncode != 0:
        print("An unexpected error occurred.")
        exit(1)
    if len(res.stdout) != 0:
        print("Branch is not clean. Please commit your changes before making a release")
        exit(1)

    res = run_command("git describe --abbrev=0", show_std_err=True)
    last_version = res.stdout.decode().strip()

    if last_version == new_version:
        print("Version number has not changed since last release. Please change it in the file 'version' before running this script.")
        exit(1)

    print()
    print("* Creating git tag")
    res = run_command(f"git tag {new_version} -a -m \"UV Server {new_version}\"", True)
    if res.returncode != 0:
        print("An error occurred while creating the tag")
        exit(1)
    res = run_command(f"git push --tags --porcelain", True)
    if res.returncode != 0:
        print("An error occurred while creating the tag")
        exit(1)


try:
    if len(sys.argv) != 2:
        print("Usage: ./release <version>")

    make_release(sys.argv[1])
except KeyboardInterrupt:
    exit(1)
