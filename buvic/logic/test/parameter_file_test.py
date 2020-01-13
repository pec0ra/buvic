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
import unittest

from buvic.logic.file import File
from buvic.logic.parameter_file import Parameters, read_parameter_file, ParameterFileParsingError, Angstrom


class UVFileReaderTestCase(unittest.TestCase):
    def test_interpolation(self):
        parameters = Parameters([10, 12, 14], [0.1, 0.3, 0.5], [Angstrom(1, 0.1), Angstrom(1.2, 0.3), Angstrom(1.5, 0.5)], [0, None, 1])

        self.assertEqual(0.1, parameters.interpolated_albedo(10, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(9, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(11, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(0, 0))

        self.assertEqual(0.3, parameters.interpolated_albedo(12, 0))
        self.assertEqual(0.3, parameters.interpolated_albedo(13, 0))

        self.assertEqual(0.5, parameters.interpolated_albedo(14, 0))
        self.assertEqual(0.5, parameters.interpolated_albedo(15, 0))
        self.assertEqual(0.5, parameters.interpolated_albedo(100, 0))

        self.assertEqual(1, parameters.interpolated_aerosol(10, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosol(9, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosol(11, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosol(0, Angstrom(0, 0)).alpha)

        self.assertEqual(1.2, parameters.interpolated_aerosol(12, Angstrom(0, 0)).alpha)
        self.assertEqual(1.2, parameters.interpolated_aerosol(13, Angstrom(0, 0)).alpha)

        self.assertEqual(1.5, parameters.interpolated_aerosol(14, Angstrom(0, 0)).alpha)
        self.assertEqual(1.5, parameters.interpolated_aerosol(15, Angstrom(0, 0)).alpha)
        self.assertEqual(1.5, parameters.interpolated_aerosol(100, Angstrom(0, 0)).alpha)

        self.assertEqual(0, parameters.cloud_cover(10))
        self.assertEqual(1, parameters.cloud_cover(14))
        self.assertEqual(None, parameters.cloud_cover(9))
        self.assertEqual(None, parameters.cloud_cover(11))
        self.assertEqual(None, parameters.cloud_cover(12))
        self.assertEqual(None, parameters.cloud_cover(13))
        self.assertEqual(None, parameters.cloud_cover(15))

        parameters = Parameters([], [], [], [])

        self.assertEqual(0, parameters.interpolated_albedo(0, 0))
        self.assertEqual(0, parameters.interpolated_albedo(10, 0))
        self.assertEqual(0, parameters.interpolated_albedo(100, 0))
        self.assertEqual(0, parameters.interpolated_albedo(1000, 0))

        self.assertEqual(0, parameters.interpolated_aerosol(0, Angstrom(0, 0)).alpha)
        self.assertEqual(0, parameters.interpolated_aerosol(10, Angstrom(0, 0)).alpha)
        self.assertEqual(0, parameters.interpolated_aerosol(100, Angstrom(0, 0)).alpha)
        self.assertEqual(0, parameters.interpolated_aerosol(1000, Angstrom(0, 0)).alpha)

        self.assertEqual(None, parameters.cloud_cover(0))
        self.assertEqual(None, parameters.cloud_cover(10))
        self.assertEqual(None, parameters.cloud_cover(100))
        self.assertEqual(None, parameters.cloud_cover(1000))

    def test_file_loading(self):
        parameters = read_parameter_file(File("buvic/logic/test/parameter_example"))

        self.assertEqual(0.1, parameters.interpolated_albedo(10, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(9, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(11, 0))
        self.assertEqual(0.1, parameters.interpolated_albedo(0, 0))

        self.assertEqual(0.3, parameters.interpolated_albedo(12, 0))
        self.assertEqual(0.3, parameters.interpolated_albedo(13, 0))

        self.assertEqual(0.5, parameters.interpolated_albedo(14, 0))
        self.assertEqual(0.5, parameters.interpolated_albedo(15, 0))
        self.assertEqual(0.5, parameters.interpolated_albedo(100, 0))

        self.assertEqual(1, parameters.interpolated_aerosol(10, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosol(9, Angstrom(0, 0)).alpha)
        self.assertEqual(1, parameters.interpolated_aerosol(0, Angstrom(0, 0)).alpha)

        self.assertEqual(1.2, parameters.interpolated_aerosol(11, Angstrom(0, 0)).alpha)
        self.assertEqual(1.2, parameters.interpolated_aerosol(12, Angstrom(0, 0)).alpha)
        self.assertEqual(1.2, parameters.interpolated_aerosol(13, Angstrom(0, 0)).alpha)

        self.assertEqual(1.5, parameters.interpolated_aerosol(14, Angstrom(0, 0)).alpha)
        self.assertEqual(1.5, parameters.interpolated_aerosol(15, Angstrom(0, 0)).alpha)
        self.assertEqual(1.5, parameters.interpolated_aerosol(100, Angstrom(0, 0)).alpha)

        self.assertEqual(None, parameters.cloud_cover(9))
        self.assertEqual(0, parameters.cloud_cover(10))
        self.assertEqual(1, parameters.cloud_cover(11))
        self.assertEqual(None, parameters.cloud_cover(12))
        self.assertEqual(None, parameters.cloud_cover(13))
        self.assertEqual(1, parameters.cloud_cover(14))
        self.assertEqual(None, parameters.cloud_cover(15))

    def test_file_failures(self):
        with self.assertRaises(ParameterFileParsingError):
            read_parameter_file(File("buvic/logic/test/parameter_example_failure_1"))

        with self.assertRaises(ParameterFileParsingError):
            read_parameter_file(File("buvic/logic/test/parameter_example_failure_2"))
