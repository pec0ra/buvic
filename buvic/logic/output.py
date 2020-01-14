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

from datetime import datetime
from enum import Enum
from logging import getLogger
from os import path, makedirs
from pathlib import Path
from threading import Lock
from typing import List
from typing import Union

from buvic.logic.brewer_infos import correct_straylight, StraylightCorrection
from buvic.logic.calculation_input import CosCorrection
from buvic.logic.darksky import DarkskyCloudCover
from buvic.logic.result import Result
from buvic.logic.utils import date_to_days, minutes_to_time
from .job import Job
from .weighted_irradiance_calculation import WeightedIrradianceCalculation
from ..const import APP_VERSION

LOG = getLogger(__name__)

lock = Lock()


class Output:
    _results: List[Result]
    _saving_dir: str

    def __init__(self, saving_dir: str, results: List[Result]):
        self._results = results
        self._saving_dir = saving_dir

    def get_jobs(self) -> List[Union[Job[Result, str], Job[List[Result], str]]]:
        output_type = self._get_output_type()
        ret_jobs = []
        if output_type == OutputType.PER_SECTION:
            for result in self._results:
                job: Union[Job[Result, str], Job[List[Result], str]] = self._get_section_job(result)
                ret_jobs.append(job)
        elif output_type == OutputType.PER_FILE:
            job = self._get_multi_section_job(self._results)
            ret_jobs.append(job)
        else:
            raise ValueError(f"Unknown output type {output_type}")
        return ret_jobs

    def _get_name(self, result: Result) -> str:
        raise NotImplementedError("Method should be implemented in subclass")

    def _get_output_type(self) -> OutputType:
        raise NotImplementedError("Method should be implemented in subclass")

    def _get_single_result_content(self, result: Result) -> str:
        raise ValueError("Single result contents are not supported for this class")

    def _get_multi_result_content(self, results: List[Result]) -> str:
        raise ValueError("Multi result contents are not supported for this class")

    def _get_section_job(self, result: Result) -> Job[Result, str]:
        return Job(self._generate_section_file, result)

    def _get_multi_section_job(self, results: List[Result]) -> Job[List[Result], str]:
        return Job(self._generate_multi_sections_file, results)

    def _generate_section_file(self, result: Result) -> str:
        file_name = self._get_name(result)
        LOG.debug(f"Generating output {file_name}")

        return self._generate_file(file_name, self._get_single_result_content(result))

    def _generate_multi_sections_file(self, results: List[Result]) -> str:
        file_name = self._get_name(results[0])
        LOG.debug(f"Generating output {file_name}")

        return self._generate_file(file_name, self._get_multi_result_content(results))

    def _generate_file(self, file_name: str, content: str) -> str:
        full_path = Path(path.join(self._saving_dir, file_name))

        with lock:
            if not path.exists(full_path.parent):
                makedirs(full_path.parent)

        with open(full_path, "w") as file:
            file.write(content)

        return file_name


class QasumeOutput(Output):
    def _get_output_type(self) -> OutputType:
        return OutputType.PER_SECTION

    def _get_name(self, result: Result) -> str:
        return result.get_qasume_name()

    def _get_single_result_content(self, result: Result) -> str:
        # Initialize the content that will be returned
        content = ""

        minutes = result.uv_file_entry.raw_values[0].time
        days = date_to_days(result.uv_file_entry.header.date)
        ozone = result.calculation_input.ozone.interpolated_ozone(minutes, result.calculation_input.settings.default_ozone)
        albedo = result.calculation_input.parameters.interpolated_albedo(days, result.calculation_input.settings.default_albedo)
        aerosol = result.calculation_input.parameters.interpolated_aerosol(days, result.calculation_input.settings.default_aerosol)
        cos_cor_to_apply = result.calculation_input.cos_correction_to_apply(minutes)

        # If the value comes from Darksky, we add the cloud cover in parenthesis after the coscor type
        cloud_cover_value = ""
        if cos_cor_to_apply != CosCorrection.NONE and isinstance(result.calculation_input.cloud_cover, DarkskyCloudCover):
            cloud_cover_value = f"(darksky:{result.calculation_input.cloud_cover.darksky_value(minutes)})"

        content += f"% Generated with Brewer UV Irradiance Calculation {APP_VERSION} at {datetime.now().replace(microsecond=0)}\n"

        content += (
            f"% {result.uv_file_entry.header.place} {result.uv_file_entry.header.position.latitude}N "
            f"{result.uv_file_entry.header.position.longitude}W\n"
        )

        straylight_correction = correct_straylight(result.calculation_input.brewer_type)
        if straylight_correction == StraylightCorrection.UNDEFINED:
            straylight_correction = result.calculation_input.settings.default_straylight_correction
        second_line_parts = {
            "type": result.uv_file_entry.header.type,
            "coscor": f"{cos_cor_to_apply.value}{cloud_cover_value}",
            "tempcor": f"{result.temperature_correction}",
            "straylightcor": straylight_correction.value,
            "o3": f"{ozone}DU",
            "albedo": str(albedo),
            "alpha": str(aerosol.alpha),
            "beta": str(aerosol.beta),
        }
        # We join the second line parts like <key>=<value> and separate them with a tabulation (\t)
        content += "% " + ("\t".join("=".join(_) for _ in second_line_parts.items())) + "\n"

        content += f"% wavelength(nm)	spectral_irradiance(W m-2 nm-1)	time_hour_UTC\n"

        for i in range(len(result.spectrum.wavelengths)):
            content += (
                f"{result.spectrum.wavelengths[i]:.1f}\t "
                f"{result.spectrum.cos_corrected_spectrum[i] / 1000:.9f}\t   "  # converted to W m-2 nm-1
                f"{result.spectrum.measurement_times[i] / 60:.5f}\n"  # converted to hours
            )

        return content


