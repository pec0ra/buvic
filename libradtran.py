from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from enum import Enum
from subprocess import PIPE, run
from typing import List, Dict


class Libradtran:

    def __init__(self):
        self._outputs: List[str] = []
        self._inputs: Dict[LibradtranInput, List[float]] = {}

    def add_input(self, input_type: LibradtranInput, input_values: List[float]) -> None:
        """
        Add an input parameter to include in the LibRadtran input file.

        :param input_type: the type of the input
        :param input_values: the values for the input
        """
        if not input_type.value.check_input_values(input_values):
            raise ValueError("Wrong number of input given for input " + input_type.name + ". Expected " +
                             str(input_type.value.value_count) + " but received " + str(len(input_values)))
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
        command = "docker run -i siarhei/libradtran uvspec < " + input_file_name
        result = run(command, stdout=PIPE, universal_newlines=True, shell=True)
        if result.returncode != 0:
            raise ChildProcessError("LibRadtran or docker returned an error. See logs or input file '" +
                                    input_file_name + "' for more details")

        # Remove LibRadtran's input file
        os.remove(input_file_name)

        return LibradtranResult(self._outputs, result.stdout)

    def _create_input_file(self) -> str:
        """
        Generate the LibRadtran input file, save it and return its name
        :return: the name of the file
        """

        # Generate a unique file name
        file_name = str(uuid.uuid4()) + ".in"

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
        """
        Check that LibRadtran's inputs and outputs are corrects. Throw an error if this is not the case
        """
        if LibradtranInput.WAVELENGTH not in self._inputs:
            raise ValueError("At least wavelength needs to be set as input")

        if len(self._outputs) == 0:
            raise ValueError("At least one output must be set")


@dataclass()
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
            line_values = re.split("\s+", line.strip())

            if len(line_values) != len(column_names):
                raise ValueError("LibRadtran din't produce the correct amount of columns. Expected: " +
                                 str(len(column_names)) + ", actual: " + str(len(line_values)))

            # We add each of the values to the list of its corresponding output
            for i in range(len(column_names)):
                output_value = column_names[i]
                self.columns[output_value].append(float(line_values[i]))


@dataclass
class LibradtranInputInfo:
    value_count: int
    line: str

    def check_input_values(self, values: List[float]) -> bool:
        return len(values) == self.value_count


class LibradtranInput(Enum):
    ALBEDO = LibradtranInputInfo(
        1,
        "albedo {}"
    )
    OZONE = LibradtranInputInfo(
        1,
        "mol_modify O3 {} DU"
    )
    PRESSURE = LibradtranInputInfo(
        1,
        "pressure {}"
    )
    AEROSOL = LibradtranInputInfo(
        2,
        "aerosol_angstrom {} {}"
    )
    WAVELENGTH = LibradtranInputInfo(
        2,
        "wavelength {} {}"
    )
    SZA = LibradtranInputInfo(
        1,
        "sza {}"
    )
    SPLINE = LibradtranInputInfo(
        3,
        "spline {} {} {}"
    )


LIBRADTRAN_STATIC_START = "data_files_path data/\n" \
                          "atmosphere_file data/atmmod/afglus.dat # Location of the extraterrestrial spectrum\n" \
                          "source solar data/solar_flux/atlas_plus_modtran\n" \
                          "aerosol_default          # Aerosol\n" \
                          "rte_solver disort        # Radiative transfer equation solver\n" \
                          "number_of_streams  8     # Number of streams\n" \
                          "quiet\n"
