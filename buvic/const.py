import os
from os import path
from subprocess import run, PIPE

TMP_FILE_DIR = "tmp/"
OUTPUT_DIR = "out/"
DATA_DIR = "data/"
ASSETS_DIR = "assets/"

UV_FILES_SUBDIR = "uvdata/"
B_FILES_SUBDIR = "uvdata/"
CALIBRATION_FILES_SUBDIR = "instr/"
ARF_FILES_SUBDIR = "instr/"
PARAMETER_FILES_SUBDIR = "instr/"

APP_VERSION = "test-version"
if path.exists("version"):
    with open("version") as version_file:
        APP_VERSION = version_file.readline().strip()
else:
    result = run("git describe --abbrev=0", stdout=PIPE, shell=True)
    if result.returncode == 0:
        APP_VERSION = result.stdout.decode().strip() + "-dirty"

if "DARKSKY_TOKEN" not in os.environ:
    DARKSKY_TOKEN = None
else:
    DARKSKY_TOKEN = os.environ['DARKSKY_TOKEN']
