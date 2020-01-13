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
    DARKSKY_TOKEN = os.environ["DARKSKY_TOKEN"]
