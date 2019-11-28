from __future__ import annotations

import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Tuple, Iterable, Generic, TypeVar, Callable

from numpy import multiply, divide, sin, add, pi, mean, exp, maximum, linspace, trapz, cos, isnan
from scipy.interpolate import UnivariateSpline

from uv.logic.calibration_file import Calibration
from .arf_file import read_arf_file, ARF
from .b_file import read_ozone_from_b_file, Ozone
from .calculation_input import CalculationInput
from .calibration_file import read_calibration_file
from .libradtran import Libradtran, LibradtranInput, LibradtranResult
from .result import Result, Spectrum
from .utils import minutes_to_time
from .uv_file import UVFileReader, UVFileEntry


class IrradianceCalculation:
    """
    A utility to calculate and correct irradiance.

    The irradiance is calculated from a UV file containing raw measurement values along with
    a calibration file and an arf file to apply the required corrections.
    """

    _calculation_input: CalculationInput
    _ozone: Ozone
    _calibration: Calibration
    _arf: ARF

    def __init__(
            self,
            calculation_input: CalculationInput
    ):
        """
        Create an instance from a given CalculationInput

        :param calculation_input: the object containing the file names and data required for the calculations
        """
        self._calculation_input = calculation_input

    def calculate(self) -> List[Job[Tuple[int, UVFileEntry], Result]]:
        """
        Parse the files into spectra.

        This method doesn't do the calculation directly but creates a list of calculation `Job` that can be scheduled on
        a thread pool or process pool.
        Each of the job of the list will do the calculation for one of the section of the UV File.

        See `JobUtils` for the handling of the created jobs

        :return: a list of calculation job.
        """
        uv_file_reader = UVFileReader(self._calculation_input.uv_file_name)
        uv_file_entries = uv_file_reader.get_uv_file_entries()

        self._ozone = read_ozone_from_b_file(self._calculation_input.b_file_name)
        self._calibration = read_calibration_file(self._calculation_input.calibration_file_name)
        self._arf = read_arf_file(self._calculation_input.arf_file_name, self._calculation_input.arf_direction)

        job_list = []
        for entry in enumerate(uv_file_entries):
            job_list.append(
                Job(self._calculate_entry, entry)
            )

        return job_list

    def _calculate_entry(self, index: int, uv_file_entry: UVFileEntry) -> Result:
        """
        Do the calculation for a file entry (section)
        :param index: the index of the section
        :param uv_file_entry: the file entry for which to calculate
        :return: the result of the calculation
        """

        libradtran_result = self._execute_libradtran(uv_file_entry)
        calibrated_spectrum = self._to_calibrated_spectrum(uv_file_entry, self._calibration)
        cos_correction = self._cos_correction(self._arf, libradtran_result)

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
            cos_correction
        )
        return Result(
            index,
            self._calculation_input,
            self._get_sza(libradtran_result),
            self._ozone,
            spectrum,
            uv_file_entry
        )

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

    def _execute_libradtran_parallel(self, uv_file_entries: List[UVFileEntry]) -> List[LibradtranResult]:
        """
        Create a process pool and execute LibRadtran in parallel for the given uv file entries on this pool.
        :param uv_file_entries: the UV file entries for which to execute LibRadtran
        :return: the LibRadtran results
        """

        with ThreadPoolExecutor() as pool:
            return pool.map(self._execute_libradtran, uv_file_entries)

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

        # Negative longitudes are West and Positive ones are East
        hemisphere = "E" if uv_file_header.position.longitude < 0 else "W"
        libradtran.add_input(LibradtranInput.LONGITUDE, [hemisphere, abs(uv_file_header.position.longitude)])

        # We set LibRadtran to interpolate to exactly the values we have from the UV file
        step = uv_file_entry.wavelengths[1] - uv_file_entry.wavelengths[0]
        libradtran.add_input(LibradtranInput.SPLINE,
                             [uv_file_entry.wavelengths[0], uv_file_entry.wavelengths[-1], step])

        libradtran.add_input(LibradtranInput.OZONE, [self._ozone.interpolated_value(minutes)])

        libradtran.add_input(LibradtranInput.TIME, [
            uv_file_header.date.year,
            uv_file_header.date.month,
            uv_file_header.date.day,
            time.hour,
            time.minute,
            time.second
        ])

        libradtran.add_input(LibradtranInput.PRESSURE, [uv_file_header.pressure])

        libradtran.add_input(LibradtranInput.ALBEDO, [self._calculation_input.albedo])
        libradtran.add_input(LibradtranInput.AEROSOL,
                             [self._calculation_input.aerosol[0], self._calculation_input.aerosol[1]])

        libradtran.add_outputs(["sza", "edir", "edn", "eglo"])
        result = libradtran.calculate()
        return result

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


I = TypeVar('I', bound=Iterable)
R = TypeVar('R')


@dataclass
class Job(Generic[I, R]):
    _fn: Callable[[I], R]
    _args: I

    def call(self) -> R:
        return self._fn(*self._args)
