from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import List

from numpy import multiply, divide, sin, add, pi, mean, exp, maximum, linspace, trapz, cos
from scipy.interpolate import UnivariateSpline

from arf_file import read_arf_file, Direction, ARF
from calibration_file import read_calibration_file
from libradtran import Libradtran, LibradtranInput, LibradtranResult
from uv_file import UVFileReader, UVFileEntry


class IrradianceEvaluation:
    """
    A utility to calculate and correct irradiance.

    The irradiance is calculated from a UV file containing raw measurement values along with
    a calibration file and an arf file to apply the required corrections.
    """

    def __init__(

            self,
            uv_file_name: str,
            calibration_file_name: str,
            arf_file_name: str,
            arf_direction: Direction = Direction.SOUTH
    ):
        """
        Create an instance from the name of a uv file, a calibration file and an ARF file and an optional direction
        for the parsing of the ARF file
        :param uv_file_name:
        :param calibration_file_name:
        :param arf_file_name:
        :param arf_direction:
        """
        self._uv_file_name = uv_file_name
        self._calibration_file_name = calibration_file_name
        self._arf_file_name = arf_file_name
        self._arf_direction = arf_direction

    def calculate(self) -> List[Spectrum]:
        """
        Parse the files into spectra
        :return: a list of spectrum
        """
        uv_file_reader = UVFileReader(self._uv_file_name)
        calibration = read_calibration_file(self._calibration_file_name)
        arf = read_arf_file(self._arf_file_name, self._arf_direction)

        spectra = []
        for uv_file_entry in uv_file_reader.get_uv_file_entries():
            calibrated_spectrum = self._to_calibrated_spectrum(uv_file_entry, calibration)
            libradtran_result = self._execute_libradtran(uv_file_entry)
            cos_correction = self._cos_correction(arf, libradtran_result)
            cos_corrected_spectrum = multiply(calibrated_spectrum, cos_correction)

            spectra.append(Spectrum(
                uv_file_entry,
                uv_file_entry.wavelengths,
                uv_file_entry.events,
                calibrated_spectrum,
                cos_corrected_spectrum,
                cos_correction,
                self._get_sza(libradtran_result)
            ))
        return spectra

    @staticmethod
    def _to_calibrated_spectrum(uv_file_entry, calibration) -> List[float]:
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

        if not uv_file_entry.brewer_info.dual:
            # Remove straylight
            below_292 = list(filter(lambda x: x.wavelength < 292, uv_file_entry.raw_values))
            if len(below_292) > 0:
                straylight_correction = mean([v.events for v in below_292])
                corrected_values = [v - straylight_correction for v in corrected_values]

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

    @staticmethod
    def _execute_libradtran(uv_file_entry: UVFileEntry) -> LibradtranResult:
        """
        Call LibRadtran with parameters extracted from a given UVFileEntry
        :param uv_file_entry: the entry to get LibRadtran's parameters from
        :return: LibRadtran's result
        """
        uv_file_header = uv_file_entry.header

        # Calculate time from the UV file's time. In those files, the time is specified as "Minutes since start of day"
        td = timedelta(minutes=uv_file_entry.raw_values[0].time)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        libradtran = Libradtran()
        libradtran.add_input(LibradtranInput.WAVELENGTH, [uv_file_entry.wavelengths[0], uv_file_entry.wavelengths[-1]])
        libradtran.add_input(LibradtranInput.LATITUDE, ["N", uv_file_header.position.latitude])

        # Negative longitudes are West and Positive ones are East
        hemisphere = "E" if uv_file_header.position.longitude < 0 else "W"
        libradtran.add_input(LibradtranInput.LONGITUDE, [hemisphere, abs(uv_file_header.position.longitude)])

        # We set LibRadtran to interpolate to exactly the values we have from the UV file
        step = uv_file_entry.wavelengths[1] - uv_file_entry.wavelengths[0]
        libradtran.add_input(LibradtranInput.SPLINE,
                             [uv_file_entry.wavelengths[0], uv_file_entry.wavelengths[-1], step])

        # TODO: read ozone value from BFile
        libradtran.add_input(LibradtranInput.OZONE, [200])

        libradtran.add_input(LibradtranInput.TIME, [
            uv_file_header.date.year + 2000,
            uv_file_header.date.month,
            uv_file_header.date.day,
            hours,
            minutes,
            seconds
        ])

        libradtran.add_input(LibradtranInput.PRESSURE, [uv_file_header.pressure])

        libradtran.add_outputs(["sza", "edir", "edn", "eglo"])
        return libradtran.calculate()

    def _cos_correction(self, arf, libradtran_result) -> List[float]:
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

        # Fdiff / Fglo
        fdiff_fglo = divide(fdiff, fglo)

        # Coscor
        coscor_diff = self._calculate_coscor_diff(arf)

        # coscor * Fdiff/Fglo
        c_inverse_left = multiply(coscor_diff, fdiff_fglo)

        # Interpolate ARF to get ARF(θ)
        angles = multiply(pi / 180, arf.szas)
        arf_spline = UnivariateSpline(angles, arf.values)

        # Fdir / Fglo
        fdir_fglo = divide(fdir, fglo)

        # Fdir/Fglo * ARF(θ)/cos(θ)
        c_inverse_right = multiply(fdir_fglo, divide(arf_spline(theta), cos(theta)))

        c_inverse = add(c_inverse_left, c_inverse_right)

        # return c
        return divide(1, c_inverse)

    def _cos_correction_2(self, arf, libradtran_result) -> List[float]:
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

        # TODO: should we set nan to 1
        # fdir_fdiff[isnan(fdir_fdiff)] = 1

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


@dataclass
class Spectrum:
    uv_file_entry: UVFileEntry
    wavelengths: List[float]
    uv_raw_values: List[float]
    original_spectrum: List[float]
    cos_corrected_spectrum: List[float]
    cos_correction: List[float]
    sza: float
