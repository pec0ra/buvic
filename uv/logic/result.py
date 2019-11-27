from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import TextIO, List

from numpy import isnan

from .b_file import Ozone
from .calculation_input import CalculationInput
from .uv_file import UVFileEntry


@dataclass
class Result:
    index: int
    calculation_input: CalculationInput
    sza: float
    ozone: Ozone
    spectrum: Spectrum
    uv_file_entry: UVFileEntry

    def to_csv(self, file: TextIO) -> None:
        """
        Convert this results value into csv and write it to a given file
        :param file: the file to write the csv content to
        """
        writer = csv.writer(file)
        writer.writerow(
            ["wavelength", "Measurement raw value", "Spectrum (Non COS corrected)", "COS corrected spectrum",
             "COS correction factor"])

        cos_correction_no_nan = self.spectrum.cos_correction.copy()
        cos_correction_no_nan[isnan(cos_correction_no_nan)] = 1
        for i in range(len(self.spectrum.wavelengths)):
            writer.writerow([
                self.spectrum.wavelengths[i],
                self.spectrum.uv_raw_values[i],
                self.spectrum.original_spectrum[i],
                self.spectrum.cos_corrected_spectrum[i],
                cos_correction_no_nan[i]
            ])

    def get_name(self, prefix: str, suffix: str):
        """
        Create a name specific to this result.

        :param prefix: the prefix to add to the file name
        :param suffix: the suffix to add to the file name
        :return: the created file name
        """
        bid = self.uv_file_entry.brewer_info.id
        return prefix + bid + "_" + self.uv_file_entry.header.date.isoformat().replace('-', '') + "_" + str(
            self.index) + "_" + self.calculation_input.to_hash() + suffix


@dataclass
class Spectrum:
    wavelengths: List[float]
    measurement_times: List[float]
    uv_raw_values: List[float]
    original_spectrum: List[float]
    cos_corrected_spectrum: List[float]
    cos_correction: List[float]
