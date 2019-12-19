from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from logging import getLogger
from os import path
from typing import List, Optional
from warnings import warn

from scipy.interpolate import interp1d

from buvic.logic.file import File

LOG = getLogger(__name__)


def read_parameter_file(file: Optional[File]) -> Parameters:
    """
    Parse a given B file to read ozone values into a `Ozone` object.
    :param file: the file to parse
    :return: the ozone values
    """

    if file is None or not path.exists(file.full_path):
        LOG.warning("Parameter File not found. Using default parameter values")
        warn(f"Parameter File not found. Using default parameter values")
        return Parameters([], [], [], [])

    LOG.debug("Parsing file: %s", file.file_name)

    with open(file.full_path) as f:
        try:

            prev_albedo = None
            prev_aerosol = None
            days = []
            albedos = []
            aerosols = []
            cloud_covers: List[Optional[float]] = []
            for raw_line in f:
                # Each line consists of 5 values separated by one semicolon
                line_values = raw_line.strip().split(";")

                if len(line_values) != 5:
                    raise ValueError("Each line of the parameter file must contain 5 values")

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

                cloud_cover = line_values[4]
                if cloud_cover != "":
                    cloud_covers.append(float(cloud_cover))
                else:
                    cloud_covers.append(None)

            LOG.debug("Finished parsing file: %s", file.file_name)

            return Parameters(
                days,
                albedos,
                aerosols,
                cloud_covers
            )
        except Exception as e:
            raise ParameterFileParsingError("An error occurred while parsing the parameter File") from e


@dataclass
class Parameters:
    days: List[int]
    albedos: List[float]
    aerosols: List[Angstrom]
    cloud_covers: List[Optional[float]]

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

    def cloud_cover(self, day: int) -> Optional[float]:
        if day not in self.days:
            return None

        index = self.days.index(day)
        return self.cloud_covers[index]


Angstrom = namedtuple('Angstrom', ['alpha', 'beta'])


class ParameterFileParsingError(ValueError):
    pass
