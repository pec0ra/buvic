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
from os import path, makedirs
from pathlib import Path
from threading import Lock
from typing import TextIO, List

from buvic.logic.result import Result
from buvic.logic.utils import minutes_to_time
from buvic.logic.weighted_irradiance_calculation import WeightedIrradianceCalculation
from ..const import APP_VERSION

lock = Lock()


def create_csv(saving_dir: str, result: Result) -> str:
    file_name = result.get_name()

    full_path = Path(path.join(saving_dir, file_name))

    with lock:
        if not path.exists(full_path.parent):
            makedirs(full_path.parent)

    with open(full_path, "w") as csv_file:
        result.to_qasume(csv_file)
    return file_name


def create_woudc(saving_dir: str, results: List[Result]) -> str:
    if len(results) == 0:
        return ""
    file_name = results[0].get_woudc_name()

    full_path = Path(path.join(saving_dir, file_name))

    with lock:
        if not path.exists(full_path.parent):
            makedirs(full_path.parent)

    with open(full_path, "w") as file:
        file.write(get_woudc_header(results[0]))
        for result in results:
            to_woudc(result, file)
    return file_name


def to_woudc(result: Result, file: TextIO) -> None:
    """
    Convert a result into woudc format and write it to a given file
    :param result: the result to convert
    :param file: the file to write the content to
    """
    minutes = result.uv_file_entry.raw_values[0].time
    time = minutes_to_time(minutes)
    file.write(
        "\n"
        "#TIMESTAMP\n"
        "UTCOffset,Date,Time\n"
        f"+00:00:00,{result.uv_file_entry.header.date.isoformat()},{time.hour:02d}:{time.minute:02d}:{time.second:02d}\n"
    )
    file.write("\n")
    file.write(
        "#GLOBAL_SUMMARY\n"
        "Time,IntACGIH,IntCIE,ZenAngle,MuValue,AzimAngle,Flag,TempC\n"
        f"{time.hour:02d}:{time.minute:02d}:{time.second:02d},3.108E-05,1.737E-04,89.10,{result.sza},119.68,,"  # TODO
        f"{result.uv_file_entry.header.temperature}\n"
    )
    file.write("\n")
    file.write("#GLOBAL\n")

    file.write(f"Wavelength,S-Irradiance,Time\n")

    for i in range(len(result.spectrum.wavelengths)):
        time = minutes_to_time(result.spectrum.measurement_times[i])
        file.write(
            f"{result.spectrum.wavelengths[i]:.1f},"
            f"{'%E' % (result.spectrum.cos_corrected_spectrum[i] / 1000)},"  # convert to W m-2 nm-1
            f"{time.hour:02d}:{time.minute:02d}:{time.second:02d}\n"
        )


def get_woudc_header(result: Result) -> str:
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


def create_uver(saving_dir: str, file_name: str, calculation: WeightedIrradianceCalculation) -> str:
    full_path = Path(path.join(saving_dir, file_name))

    with lock:
        if not path.exists(full_path.parent):
            makedirs(full_path.parent)

    weighted_irradiance = calculation.calculate()
    daily_dosis = calculation.calculate_daily_dosis(weighted_irradiance)

    with open(full_path, "w") as file:

        file.write(f"{weighted_irradiance.type.value} dosis [Jul/m2]: {daily_dosis: 11.6f}\n")
        file.write(f"Time {weighted_irradiance.type.value} Weighted Irradiance [mW/m2]\n")

        for i, time in enumerate(weighted_irradiance.times):
            file.write(f"{time:11.6f}    {weighted_irradiance.values[i]:.6f}\n")
    return file_name
