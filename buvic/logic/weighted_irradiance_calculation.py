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
from os import path
from typing import List, Dict, Optional

import numpy
from numpy import multiply, trapz
from scipy.interpolate import UnivariateSpline, RectBivariateSpline

from buvic.logic.result import Result
from buvic.logic.weighted_irradiance import WeightedIrradiance, WeightedIrradianceType

LOG = getLogger(__name__)


class VitD3Spline:
    """
    A wrapper for the vitamin d3's `UnivariateSpline`.

    Interpolated values can be retrieved with the method `get_value(wavelength)`.

    This class uses a cache to improve the performance by interpolating each value only once.
    """

    VIT_D3_WAVELENGTH_START = 252
    VIT_D3_WAVELENGTH_END = 330
    VIT_D3_VALUES = numpy.genfromtxt(path.join("buvic/logic/data", "vit_d3_values"))
    VIT_D3_WAVELENGTHS = range(VIT_D3_WAVELENGTH_START, VIT_D3_WAVELENGTH_END + 1)

    _spline: UnivariateSpline
    _cache: Dict[float, float]

    def __init__(self) -> None:
        self._spline = UnivariateSpline(self.VIT_D3_WAVELENGTHS, self.VIT_D3_VALUES)
        self._cache = {}

    def get_value(self, wavelength: float) -> float:
        """
        Get an interpolated value at a given wavelength
        :param wavelength: the wavelength to get the value for
        :return: the interpolated value
        """
        if wavelength < self.get_min_wavelength() or wavelength > self.get_max_wavelength():
            raise ValueError(f"The wavelength must be within the bounds {self.get_min_wavelength()} - {self.get_max_wavelength()}")

        if wavelength not in self._cache:
            self._cache[wavelength] = self._spline(wavelength)
        return self._cache[wavelength]

    def get_min_wavelength(self) -> float:
        """
        The minimum wavelength for which the value can be evaluated
        :return: the minimum wavelength
        """
        return self.VIT_D3_WAVELENGTH_START

    def get_max_wavelength(self) -> float:
        """
        The maximum wavelength for which the value can be evaluated
        :return: the maximum wavelength
        """
        return self.VIT_D3_WAVELENGTH_END


class CorrectionSpline:
    """
    A wrapper for the correction spline.

    This class makes 2 dimensional interpolation to retrieve the correction value for given sza and ozone level.
    """

    OZONE_LEVELS = range(200, 520, 20)  # From 0 to 500 in increments of 20
    SZAS = range(0, 95, 5)  # From 0 to 90 in increments of 5

    _spline: RectBivariateSpline

    def __init__(self, file_name: str) -> None:

        # Load the 2D array from the given file
        correction_values = numpy.genfromtxt(path.join("buvic/logic/data", file_name))

        # Initialize the spline
        self._spline = RectBivariateSpline(self.SZAS, self.OZONE_LEVELS, correction_values)

    def get_value(self, sza: float, ozone: float) -> float:
        """
        Get the interpolated correction value for given sza and ozone
        :param sza: the sza to get the value for
        :param ozone: the ozone level to get the value for
        :return: the interpolated value
        """
        # We only interpolate within the sza and ozone bounds
        if sza > 90:
            LOG.debug(f"Value '{sza}' is greater than 90. Interpolation will use 90 instead")
            sza = 90
        elif sza < 0:
            LOG.warning(f"Value '{sza}' is smaller than 0. Interpolation will use 0 instead")
            sza = 0

        if ozone > 500:
            LOG.info(f"Value '{ozone}' is greater than 500. Interpolation will use 500 instead")
            ozone = 500
        elif ozone < 200:
            LOG.info(f"Value '{ozone}' is smaller than 200. Interpolation will use 200 instead")
            ozone = 200

        spline_result = self._spline(sza, ozone)
        return spline_result[0][0]


