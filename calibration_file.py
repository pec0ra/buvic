from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from numpy import interp


def read_calibration_file(file_name: str) -> Calibration:
    """
    Parse a given calibration file into a `Calibration` object.
    :param file_name: the name of the file to parse
    :return: the `Calibration` object
    """

    with open(file_name) as file:
        wavelengths = []
        values = []
        for line in file:
            # Each line consists of two values separated by spaces
            line_values = re.split("\s+", line.strip())
            if len(line_values) != 2:
                raise CalibrationFileParsingError("Failure to read calibration file line correctly.\nLine: " + line)
            wavelengths.append(float(line_values[0]) / 10)
            values.append(float(line_values[1]))

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
