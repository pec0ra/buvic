from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import List

from scipy.interpolate import interp1d

SUMMARY_LINE_REGEX = re.compile(
    "summary "
    "(?P<hours>\d\d):(?P<minutes>\d\d):(?P<seconds>\d\d) "
    "(?:\S+\s+){6}"
    "ds\s+"
    "(?:\S+\s+){8}"
    "(?P<ozone>\S+)"
)


def read_ozone_from_b_file(file_name: str) -> Ozone:
    """
    Parse a given B file to read ozone values into a `Ozone` object.
    :param file_name: the name of the file to parse
    :return: the ozone values
    """

    with open(file_name, newline='\r\n') as file:
        try:
            times = []
            values = []
            for raw_line in file:
                line = raw_line.replace('\r', ' ').replace('\n', '').strip()
                res = re.match(SUMMARY_LINE_REGEX, line)
                if res is not None:
                    td = timedelta(hours=float(res.group("hours")), minutes=float(res.group("minutes")),
                                   seconds=float(res.group("seconds")))
                    minutes_since_midnight = td.seconds / 60
                    times.append(minutes_since_midnight)
                    values.append(float(res.group("ozone")))

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

    def interpolated_value(self, time: float) -> List[float]:
        interpolator = interp1d(self.times, self.values, kind='nearest', fill_value='extrapolate')
        return interpolator(time)


class BFileParsingError(ValueError):
    pass
