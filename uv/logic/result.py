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
        minutes = self.uv_file_entry.raw_values[0].time
        days = date_to_days(self.uv_file_entry.header.date)
        ozone = self.calculation_input.ozone.interpolated_value(minutes, self.calculation_input.input_parameters.default_ozone)
        albedo = self.calculation_input.parameters.interpolated_albedo(days, self.calculation_input.input_parameters.default_albedo)
        aerosol = self.calculation_input.parameters.interpolated_aerosol(days, self.calculation_input.input_parameters.default_aerosol)
        cos_cor_to_apply = self.calculation_input.cos_correction_to_apply(minutes)
        file.write(f"% {self.uv_file_entry.header.place} {self.uv_file_entry.header.position.latitude}N "
                   f"{self.uv_file_entry.header.position.longitude}W\n")
        file.write(f"% type={self.uv_file_entry.header.type}\tcoscor={cos_cor_to_apply.value}\ttempcor=false\to3={ozone}DU\t"
                   f"albedo={albedo}\talpha={aerosol.alpha}\t"
                   f"beta={aerosol.beta}\n")
        file.write(f"% wavelength(nm)	spectral_irradiance(W m-2 nm-1)	time_hour_UTC\n")

        for i in range(len(self.spectrum.wavelengths)):
            file.write(f"{self.spectrum.wavelengths[i]:.1f}\t {self.spectrum.cos_corrected_spectrum[i] / 1000:.9f}\t   "
                       f"{self.spectrum.measurement_times[i] / 60:.5f}\n")

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
