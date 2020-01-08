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

from logging import getLogger
from typing import List

import numpy
from numpy import multiply, trapz
from scipy.interpolate import UnivariateSpline

from buvic.logic.result import Result
from buvic.logic.weighted_irradiance import WeightedIrradiance, WeightedIrradianceType

LOG = getLogger(__name__)


class WeightedIrradianceCalculation:
    """
    A utility to calculate weighted irradiance.

    The weighted irradiance is calculated for every available time of the day from a spectrum λ(w) and a weight function f(w) as their
    multiplication λ(w) * f(w). These weighted values are then integrated over the wavelengths ∫ λ(w) f(w) dw
    """

    VIT_D3_VALUES = [0.036, 0.039, 0.043, 0.047, 0.051, 0.056, 0.061, 0.066, 0.075, 0.084, 0.093, 0.102, 0.112, 0.122, 0.133, 0.146, 0.160,
                     0.177, 0.195, 0.216, 0.238, 0.263, 0.289, 0.317, 0.346, 0.376, 0.408, 0.440, 0.474, 0.543, 0.583, 0.617, 0.652, 0.689,
                     0.725, 0.763, 0.805, 0.842, 0.878, 0.903, 0.928, 0.952, 0.976, 0.983, 0.990, 0.996, 1, 0.977, 0.951, 0.917, 0.878,
                     0.771, 0.701, 0.634, 0.566, 0.488, 0.395, 0.306, 0.22, 0.156, 0.119, 0.083, 0.049, 0.034, 0.02, 1.41e-2, 9.76e-3,
                     6.52e-3, 4.36e-3, 2.92e-3, 1.95e-3, 1.31e-3, 8.73e-4, 5.84e-4, 3.9e-4, 2.61e-4, 1.75e-4, 1.17e-4, 7.8e-5]
    VIT_D3_WAVELENGTHS = range(252, 331)

    _result: List[Result]

    def __init__(
            self,
            results: List[Result]
    ):
        self._result = results

    def calculate(self) -> WeightedIrradiance:
        """
        Calculate the weighted irradiance for the results

        :return: the weighted irradiance
        """
        weighted_irradiance_type = self._result[0].calculation_input.settings.weighted_irradiance_type
        times = []
        values = []
        for result in self._result:
            time = result.uv_file_entry.times[0] / 60
            value = self._calculate_value(result, weighted_irradiance_type)

            times.append(time)
            values.append(value)

        return WeightedIrradiance(weighted_irradiance_type, times, values)

    @staticmethod
    def calculate_daily_dosis(weighted_irradiance: WeightedIrradiance) -> float:
        """
        Integrate weighted irradiance over a whole day

        :param weighted_irradiance: the irradiance to integrate
        :return: the integrated irradiance
        """
        # We convert the time in hours to a time in seconds
        times_sec = [t * 3600 for t in weighted_irradiance.times]
        # We convert milliwatts to watts
        values_watt = [v / 1000 for v in weighted_irradiance.values]

        return trapz(values_watt, times_sec)

    def _calculate_value(self, result: Result, weighted_irradiance_type: WeightedIrradianceType) -> float:
        """
        Calculate the weighted irradiance ∫ λ(w) f(w) dw for a given spectrum and a given weight function type
        :param result: the result containing the spectrum
        :param weighted_irradiance_type: the type of weight function
        :return: the weighted irradiance
        """
        LOG.debug(f"Calculating weighted irradiance for type '{weighted_irradiance_type.value}'")

        # get the weight function
        f = self._get_function(result.uv_file_entry.wavelengths, weighted_irradiance_type)

        # multiply λ(w) * f(w)
        combi = multiply(result.spectrum.cos_corrected_spectrum, f)

        # integrate over the wavelengths ∫ λ(w) f(w) dw
        return self._integrate(result.spectrum.wavelengths, combi)

    def _get_function(self, wavelengths: List[float], weighted_irradiance_type: WeightedIrradianceType) -> List[float]:
        """
        Get a given type of weight function
        :param wavelengths: the steps for which to evaluate the weight function
        :param weighted_irradiance_type: the type of weight function
        :return: the values of the evaluation of the weight function for each wavelength
        """
        if weighted_irradiance_type == WeightedIrradianceType.ERYTHEMAL:
            ret = []
            for w in wavelengths:
                if w <= 298:
                    ret.append(1)
                elif 298 < w <= 328:
                    ret.append(pow(10, 0.094 * (298 - w)))
                elif 328 < w <= 400:
                    ret.append(pow(10, 0.015 * (140 - w)))
                else:
                    ret.append(0)
            return ret
        if weighted_irradiance_type == WeightedIrradianceType.VITAMIN_D3:
            spline = UnivariateSpline(self.VIT_D3_WAVELENGTHS, self.VIT_D3_VALUES)
            ret = []
            for w in wavelengths:
                if w < numpy.min(self.VIT_D3_WAVELENGTHS) or w > numpy.max(self.VIT_D3_WAVELENGTHS):
                    ret.append(0)
                else:
                    ret.append(spline(w))
            return ret
        if weighted_irradiance_type == WeightedIrradianceType.UV:
            ret = []
            for w in wavelengths:
                if 280 <= w <= 400:
                    ret.append(1)
                else:
                    ret.append(0)
            return ret
        if weighted_irradiance_type == WeightedIrradianceType.UVA:
            ret = []
            for w in wavelengths:
                if 280 <= w <= 315:
                    ret.append(1)
                else:
                    ret.append(0)
            return ret
        if weighted_irradiance_type == WeightedIrradianceType.UVB:
            ret = []
            for w in wavelengths:
                if 315 <= w <= 400:
                    ret.append(1)
                else:
                    ret.append(0)
            return ret

    @staticmethod
    def _integrate(wavelengths: List[float], values: List[float]) -> float:
        return trapz(values, wavelengths)