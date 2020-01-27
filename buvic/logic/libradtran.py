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

import os
import re
import uuid
from dataclasses import dataclass
from enum import Enum
from subprocess import PIPE, run
from typing import List, Dict, Any

from buvic.libradtran_command import LIBRADTRAN_COMMAND
from ..const import TMP_FILE_DIR


class Libradtran:
    def __init__(self):
        self._outputs: List[str] = []
        self._inputs: Dict[LibradtranInput, List[Any]] = {}

    def add_input(self, input_type: LibradtranInput, input_values: List[Any]) -> None:
        """
        Add an input parameter to include in the LibRadtran input file.

        :param input_type: the type of the input
        :param input_values: the values for the input
        """
        if not input_type.value.check_input_values(input_values):
            raise ValueError(
                "Wrong number of input given for input "
                + input_type.name
                + ". Expected "
                + str(input_type.value.value_count)
                + " but received "
                + str(len(input_values))
            )
        self._inputs[input_type] = input_values

    def add_output(self, output: str) -> None:
        """
        Add an output value for LibRadtran. This value will be included in LibRadtran's input file as `output_user`.

        :param output: the output value
        """
        if output not in self._outputs:
            self._outputs.append(output)

    def add_outputs(self, outputs: List[str]) -> None:
        """
        Add multiple output values for LibRadtran. These values will be included in LibRadtran's input file as
        `output_user`.

        :param outputs: the output values
        """
        for output in outputs:
            self.add_output(output)

    def calculate(self) -> LibradtranResult:
        """
        Call LibRadtran to execute the calculations
        :return: LibRadtran's result
        """
        self._check_consistency()

        # Generate LibRadtran's input file
        input_file_name = self._create_input_file()

        # Call LibRadtran
        command = LIBRADTRAN_COMMAND + " < " + input_file_name
        result = run(command, stdout=PIPE, universal_newlines=True, shell=True)
        if result.returncode != 0:
            raise ChildProcessError(
                "LibRadtran or docker returned an error. See logs or input file '" + input_file_name + "' for more details"
            )

        # Remove LibRadtran's input file
        os.remove(input_file_name)

        return LibradtranResult(self._outputs, result.stdout)

    def _create_input_file(self) -> str:
        """
        Generate the LibRadtran input file, save it and return its name
        :return: the name of the file
        """

        # Generate a unique file name
        file_name = TMP_FILE_DIR + "input_" + str(uuid.uuid4()) + ".in"

        with open(file_name, "w") as input_file:
            # Write static content to the file
            input_file.write(LIBRADTRAN_STATIC_START)

            # Write inputs to the file
            for input_param in self._inputs:
                input_values = self._inputs[input_param]
                input_file.write(input_param.value.line.format(*input_values) + "\n")

            # Write outputs to the file
            input_file.write("output_user " + " ".join(self._outputs) + "\n")

        return file_name

    def _check_consistency(self) -> None:
        """Check that LibRadtran's inputs and outputs are corrects. Throw an error if this is not the case"""
        if LibradtranInput.WAVELENGTH not in self._inputs:
            raise ValueError("At least wavelength needs to be set as input")

        if len(self._outputs) == 0:
            raise ValueError("At least one output must be set")


@dataclass
class LibradtranResult:
    columns: Dict[str, List[float]]

    def __init__(self, column_names: List[str], libradtran_output: str):
        """
        Create an instance from a given LibRadtran's raw output and its column names
        :param column_names: the names of the columns
        :param libradtran_output: LibRadtran's raw output
        """

        # Initialize dictionary
        self.columns = {}
        for output_value in column_names:
            self.columns[output_value] = []

        for line in libradtran_output.splitlines():
            # Each line consists of values separated by spaces
            line_values = re.split(r"\s+", line.strip())

            if len(line_values) != len(column_names):
                raise ValueError(
                    "LibRadtran din't produce the correct amount of columns. Expected: "
                    + str(len(column_names))
                    + ", actual: "
                    + str(len(line_values))
                )

            # We add each of the values to the list of its corresponding output
            for i, _ in enumerate(column_names):
                output_value = column_names[i]
                self.columns[output_value].append(float(line_values[i]))


@dataclass
class LibradtranInputInfo:
    value_count: int
    line: str

    def check_input_values(self, values: List[Any]) -> bool:
        return len(values) == self.value_count


class LibradtranInput(Enum):
    AEROSOL = LibradtranInputInfo(2, "aerosol_angstrom {} {}")
    ALBEDO = LibradtranInputInfo(1, "albedo {}")
    LATITUDE = LibradtranInputInfo(2, "latitude {} {}")
    LONGITUDE = LibradtranInputInfo(2, "longitude {} {}")
    OZONE = LibradtranInputInfo(1, "mol_modify O3 {} DU")
    PRESSURE = LibradtranInputInfo(1, "pressure {}")
    SPLINE = LibradtranInputInfo(3, "spline {} {} {}")
    SZA = LibradtranInputInfo(1, "sza {}")
    TIME = LibradtranInputInfo(6, "time {} {} {} {} {} {}")
    WAVELENGTH = LibradtranInputInfo(2, "wavelength {} {}")


LIBRADTRAN_STATIC_START = (
    "data_files_path /opt/libRadtran/data/\n"
    "atmosphere_file /opt/libRadtran/data/atmmod/afglus.dat # Location of the extraterrestrial spectrum\n"
    "source solar /opt/libRadtran/data/solar_flux/atlas_plus_modtran\n"
    "aerosol_default          # Aerosol\n"
    "rte_solver disort        # Radiative transfer equation solver\n"
    "number_of_streams  8     # Number of streams\n"
    "quiet\n"
)
