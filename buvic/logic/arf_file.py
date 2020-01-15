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
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from typing import List

from .warnings import warn

LOG = getLogger(__name__)


class ARFProvider:
    def get_arf(self) -> ARF:
        """
        Get the arf
        :return: the arf
        """
        raise NotImplementedError("Method must be implemented in subclass")


class FileARFProvider(ARFProvider):
    _file_name: str
    _arf_column: int

    def __init__(self, file_name: str, arf_column: int):
        self._file_name = file_name
        self._arf_column = arf_column

    def get_arf(self) -> ARF:
        LOG.debug("Parsing file: %s", self._file_name)

        with open(self._file_name) as file:
            try:
                szas = []
                values: List[float] = []
                for line in file:
                    # Skip header
                    if line.strip().startswith("%"):
                        continue
                    # Each line consists of at least five values separated by spaces
                    line_values = re.split(r"\s+", line.strip())
                    sza = float(line_values[0])
                    if sza < 0 or sza > 90:
                        raise ValueError(f"Invalid value found in the first column. Sza must be between 0 and 90. Found {sza}")
                    szas.append(sza)

                    if len(line_values) <= self._arf_column:
                        if len(values) == 0:
                            warn(
                                f"Could not read column {self._arf_column} from arf file, file has only {len(line_values)} columns. Used last column"
                                f" instead."
                            )
                        values.append(float(line_values[-1]))
                    else:
                        values.append(float(line_values[self._arf_column]))
                szas.append(90)
                values.append(0)

                LOG.debug("Finished parsing file: %s", self._file_name)

                return ARF(szas, values)
            except Exception as e:
                raise ARFFileParsingError(f"An error occurred while parsing the arf file: {e}") from e


@dataclass
class ARF:
    szas: List[float]
    values: List[float]


class Direction(Enum):
    NORTH = 1
    WEST = 2
    SOUTH = 3
    EAST = 4


class ARFFileParsingError(ValueError):
    pass
