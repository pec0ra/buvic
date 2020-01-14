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

from dataclasses import dataclass
from os import path
from typing import List

from buvic.logic.utils import date_to_days, minutes_to_time
from .calculation_input import CalculationInput
from .uv_file import UVFileEntry


@dataclass
class Result:
    index: int
    calculation_input: CalculationInput
    sza: float
    temperature_correction: float
    spectrum: Spectrum

    def get_qasume_name(self, prefix: str = "", suffix: str = "") -> str:
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
        return path.join(self.get_relative_path(), file_name)

    def get_woudc_name(self):
        """
        Create a WOUDC format name specific to this result.

        :return: the created file name
        """
        bid = self.calculation_input.brewer_id
        d = self.uv_file_entry.header.date
        agency = "TODO"  # TODO
        file_name = f"{d.year:04d}{d.month:02d}{d.day:02d}.Brewer.{self.calculation_input.brewer_type.upper()}.{bid}" f".{agency}.csv"
        return path.join(self.get_relative_path(), file_name)

    def get_uver_name(self):
        """
        Create a UVER name specific to this result.

        :return: the created file name
        """
        bid = self.calculation_input.brewer_id
        d = self.uv_file_entry.header.date
        file_name = f"UVER{date_to_days(d):03d}{d.year:02d}.{bid}"
        return path.join(self.get_relative_path(), file_name)

    def get_relative_path(self):
        """
        Get the path (relative to the output directory) in which to the output files for this result.

        If a UV file and/or a B file exist, the common component of their path is used. Otherwise, the path is created from the brewer id
        and the year.

        If the option to skip cos correction is checked in the settings, a directory called 'nocoscor' is prepended to the path.

        examples:
            uv file: 033/2019/uv/UV11119.033 and b file: 033/2019/b/B11119.033 will give a relative path 033/2019/
            uv file: 2019/033/uv/UV11119.033 and b file: 2019/033/b/B11119.033 will give a relative path 2019/033/
            uv file: 033/2019/UV11119.033 and b file: 033/2019/B11119.033 will give a relative path 033/2019/
            uv file: 033/2019/uv/UV11119.033 and b file not specified will give a relative path 033/2019/uv/
            uv file and b file not specified will give a relative path 033/2019/

            Any of this example will be prepended by 'nocoscor' if the option is checked (e.g. nocoscor/033/2019/ )

        :return: the path
        """
        if self.calculation_input.uv_file_name is not None and self.calculation_input.b_file_name is not None:
            output_path = path.commonprefix([self.calculation_input.b_file_name.path, self.calculation_input.uv_file_name.path])
        elif self.calculation_input.uv_file_name is not None:
            output_path = self.calculation_input.uv_file_name.path
        elif self.calculation_input.b_file_name is not None:
            output_path = self.calculation_input.b_file_name.path
        else:
            output_path = path.join(f"{self.calculation_input.brewer_id}", f"{self.calculation_input.date.year}")

        if self.calculation_input.settings.no_coscor:
            return path.join("nocoscor", output_path)
        else:
            return output_path

    @property
    def uv_file_entry(self) -> UVFileEntry:
        return self.calculation_input.uv_file_entries[self.index]


@dataclass
class Spectrum:
    wavelengths: List[float]
    measurement_times: List[float]  # in minutes
    uv_raw_values: List[float]
    original_spectrum: List[float]  # in mW m-2 nm-1
    cos_corrected_spectrum: List[float]  # in mW m-2 nm-1
    cos_correction: List[float]
