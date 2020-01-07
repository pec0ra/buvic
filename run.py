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
import logging
import os

from remi import start

from buvic.app import BUVIC
from buvic.const import TMP_FILE_DIR, OUTPUT_DIR
from buvic.logutils import init_logging

if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

init_logging(logging.INFO)

# starts the web server
start(BUVIC, multiple_instance=True, title="BUVIC | Brewer UV Irradiance Calculator")
