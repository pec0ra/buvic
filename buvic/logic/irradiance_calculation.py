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

import warnings
from logging import getLogger
from typing import List

from numpy import multiply, divide, sin, add, pi, mean, exp, maximum, linspace, trapz, cos, isnan, ones, arcsin
from scipy.interpolate import UnivariateSpline

from buvic.logic.brewer_infos import StraylightCorrection, correct_straylight
from buvic.logic.calibration_file import Calibration
from buvic.logic.ozone import Ozone
from .arf_file import ARF
from .calculation_input import CalculationInput, CosCorrection
from .libradtran import Libradtran, LibradtranInput, LibradtranResult
from .result import Result, Spectrum
from .utils import minutes_to_time, date_to_days
from .uv_file import UVFileEntry

LOG = getLogger(__name__)


class IrradianceCalculation:
    """
    A utility to calculate and correct irradiance.

    The irradiance is calculated from a UV file containing raw measurement values along with
    a calibration file and an arf file to apply the required corrections.
    """

    _calculation_input: CalculationInput

    def __init__(self, calculation_input: CalculationInput):
        """
        Create an instance from a given CalculationInput

        :param calculation_input: the object containing the file names and data required for the calculations
        """
        self._calculation_input = calculation_input

    def calculate(self, index: int) -> Result:
        """
        Do the calculation for a file entry (section)
        :param index: the index of the section
        :return: the result of the calculation
        """

        try:
            LOG.debug("Starting calculation for section %d of '%s'", index, self._calculation_input.uv_file_name)

            uv_file_entry: UVFileEntry = self._calculation_input.uv_file_entries[index]

            libradtran_result = self._execute_libradtran(uv_file_entry)
            calibrated_spectrum = self._to_calibrated_spectrum(uv_file_entry, self._calculation_input.calibration)

            # Apply temperature correction
            c = self._calculation_input.settings.temperature_correction_factor
            tref = self._calculation_input.settings.temperature_correction_ref
            temperature_correction = 1 + c * (uv_file_entry.header.temperature - tref)
            LOG.debug(f"Temperature is {uv_file_entry.header.temperature:.2f}°C and corresponding correction is {temperature_correction}")
            calibrated_spectrum = multiply(calibrated_spectrum, temperature_correction)

            # Find cos correction and apply it
            minutes = uv_file_entry.raw_values[0].time
            cos_cor_to_apply = self._calculation_input.cos_correction_to_apply(minutes)
            if cos_cor_to_apply == CosCorrection.DIFFUSE:
                LOG.debug("Using diffuse correction for time %s", minutes_to_time(minutes).isoformat())
                cos_correction = divide(
                    [1] * len(libradtran_result.columns["sza"]), self._calculate_coscor_diff(self._calculation_input.arf)
                )
            elif cos_cor_to_apply == CosCorrection.CLEAR_SKY:
                LOG.debug("Using clear sky correction for time %s", minutes_to_time(minutes).isoformat())
                cos_correction = self._cos_correction(self._calculation_input.arf, libradtran_result)
            else:
                LOG.debug("Using no cos correction")
                cos_correction = ones(len(libradtran_result.columns["sza"]))

            # Set nan to 1
            cos_correction_no_nan = cos_correction.copy()
            cos_correction_no_nan[isnan(cos_correction_no_nan)] = 1
            cos_corrected_spectrum = multiply(calibrated_spectrum, cos_correction_no_nan)

            spectrum = Spectrum(
                uv_file_entry.wavelengths,
                uv_file_entry.times,
                uv_file_entry.events,
                calibrated_spectrum,
                cos_corrected_spectrum,
                cos_correction,
            )

            sza = self._get_sza(libradtran_result)

            air_mass = self._calculate_air_mass(sza)

            LOG.debug("Finished calculation for section %d of %s", index, self._calculation_input.uv_file_name)

            return Result(index, self._calculation_input, sza, air_mass, temperature_correction, spectrum)

        except Exception as e:
            LOG.error("An error occurred while doing the calculation", exc_info=True)
            raise e

    def _to_calibrated_spectrum(self, uv_file_entry: UVFileEntry, calibration: Calibration) -> List[float]:
        """
        Convert raw (count) measures to a calibrated spectrum
        :param uv_file_entry: the entry from which to get raw values
        :param calibration: the calibration data
        :return: the calibrated spectrum
        """

        uv_file_header = uv_file_entry.header

        # Remove dark signal
        raw_values = [v.events for v in uv_file_entry.raw_values]
        corrected_values = [v - uv_file_header.dark for v in raw_values]

        straylight_correction = correct_straylight(self._calculation_input.brewer_type)
        if straylight_correction == StraylightCorrection.UNDEFINED:
            straylight_correction = self._calculation_input.settings.default_straylight_correction
        if straylight_correction == StraylightCorrection.APPLIED:
            LOG.debug("Applying straylight correction")
            # Remove straylight
            below_292 = list(filter(lambda x: x.wavelength < 292, uv_file_entry.raw_values))
            if len(below_292) > 0:
                correction = mean([v.events for v in below_292])
                corrected_values = [v - correction for v in corrected_values]

        # Convert to photon/sec
        photon_rate = [v * 4 / (uv_file_header.cycles * uv_file_header.integration_time) for v in corrected_values]

        # Correct for linearity
        photon_rate0 = photon_rate
        for i in range(25):
            photon_rate = multiply(photon_rate0, exp(multiply(photon_rate, uv_file_header.dead_time)))

        # Set negative values to 0
        photon_rate = maximum(0, photon_rate)

        # Apply sensitivity
        values = calibration.interpolated_values(uv_file_entry.wavelengths)
        photon_rate = divide(photon_rate, values)

        return photon_rate

    @staticmethod
    def _calculate_coscor_diff(arf: ARF) -> float:
        """
        Integrates ARF(θ)sin(θ) (see inline comments)
        :param arf: the ARF to get the values from
        :return: the result of the integration
        """

        # Interpolate ARF over smaller steps to get a better precision
        angles = multiply(pi / 180, arf.szas)
        spline = UnivariateSpline(angles, arf.values)
        theta = linspace(0, pi / 2, 160)

        # Integrate `1/π ∬arf(θ) sin(θ) dθdφ` with θ from 0 to π/2 and φ from 0 to 2π
        # This is equivalent to integrating `2 ∫arf(θ) sin(θ) dθ` with θ from 0 to π/2
        return 2 * trapz(spline(theta) * sin(theta), theta)

    def _execute_libradtran(self, uv_file_entry: UVFileEntry) -> LibradtranResult:
        """
        Call LibRadtran with parameters extracted from a given UVFileEntry
        :param uv_file_entry: the entry to get LibRadtran's parameters from
        :return: LibRadtran's result
        """
        uv_file_header = uv_file_entry.header

        # Calculate time from the UV file's time. In those files, the time is specified as "Minutes since start of day"
        minutes = uv_file_entry.raw_values[0].time
        time = minutes_to_time(minutes)

        libradtran = Libradtran()
        libradtran.add_input(LibradtranInput.WAVELENGTH, [uv_file_entry.wavelengths[0], uv_file_entry.wavelengths[-1]])
        libradtran.add_input(LibradtranInput.LATITUDE, ["N", uv_file_header.position.latitude])

        # Negative longitudes are East and Positive ones are West
        hemisphere = "E" if uv_file_header.position.longitude < 0 else "W"
        libradtran.add_input(LibradtranInput.LONGITUDE, [hemisphere, abs(uv_file_header.position.longitude)])

        # We set LibRadtran to interpolate to exactly the values we have from the UV file
        step = uv_file_entry.wavelengths[1] - uv_file_entry.wavelengths[0]
        libradtran.add_input(LibradtranInput.SPLINE, [uv_file_entry.wavelengths[0], uv_file_entry.wavelengths[-1], step])

        ozone: Ozone = self._calculation_input.ozone
        libradtran.add_input(LibradtranInput.OZONE, [ozone.interpolated_ozone(minutes, self._calculation_input.settings.default_ozone)])

        libradtran.add_input(
            LibradtranInput.TIME,
            [uv_file_header.date.year, uv_file_header.date.month, uv_file_header.date.day, time.hour, time.minute, time.second],
        )

        days = date_to_days(uv_file_header.date)
        libradtran.add_input(LibradtranInput.PRESSURE, [uv_file_header.pressure])
        libradtran.add_input(
            LibradtranInput.ALBEDO,
            [self._calculation_input.parameters.interpolated_albedo(days, self._calculation_input.settings.default_albedo)],
        )
        aerosol = self._calculation_input.parameters.interpolated_aerosol(days, self._calculation_input.settings.default_aerosol)
        libradtran.add_input(LibradtranInput.AEROSOL, [aerosol.alpha, aerosol.beta])

        libradtran.add_outputs(["sza", "edir", "edn", "eglo"])
        result = libradtran.calculate()
        return result

    def _cos_correction(self, arf: ARF, libradtran_result: LibradtranResult) -> List[float]:
        """
        Calculate the cosine correction factor `c` from a LibRadtran result and ARF values
        :param arf: the ARF object containing the ARF values
        :param libradtran_result: the LibRadtran result
        :return: the cos correction factor
        """

        fdiff = libradtran_result.columns["edn"]
        fdir = libradtran_result.columns["edir"]
        fglo = libradtran_result.columns["eglo"]
        theta = libradtran_result.columns["sza"][0] * pi / 180

        # We ignore division by zero warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Fdiff / Fglo
            fdiff_fglo = divide(fdiff, fglo)

        # Coscor
        coscor_diff = self._calculate_coscor_diff(arf)

        # coscor * Fdiff/Fglo
        c_inverse_left = multiply(coscor_diff, fdiff_fglo)

        # Interpolate ARF to get ARF(θ)
        angles = multiply(pi / 180, arf.szas)
        arf_spline = UnivariateSpline(angles, arf.values)

        # We ignore division by zero warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Fdir / Fglo
            fdir_fglo = divide(fdir, fglo)

        # Fdir/Fglo * ARF(θ)/cos(θ)
        c_inverse_right = multiply(fdir_fglo, divide(arf_spline(theta), cos(theta)))

        c_inverse = add(c_inverse_left, c_inverse_right)

        # return c
        return divide(1, c_inverse)

    def _cos_correction_2(self, arf: ARF, libradtran_result: LibradtranResult) -> List[float]:
        """
        Calculate the cosine correction factor `c` from a LibRadtran result and ARF values

        This is an alternative method but should return the same result as `_cos_correction()`

        :param arf: the ARF object containing the ARF values
        :param libradtran_result: the LibRadtran result
        :return: the cos correction factor
        """

        fdiff = libradtran_result.columns["edn"]
        fdir = libradtran_result.columns["edir"]
        theta = self._get_sza(libradtran_result) * pi / 180

        # Fdir / Fdiff
        fdir_fdiff = divide(fdir, fdiff)

        # Fdir / Fdiff + 1
        c_upper = add(fdir_fdiff, 1)

        # Interpolate ARF to get ARF(θ)
        angles = multiply(pi / 180, arf.szas)
        arf_spline = UnivariateSpline(angles, arf.values)

        # Fdir' / Fdir
        fdir_p_fdir = divide(arf_spline(theta), cos(theta))

        # Fdiff' / Fdiff
        fdiff_p_fdiff = self._calculate_coscor_diff(arf)

        c_lower = add(multiply(fdir_p_fdir, fdir_fdiff), fdiff_p_fdiff)

        c = divide(c_upper, c_lower)

        return c

    @staticmethod
    def _get_sza(libradtran_result: LibradtranResult) -> float:
        """
        Extracts the sza from a given libradtran result
        :param libradtran_result: the libradtran result
        :return: the sza
        """
        return libradtran_result.columns["sza"][0]

    @staticmethod
    def _calculate_air_mass(sza: float):
        """
        Calculate the air mass for a given sza (in degree)
        :param sza: the solar zenith angle
        :return: the air mass
        """
        earth_radius = 6_370_000.0  # in meters
        h = 22_000.0  # in meters
        sza_radian = sza * pi / 180

        sin_theta = earth_radius * sin(pi - sza_radian) / (earth_radius + h)
        theta = arcsin(sin_theta)

        return 1 / cos(theta)
