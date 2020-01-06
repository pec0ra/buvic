from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from os import path
from typing import TextIO, List

from buvic.brewer_infos import StraylightCorrection
from buvic.logic.darksky import DarkskyCloudCover
from buvic.logic.utils import date_to_days, minutes_to_time
from .calculation_input import CalculationInput, CosCorrection
from .uv_file import UVFileEntry
from ..const import APP_VERSION


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
        ozone = self.calculation_input.ozone.interpolated_ozone(minutes, self.calculation_input.settings.default_ozone)
        albedo = self.calculation_input.parameters.interpolated_albedo(days, self.calculation_input.settings.default_albedo)
        aerosol = self.calculation_input.parameters.interpolated_aerosol(days, self.calculation_input.settings.default_aerosol)
        cos_cor_to_apply = self.calculation_input.cos_correction_to_apply(minutes)

        # If the value comes from Darksky, we add the cloud cover in parenthesis after the coscor type
        cloud_cover_value = ""
        if isinstance(self.calculation_input.cloud_cover, DarkskyCloudCover) and cos_cor_to_apply != CosCorrection.NONE:
            cloud_cover_value = f"(darksky:{self.calculation_input.cloud_cover.darksky_value(minutes)})"

        file.write(f"% Generated with Brewer UV Irradiance Calculation {APP_VERSION} at {datetime.now().replace(microsecond=0)}\n")

        file.write(f"% {self.uv_file_entry.header.place} {self.uv_file_entry.header.position.latitude}N "
                   f"{self.uv_file_entry.header.position.longitude}W\n")

        straylight_correction = self.calculation_input.straylight_correction
        if straylight_correction == StraylightCorrection.UNDEFINED:
            straylight_correction = self.calculation_input.settings.default_straylight_correction
        second_line_parts = {
            "type": self.uv_file_entry.header.type,
            "coscor": f"{cos_cor_to_apply.value}{cloud_cover_value}",
            "tempcor": "false",
            "straylightcor": straylight_correction.value,
            "o3": f"{ozone}DU",
            "albedo": str(albedo),
            "alpha": str(aerosol.alpha),
            "beta": str(aerosol.beta)
        }
        # We join the second line parts like <key>=<value> and separate them with a tabulation (\t)
        file.write("% " + ("\t".join("=".join(_) for _ in second_line_parts.items())) + "\n")

        file.write(f"% wavelength(nm)	spectral_irradiance(W m-2 nm-1)	time_hour_UTC\n")

        for i in range(len(self.spectrum.wavelengths)):
            file.write(f"{self.spectrum.wavelengths[i]:.1f}\t {self.spectrum.cos_corrected_spectrum[i] / 1000:.9f}\t   "
                       f"{self.spectrum.measurement_times[i] / 60:.5f}\n")

    def get_name(self, prefix: str = "", suffix: str = "") -> str:
        """
        Create a name specific to this result.

        :param prefix: the prefix to add to the file name
        :param suffix: the suffix to add to the file name
        :return: the created file name
        """
        bid = self.calculation_input.brewer_id
        days = date_to_days(self.calculation_input.date)
        time = minutes_to_time(self.spectrum.measurement_times[0])

        file_name = f"{prefix}{days:03}{time.hour:02}{time.minute:02}G.{bid}{suffix}"
        if self.calculation_input.uv_file_name is not None and self.calculation_input.b_file_name is not None:
            output_path = path.commonprefix([self.calculation_input.b_file_name.path, self.calculation_input.uv_file_name.path])
        elif self.calculation_input.uv_file_name is not None:
            output_path = self.calculation_input.uv_file_name.path
        elif self.calculation_input.b_file_name is not None:
            output_path = self.calculation_input.b_file_name.path
        else:
            output_path = path.join(f"{self.calculation_input.brewer_id}", f"{self.calculation_input.date.year}")
        file_path = path.join(output_path, file_name)

        if self.calculation_input.settings.no_coscor:
            return path.join("nocoscor", file_path)
        else:
            return file_path

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
