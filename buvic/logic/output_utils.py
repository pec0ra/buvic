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
from os import path, makedirs
from pathlib import Path
from threading import Lock

from buvic.logic.result import Result

lock = Lock()


def create_csv(saving_dir: str, result: Result) -> str:
    file_name = result.get_name()

    full_path = Path(path.join(saving_dir, file_name))

    with lock:
        if not path.exists(full_path.parent):
            makedirs(full_path.parent)

    with open(full_path, "w") as csv_file:
        result.to_qasume(csv_file)
    return file_name
