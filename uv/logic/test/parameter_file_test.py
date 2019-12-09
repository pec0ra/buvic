import unittest

from uv.logic.calculation_input import Angstrom
from uv.logic.parameter_file import Parameters, read_parameter_file, ParameterFileParsingError


class UVFileReaderTestCase(unittest.TestCase):

    def test_interpolation(self):
        parameters = Parameters(
            [10, 12, 14],
            [0.1, 0.3, 0.5],
            [Angstrom(1, 0.1), Angstrom(1.2, 0.3), Angstrom(1.5, 0.5)]
        )

        self.assertEqual(0.1, parameters.interpolated_albedo(10, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(9, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(11, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(0, 0))

        self.assertEqual(0.3, parameters.interpolated_albedo(12, 0))
        self.assertEqual(0.3, parameters.interpolated_albedo(13, 0))

        self.assertEqual(0.5, parameters.interpolated_albedo(14, 0))
        self.assertEqual(0.5, parameters.interpolated_albedo(15, 0))
        self.assertEqual(0.5, parameters.interpolated_albedo(100, 0))

        self.assertEqual(1, parameters.interpolated_aerosols(10, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosols(9, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosols(11, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosols(0, Angstrom(0, 0)).alpha)

        self.assertEqual(1.2, parameters.interpolated_aerosols(12, Angstrom(0, 0)).alpha)
        self.assertEqual(1.2, parameters.interpolated_aerosols(13, Angstrom(0, 0)).alpha)

        self.assertEqual(1.5, parameters.interpolated_aerosols(14, Angstrom(0, 0)).alpha)
        self.assertEqual(1.5, parameters.interpolated_aerosols(15, Angstrom(0, 0)).alpha)
        self.assertEqual(1.5, parameters.interpolated_aerosols(100, Angstrom(0, 0)).alpha)

        parameters = Parameters(
            [],
            [],
            []
        )

        self.assertEqual(0, parameters.interpolated_albedo(0, 0))
        self.assertEqual(0, parameters.interpolated_albedo(10, 0))
        self.assertEqual(0, parameters.interpolated_albedo(100, 0))
        self.assertEqual(0, parameters.interpolated_albedo(1000, 0))

        self.assertEqual(0, parameters.interpolated_aerosols(0, Angstrom(0, 0)).alpha)
        self.assertEqual(0, parameters.interpolated_aerosols(10, Angstrom(0, 0)).alpha)
        self.assertEqual(0, parameters.interpolated_aerosols(100, Angstrom(0, 0)).alpha)
        self.assertEqual(0, parameters.interpolated_aerosols(1000, Angstrom(0, 0)).alpha)

    def test_file_loading(self):
        parameters = read_parameter_file("parameter_example")

        self.assertEqual(0.1, parameters.interpolated_albedo(10, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(9, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(11, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(0, 0))

        self.assertEqual(0.3, parameters.interpolated_albedo(12, 0))
        self.assertEqual(0.3, parameters.interpolated_albedo(13, 0))

        self.assertEqual(0.5, parameters.interpolated_albedo(14, 0))
        self.assertEqual(0.5, parameters.interpolated_albedo(15, 0))
        self.assertEqual(0.5, parameters.interpolated_albedo(100, 0))

        self.assertEqual(1, parameters.interpolated_aerosols(10, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosols(9, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosols(0, Angstrom(0, 0)).alpha)

        self.assertEqual(1.2, parameters.interpolated_aerosols(11, Angstrom(0, 0)).alpha)
        self.assertEqual(1.2, parameters.interpolated_aerosols(12, Angstrom(0, 0)).alpha)
        self.assertEqual(1.2, parameters.interpolated_aerosols(13, Angstrom(0, 0)).alpha)

        self.assertEqual(1.5, parameters.interpolated_aerosols(14, Angstrom(0, 0)).alpha)
        self.assertEqual(1.5, parameters.interpolated_aerosols(15, Angstrom(0, 0)).alpha)
        self.assertEqual(1.5, parameters.interpolated_aerosols(100, Angstrom(0, 0)).alpha)

    def test_file_failures(self):
        with self.assertRaises(ParameterFileParsingError):
            read_parameter_file("parameter_example_failure_1")

        with self.assertRaises(ParameterFileParsingError):
            read_parameter_file("parameter_example_failure_2")