class WeightedIrradianceCalculation:
    """
    A utility to calculate weighted irradiance.

    The weighted irradiance is calculated for every available time of the day from a spectrum λ(w) and a weight function f(w) as their
    multiplication λ(w) * f(w). These weighted values are then integrated over the wavelengths ∫ λ(w) f(w) dw
    """

    vit_d3_spline: VitD3Spline = VitD3Spline()

    max_325_correction_spline = CorrectionSpline("max_325")
    max_363_correction_spline = CorrectionSpline("max_363")

    _results: List[Result]

    def __init__(self, results: List[Result], weighted_irradiance_type: Optional[WeightedIrradianceType] = None):
        self._results = results
        if weighted_irradiance_type is not None:
            self._weighted_irradiance_type = weighted_irradiance_type
        else:
            self._weighted_irradiance_type = self._results[0].calculation_input.settings.weighted_irradiance_type

    def calculate(self) -> WeightedIrradiance:
        """
        Calculate the weighted irradiance for the results.

        The result is in mW/m^2

        :return: the weighted irradiance
        """

        LOG.debug(
            f"Calculating weighted irradiance for type '{self._weighted_irradiance_type.value}' for date "
            f"{self._results[0].calculation_input.date.isoformat()}"
        )

        times = []
        values = []
        for result in self._results:
            t = result.uv_file_entry.times[0] / 60
            value = self._calculate_value(result)

            times.append(t)
            values.append(value)

        return WeightedIrradiance(self._weighted_irradiance_type, times, values)

    @staticmethod
    def calculate_daily_dosis(weighted_irradiance: WeightedIrradiance) -> float:
        """
        Integrate weighted irradiance over a whole day in Jul/m^2

        :param weighted_irradiance: the irradiance to integrate
        :return: the integrated irradiance
        """
        # We convert the time in hours to a time in seconds
        times_sec = [t * 3600 for t in weighted_irradiance.times]
        # We convert milliwatts to watts
        values_watt = [v / 1000 for v in weighted_irradiance.values]

        return trapz(values_watt, times_sec)

    def _calculate_value(self, result: Result) -> float:
        """
        Calculate the weighted irradiance ∫ λ(w) f(w) dw for a given spectrum and a given weight function type
        :param result: the result containing the spectrum
        :return: the weighted irradiance
        """

        # get the weight function
        f = self._get_function(result.uv_file_entry.wavelengths)

        # multiply λ(w) * f(w)
        combi = multiply(result.spectrum.cos_corrected_spectrum, f)

        # integrate over the wavelengths ∫ λ(w) f(w) dw
        v = self._integrate(result.spectrum.wavelengths, combi)

        # Add correction for spectra that don't cover all wavelengths
        correction = self._get_correction(result)
        LOG.debug(f"Integral correction: {correction}")
        return v + correction

    def _get_function(self, wavelengths: List[float]) -> List[float]:
        """
        Get a given type of weight function
        :param wavelengths: the steps for which to evaluate the weight function
        :return: the values of the evaluation of the weight function for each wavelength
        """
        if self._weighted_irradiance_type == WeightedIrradianceType.ERYTHEMAL:
            ret: List[float] = []
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

        if self._weighted_irradiance_type == WeightedIrradianceType.VITAMIN_D3:
            ret = []
            for w in wavelengths:
                if w < self.vit_d3_spline.get_min_wavelength() or w > self.vit_d3_spline.get_max_wavelength():
                    ret.append(0)
                else:
                    ret.append(self.vit_d3_spline.get_value(w))
            return ret

        if self._weighted_irradiance_type == WeightedIrradianceType.UV:
            ret = []
            for w in wavelengths:
                if 280 <= w <= 400:
                    ret.append(1)
                else:
                    ret.append(0)
            return ret

        if self._weighted_irradiance_type == WeightedIrradianceType.UVA:
            ret = []
            for w in wavelengths:
                if 280 <= w <= 315:
                    ret.append(1)
                else:
                    ret.append(0)
            return ret

        if self._weighted_irradiance_type == WeightedIrradianceType.UVB:
            ret = []
            for w in wavelengths:
                if 315 <= w <= 400:
                    ret.append(1)
                else:
                    ret.append(0)
            return ret
        raise ValueError(f"Invalid weighted irradiance type provided: '{self._weighted_irradiance_type}'")

    @staticmethod
    def _integrate(wavelengths: List[float], values: List[float]) -> float:
        return trapz(values, wavelengths)

    def _get_correction(self, result: Result) -> float:
        max_wl = result.spectrum.wavelengths[-1]
        minutes = result.uv_file_entry.raw_values[0].time
        ozone = result.calculation_input.ozone.interpolated_ozone(minutes, result.calculation_input.settings.default_ozone)

        if max_wl <= 325:
            # For spectra with values up to 325nm, we don't use the last value of the spectrum but the value measured for 324nm.
            # The reason for this is that the value measured at 324nm is less affected by ozone.
            index_325 = result.spectrum.wavelengths.index(324.0)
            return result.spectrum.cos_corrected_spectrum[index_325] * self.max_325_correction_spline.get_value(result.sza, ozone)
        elif max_wl <= 363:
            # For spectra with values up to 363nm, we use the last value of the spectrum
            return result.spectrum.cos_corrected_spectrum[-1] * self.max_363_correction_spline.get_value(result.sza, ozone)
        else:
            return 0