class UverOutput(Output):
    def _get_name(self, result: Result) -> str:
        return result.get_uver_name()

    def _get_output_type(self) -> OutputType:
        return OutputType.PER_FILE

    def _get_multi_result_content(self, results: List[Result]) -> str:
        calculation = WeightedIrradianceCalculation(results)
        weighted_irradiance = calculation.calculate()
        daily_dosis = calculation.calculate_daily_dosis(weighted_irradiance)

        # Initialize the content that will be returned
        content = ""

        content += f"{weighted_irradiance.type.value} dosis [Jul/m2]: {daily_dosis: 11.6f}\n"
        content += f"Time {weighted_irradiance.type.value} Weighted Irradiance [mW/m2]\n"

        for i, time in enumerate(weighted_irradiance.times):
            content += f"{time:11.6f}    {weighted_irradiance.values[i]:.6f}\n"

        return content


class WoudcOutput(Output):
    def _get_name(self, result: Result) -> str:
        return result.get_woudc_name()

    def _get_output_type(self) -> OutputType:
        return OutputType.PER_FILE

    def _get_multi_result_content(self, results: List[Result]) -> str:
        content = ""

        content += self._get_woudc_header(results[0])
        for result in results:
            content += self._to_woudc(result)

        return content

    @staticmethod
    def _to_woudc(result: Result) -> str:
        minutes = result.uv_file_entry.raw_values[0].time
        time = minutes_to_time(minutes)

        content = ""
        content += (
            "\n"
            "#TIMESTAMP\n"
            "UTCOffset,Date,Time\n"
            f"+00:00:00,{result.uv_file_entry.header.date.isoformat()},{time.hour:02d}:{time.minute:02d}:{time.second:02d}\n"
        )
        content += "\n"
        content += (
            "#GLOBAL_SUMMARY\n"
            "Time,IntACGIH,IntCIE,ZenAngle,MuValue,AzimAngle,Flag,TempC\n"
            f"{time.hour:02d}:{time.minute:02d}:{time.second:02d},3.108E-05,1.737E-04,89.10,{result.sza},119.68,,"  # TODO
            f"{result.uv_file_entry.header.temperature:.1f}\n"
        )
        content += "\n"
        content += "#GLOBAL\n"

        content += f"Wavelength,S-Irradiance,Time\n"

        for i in range(len(result.spectrum.wavelengths)):
            time = minutes_to_time(result.spectrum.measurement_times[i])
            content += (
                f"{result.spectrum.wavelengths[i]:.1f},"
                f"{'%E' % (result.spectrum.cos_corrected_spectrum[i] / 1000)},"  # convert to W m-2 nm-1
                f"{time.hour:02d}:{time.minute:02d}:{time.second:02d}\n"
            )

        return content

    @staticmethod
    def _get_woudc_header(result: Result) -> str:
        position = result.uv_file_entry.header.position
        altitude = (1 - pow(result.uv_file_entry.header.pressure / 1013.25, 0.190284)) * 44307.69396
        brewer_type = result.calculation_input.brewer_type.upper() if result.calculation_input.brewer_type is not None else "UNKNOWN"
        return (
            f"*SOFTWARE: BUVIC {APP_VERSION}\n"
            "\n"
            "#CONTENT\n"
            "Class,Category,Level,Form\n"
            "WOUDC,Spectral,1.0,1\n"
            "\n"
            "#DATA_GENERATION\n"
            "Date,Agency,Version,ScientificAuthority\n"
            f"{result.uv_file_entry.header.date.isoformat()},TODO,1.0,TODO\n"
            "\n"
            "#PLATFORM\n"
            "Type,ID,Name,Country,GAW_ID\n"
            "TODO_STN,315,Eureka,CAN,71917\n"
            "\n"
            "#INSTRUMENT\n"
            "Name,Model,Number\n"
            f"Brewer,{brewer_type},{result.calculation_input.brewer_id}\n"
            "\n"
            "#LOCATION\n"
            "Latitude,Longitude,Height\n"
            f"{position.latitude}, {-position.longitude}, {altitude:.0f}\n"
        )


class OutputType(Enum):
    PER_SECTION = 0
    PER_FILE = 1
