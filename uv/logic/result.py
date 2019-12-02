from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO, List

from uv.logic.utils import date_to_days, minutes_to_time
from .calculation_input import CalculationInput
from .uv_file import UVFileEntry


@dataclass
class Result:
    index: int
    calculation_input: CalculationInput
    sza: float
    spectrum: Spectrum

    def to_qasume(self, file: TextIO) -> None:
        """
        Convert this results value into qasume format and write it to a given file
        :param file: the file to write the qasume content to
        """
        file.write("wavelength(nm)	spectral_irradiance(W m-2 nm-1)	time_min_UTC\n")

        for i in range(len(self.spectrum.wavelengths)):
            file.write(
                f"{self.spectrum.wavelengths[i]:.1f}\t {self.spectrum.cos_corrected_spectrum[i] / 1000:.9f}\t   {self.spectrum.measurement_times[i]:.5f}\n")

    def get_name(self, prefix: str = "", suffix: str = ""):
        """
        Create a name specific to this result.

        :param prefix: the prefix to add to the file name
        :param suffix: the suffix to add to the file name
        :return: the created file name
        """
        bid = self.uv_file_entry.brewer_info.id
        days = date_to_days(self.uv_file_entry.header.date)
        time = minutes_to_time(self.spectrum.measurement_times[0])
        return f"{prefix}{days:03}{time.hour:02}{time.minute:02}G.{bid}{suffix}"

    @property
    def uv_file_entry(self) -> UVFileEntry:
        return self.calculation_input.uv_file_entries[self.index]


@dataclass
class Spectrum:
    wavelengths: List[float]
    measurement_times: List[float]
    uv_raw_values: List[float]
    original_spectrum: List[float]
    cos_corrected_spectrum: List[float]
    cos_correction: List[float]
