from __future__ import annotations

import re
from collections import namedtuple
from dataclasses import dataclass
from logging import getLogger
from os import path
from typing import List

from scipy.interpolate import interp1d

LOG = getLogger(__name__)


def read_parameter_file(file_name: str or None) -> Parameters:
    """
    Parse a given B file to read ozone values into a `Ozone` object.
    :param file_name: the name of the file to parse
    :return: the ozone values
    """

    if file_name is None or not path.exists(file_name):
        LOG.info("Parameter File not found. Using default parameter values")
        return Parameters([], [], [])

    LOG.debug("Parsing file: %s", file_name)

    with open(file_name) as file:
        try:

            prev_albedo = None
            prev_aerosol = None
            days = []
            albedos = []
            aerosols = []
            for raw_line in file:
                # Each line consists of 4 values separated by one space
                line_values = re.split("\s", raw_line)
                days.append(int(line_values[0]))

                new_albedo = line_values[1]
                if new_albedo != "":
                    albedos.append(float(new_albedo))
                    prev_albedo = float(new_albedo)
                else:
                    if prev_albedo is None:
                        raise ValueError("The albedo must be defined in the first line of the file")
                    albedos.append(prev_albedo)

                new_aerosol_alpha = line_values[2]
                new_aerosol_beta = line_values[3]
                if new_aerosol_alpha != "" and new_aerosol_beta != "":
                    new_aerosol = Angstrom(float(new_aerosol_alpha), float(new_aerosol_beta))
                    aerosols.append(new_aerosol)
                    prev_aerosol = new_aerosol
                else:
                    if prev_aerosol is None:
                        raise ValueError("The aerosol must be defined in the first line of the file")
                    aerosols.append(prev_aerosol)

            LOG.debug("Finished parsing file: %s", file_name)

            return Parameters(
                days,
                albedos,
                aerosols
            )
        except Exception as e:
            raise ParameterFileParsingError(str(e))


@dataclass
class Parameters:
    days: List[int]
    albedos: List[float]
    aerosols: List[Angstrom]

    def interpolated_albedo(self, day: int, default_value: float) -> float:
        if len(self.albedos) == 0:
            LOG.debug("Parameter object has no albedo value. Using default")
            return default_value
        interpolator = interp1d(self.days, self.albedos, kind='previous', fill_value='extrapolate')
        interpolator1 = interpolator(day)
        return interpolator1

    def interpolated_aerosol(self, day: int, default_value: Angstrom) -> Angstrom:
        if len(self.albedos) == 0:
            LOG.debug("Parameter object has no aerosol value. Using default")
            return default_value
        alpha_interpolator = interp1d(self.days, [a.alpha for a in self.aerosols], kind='previous', fill_value='extrapolate')
        beta_interpolator = interp1d(self.days, [a.beta for a in self.aerosols], kind='previous', fill_value='extrapolate')
        return Angstrom(alpha_interpolator(day), beta_interpolator(day))


Angstrom = namedtuple('Angstrom', ['alpha', 'beta'])


class ParameterFileParsingError(ValueError):
    pass
