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

import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import date
from logging import getLogger
from typing import List
from urllib.error import HTTPError

from numpy import interp

LOG = getLogger(__name__)


class CalibrationProvider:

    def get_calibration_data(self) -> Calibration:
        raise NotImplementedError("'get_calibration_data' must be implemented in a descendent class")


class EubrewnetCalibrationProvider(CalibrationProvider):

    def __init__(self, brewer_id: str, d: date):
        self._url_string = f"http://rbcce.aemet.es/eubrewnet/getdataold/getUVR?brewerid={brewer_id}&date={d.isoformat()}"

    def get_calibration_data(self) -> Calibration:

        LOG.info("Retrieving calibration data from %s", self._url_string)
        try:
            with urllib.request.urlopen(self._url_string) as url:
                data = json.loads(url.read().decode())
        except HTTPError as e:
            raise Exception(f"Error while trying to access eubrewnet. {e}") from e
        wavelengths = [value / 10 for value in data[1]]
        values = data[2]

        return Calibration(
            wavelengths,
            values
        )


class UVRFileCalibrationProvider(CalibrationProvider):
    _file_name: str

    def __init__(self, file_name: str):
        self._file_name = file_name

    def get_calibration_data(self) -> Calibration:
        """
        Parse a given calibration file into a `Calibration` object.
        :return: the `Calibration` object
        """

        LOG.debug("Parsing file: %s", self._file_name)

        with open(self._file_name) as file:
            wavelengths = []
            values = []
            for line in file:
                # Each line consists of two values separated by spaces
                line_values = re.split(r"\s+", line.strip())
                if len(line_values) != 2:
                    raise CalibrationFileParsingError("Failure to read calibration file line correctly.\nLine: " + line)
                wavelengths.append(float(line_values[0]) / 10)
                values.append(float(line_values[1]))

            LOG.debug("Finished parsing file: %s", self._file_name)

            return Calibration(
                wavelengths,
                values
            )


@dataclass
class Calibration:
    wavelengths: List[float]
    values: List[float]

    def interpolated_values(self, wavelengths: List[float]) -> List[float]:
        return interp(wavelengths, self.wavelengths, self.values)


class CalibrationFileParsingError(ValueError):
    pass
