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
from dataclasses import dataclass
from datetime import date, datetime
from datetime import timedelta
from logging import getLogger
from os import path
from typing import Optional, List

import requests
import requests.auth
from scipy.interpolate import interp1d

from buvic.logic.file import File
from .warnings import warn

LOG = getLogger(__name__)


class OzoneProvider:
    def get_ozone_data(self) -> Ozone:
        raise NotImplementedError("'get_ozone_data' must be implemented in a descendent class")

    @staticmethod
    def convert_time(hour: float, minute: float, second: float) -> float:
        td = timedelta(hours=hour, minutes=minute, seconds=second)
        minutes_since_midnight = td.seconds / 60
        return minutes_since_midnight


class EubrewnetOzoneProvider(OzoneProvider):
    def __init__(self, brewer_id: str, d: date):
        self._url_string = f"http://rbcce.aemet.es/eubrewnet/data/get/O3L1_5?brewerid={brewer_id}&date={d.isoformat()}"

    def get_ozone_data(self) -> Ozone:

        LOG.info("Retrieving ozone data from %s", self._url_string)
        try:
            response = requests.get(self._url_string, auth=requests.auth.HTTPBasicAuth("are2019", "arework"))
            data = json.loads(response.text)
            content = data[1:]
            times = []
            values = []
            for line in content:
                dt = datetime.strptime(line[1][:-1], "%Y%m%dT%H%M%S")
                times.append(self.convert_time(dt.hour, dt.minute, dt.second))
                values.append(float(line[9]))
            return Ozone(times, values)
        except Exception as e:
            raise Exception(f"Error while trying to access eubrewnet ({self._url_string}). {e}") from e


class BFileOzoneProvider(OzoneProvider):
    SUMMARY_LINE_REGEX = re.compile(
        r"summary "
        r"(?P<hours>\d\d):(?P<minutes>\d\d):(?P<seconds>\d\d)\s+"
        r"[A-Z]{3}\s+\d\d/\s*\d\d\s+"
        r"\S+\s+"
        r"(?P<air_mass>\S+)\s+"
        r"\S+\s+"
        r"ds\s+"
        r"(?:\S+\s+){8}"
        r"(?P<ozone>\S+)\s+"
        r"(?:\S+\s+){7}"
        r"(?P<ozone_std>\S+)"
    )
    INSTRUMENT_CONSTANTS_LINE_REGEX = re.compile(r"inst\s+" r"(?:\S+\s+){22}" r"(?P<brewer_type>\S+)\s+")

    def __init__(self, file: Optional[File]):
        self._file = file

    def get_ozone_data(self) -> Ozone:
        if self._file is None or not path.exists(self._file.full_path):
            warn(f"Corresponding B file not found. default ozone value is used " f"and straylight correction is applied.")
            return Ozone([], [])

        LOG.debug("Parsing file: %s", self._file.file_name)

        with open(self._file.full_path, newline="\r\n") as f:
            try:
                brewer_type = None
                times = []
                values = []
                for raw_line in f:
                    line = raw_line.replace("\r", " ").replace("\n", "").strip()
                    res = re.match(self.SUMMARY_LINE_REGEX, line)
                    res_constants = re.match(self.INSTRUMENT_CONSTANTS_LINE_REGEX, line)
                    if res is not None:
                        # Ignore measurements where air mass or ozone std is too high
                        if float(res.group("air_mass")) > 3.5 or float(res.group("ozone_std")) > 2.5:
                            continue

                        td = timedelta(
                            hours=float(res.group("hours")), minutes=float(res.group("minutes")), seconds=float(res.group("seconds"))
                        )
                        minutes_since_midnight = td.seconds / 60
                        times.append(minutes_since_midnight)
                        values.append(float(res.group("ozone")))
                    elif res_constants is not None:
                        brewer_type = res_constants.group("brewer_type")

                LOG.debug("Finished parsing file: %s", self._file.file_name)

                if brewer_type is None:
                    raise ValueError(f"No brewer type found in b file {self._file.file_name}")

                return Ozone(times, values)
            except Exception as e:
                raise BFileParsingError("An error occurred while parsing the B File") from e


@dataclass
class Ozone:
    times: List[float]
    values: List[float]

    def interpolated_ozone(self, time: float, default_value: float) -> float:
        if len(self.values) == 0:
            LOG.debug("Ozone object has no value. Using default")
            return default_value
        if len(self.values) == 1:
            LOG.debug("Ozone object has only one value. Using it")
            return self.values[0]
        interpolator = interp1d(self.times, self.values, kind="nearest", fill_value="extrapolate")
        return interpolator(time)


class BFileParsingError(ValueError):
    pass
