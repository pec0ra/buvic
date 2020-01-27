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
import logging
import unittest
from datetime import date

from buvic.logic.calculation_input import CalculationInput
from buvic.logic.darksky import ParameterCloudCover, DefaultCloudCover
from buvic.logic.file import File
from buvic.logic.settings import Settings, DataSource
from buvic.logutils import init_logging


class UVFileReaderTestCase(unittest.TestCase):
    @staticmethod
    def test_cache():
        init_logging(logging.DEBUG)

        calculation_input = CalculationInput(
            "033",
            date(2019, 12, 20),
            Settings(),
            File("dummy"),
            File("dummy"),
            File("buvic/logic/test/calibration_example"),
            File("dummy"),
        )

        c = calculation_input.calibration
        del c

        calculation_input.calibration_file_name = "does_not_exist"
        # No exception is thrown since the calibration value used is cached
        c = calculation_input.calibration
        del c

    def test_cloud_cover(self):
        init_logging(logging.DEBUG)

        calculation_input = CalculationInput(
            "033",
            date(2019, 12, 20),
            Settings(),
            File("buvic/logic/test/uv_example"),
            File("dummy"),
            File("dummy"),
            File("dummy"),
            parameter_file_name=File("buvic/logic/test/parameter_example"),
        )

        self.assertTrue(isinstance(calculation_input.cloud_cover, ParameterCloudCover))
        self.assertTrue(calculation_input.cloud_cover.is_diffuse(4))
        self.assertTrue(calculation_input.cloud_cover.is_diffuse(10))
        self.assertTrue(calculation_input.cloud_cover.is_diffuse(15))

        calculation_input = CalculationInput(
            "033",
            date(2019, 12, 20),
            Settings(),
            File("buvic/logic/test/uv_example"),
            File("dummy"),
            File("dummy"),
            File("dummy"),
            parameter_file_name=None,
        )

        self.assertTrue(isinstance(calculation_input.cloud_cover, DefaultCloudCover))
        self.assertFalse(calculation_input.cloud_cover.is_diffuse(4))
        self.assertFalse(calculation_input.cloud_cover.is_diffuse(10))
        self.assertFalse(calculation_input.cloud_cover.is_diffuse(15))

    def test_uv_sources(self):
        calculation_input = CalculationInput(
            "033",
            date(2019, 12, 20),
            Settings(uv_data_source=DataSource.FILES),
            File("buvic/logic/test/uv_example"),
            File("dummy"),
            File("dummy"),
            File("dummy"),
        )

        entries = calculation_input.uv_file_entries
        # 30 sections are present in `uv_example`
        self.assertEqual(30, len(entries))

        calculation_input = CalculationInput(
            "033",
            date(2019, 6, 20),
            Settings(uv_data_source=DataSource.EUBREWNET),
            File("dummy"),
            File("dummy"),
            File("dummy"),
            File("dummy"),
        )

        # 13 sections are present on EUBREWNET for day 2019-06-20
        entries = calculation_input.uv_file_entries
        self.assertEqual(13, len(entries))

        # Test that uv, uvr and ozone data can be retrieved from EUBREWNET
        calculation_input = CalculationInput(
            "033",
            date(2019, 6, 20),
            Settings(uv_data_source=DataSource.EUBREWNET, uvr_data_source=DataSource.EUBREWNET, ozone_data_source=DataSource.EUBREWNET),
            File("dummy"),
            File("dummy"),
            File("dummy"),
            None,
        )

        calculation_input.init_properties()
