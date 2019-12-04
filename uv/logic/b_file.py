from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from logging import getLogger
from typing import List
from os import path

from scipy.interpolate import interp1d

LOG = getLogger(__name__)

SUMMARY_LINE_REGEX = re.compile(
    "summary "
    "(?P<hours>\d\d):(?P<minutes>\d\d):(?P<seconds>\d\d)\s+"
    "[A-Z]{3}\s+\d\d/\s*\d\d\s+"
    "\S+\s+"
    "(?P<air_mass>\S+)\s+"
    "\S+\s+"
    "ds\s+"
    "(?:\S+\s+){8}"
    "(?P<ozone>\S+)\s+"
    "(?:\S+\s+){7}"
    "(?P<ozone_std>\S+)"
)


def read_ozone_from_b_file(file_name: str) -> Ozone:
    """
    Parse a given B file to read ozone values into a `Ozone` object.
    :param file_name: the name of the file to parse
    :return: the ozone values
    """

    if file_name is None or not path.exists(file_name):
        LOG.info("B File not found. Using default ozone value")
        return Ozone([], [])

    LOG.debug("Parsing file: %s", file_name)

    with open(file_name, newline='\r\n') as file:
        try:
            times = []
            values = []
            for raw_line in file:
                line = raw_line.replace('\r', ' ').replace('\n', '').strip()
                res = re.match(SUMMARY_LINE_REGEX, line)
                if res is not None:
                    # Ignore measurements where air mass or ozone std is too high
                    if float(res.group("air_mass")) > 3.5 or float(res.group("ozone_std")) > 2.5:
                        continue

                    td = timedelta(hours=float(res.group("hours")), minutes=float(res.group("minutes")),
                                   seconds=float(res.group("seconds")))
                    minutes_since_midnight = td.seconds / 60
                    times.append(minutes_since_midnight)
                    values.append(float(res.group("ozone")))

            LOG.debug("Finished parsing file: %s", file_name)

            return Ozone(
                times,
                values
            )
        except Exception as e:
            raise BFileParsingError(str(e))


@dataclass
class Ozone:
    times: List[float]
    values: List[float]

    def interpolated_value(self, time: float, default_value: float) -> float:
        if len(self.values) == 0:
            LOG.debug("Ozone object has no value. Using default")
            return default_value
        interpolator = interp1d(self.times, self.values, kind='nearest', fill_value='extrapolate')
        return interpolator(time)


class BFileParsingError(ValueError):
    pass
