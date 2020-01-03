import logging
import unittest
import warnings
from datetime import date

from buvic.brewer_infos import StraylightCorrection
from buvic.logic.calculation_input import CalculationInput
from buvic.logic.darksky import ParameterCloudCover, DefaultCloudCover
from buvic.logic.file import File
from buvic.logic.settings import Settings, DataSource
from buvic.logutils import init_logging


class UVFileReaderTestCase(unittest.TestCase):

    def test_cache(self):
        init_logging(logging.DEBUG)

        calculation_input = CalculationInput(
            "033",
            date(2019, 12, 20),
            Settings(),
            File("dummy"),
            File("dummy"),
            File("buvic/logic/test/calibration_example"),
            File("dummy"),
            StraylightCorrection.UNDEFINED
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
            StraylightCorrection.UNDEFINED,
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
            StraylightCorrection.UNDEFINED,
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
            StraylightCorrection.UNDEFINED
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
            StraylightCorrection.UNDEFINED
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
            StraylightCorrection.UNDEFINED
        )

        with warnings.catch_warnings(record=True) as w:
            calculation_input.init_properties()
            # We expect 3 warnings: arf file not found, parameter file not found and darksky token not set
            self.assertEqual(3, len(w))
