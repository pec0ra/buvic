#!/usr/bin/python3
import sys

from script_utils import Colors, p, run_command


def make_release(new_version):

    print(f"* Will create a release for version {new_version}")
    print()

    print("* Checking branch state")
    res = run_command("git status --porcelain", show_std_err=True)
    if res.returncode != 0:
        p("An unexpected error occurred.", Colors.ERROR)
        exit(1)
    if len(res.stdout) != 0:
        p("Branch is not clean. Please commit your changes before making a release", Colors.ERROR)
        exit(1)

    res = run_command("git describe --abbrev=0", show_std_err=True)
    last_version = res.stdout.decode().strip()

    if last_version == new_version:
        p("Version number has not changed since last release. Please change it in the file 'version' before running this script.",
          Colors.ERROR)
        exit(1)

    print()
    print("* Creating git tag")
    res = run_command(f"git tag {new_version} -a -m \"UV Server {new_version}\"", True)
    if res.returncode != 0:
        p("An error occurred while creating the tag", Colors.ERROR)
        exit(1)
    res = run_command(f"git push --tags --porcelain", True)
    if res.returncode != 0:
        p("An error occurred while creating the tag", Colors.ERROR)
        exit(1)


try:
    if len(sys.argv) != 2:
        print("Usage: ./release <version>")

    make_release(sys.argv[1])
except KeyboardInterrupt:
    print(Colors.ENDC)
