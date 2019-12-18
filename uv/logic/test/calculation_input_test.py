import logging
import unittest

from uv.logic.calculation_input import CalculationInput, InputParameters
from uv.logic.darksky import ParameterCloudCover, DefaultCloudCover
from uv.logic.file import File
from uv.logic.parameter_file import Angstrom
from uv.logutils import init_logging


class UVFileReaderTestCase(unittest.TestCase):

    def test_cache(self):
        init_logging(logging.DEBUG)

        calculation_input = CalculationInput(
            InputParameters(0, Angstrom(0, 0), 0),
            File("dummy"),
            File("dummy"),
            File("uv/logic/test/calibration_example"),
            File("dummy"),
        )

        c = calculation_input.calibration

        calculation_input.calibration_file_name = "does_not_exist"
        # No exception is thrown since the calibration value used is cached
        c = calculation_input.calibration

    def test_cloud_cover(self):
        init_logging(logging.DEBUG)

        calculation_input = CalculationInput(
            InputParameters(0, Angstrom(0, 0), 0),
            File("uv/logic/test/uv_example"),
            File("dummy"),
            File("dummy"),
            File("dummy"),
            parameter_file_name=File("uv/logic/test/parameter_example"),
        )

        self.assertTrue(isinstance(calculation_input.cloud_cover, ParameterCloudCover))
        self.assertTrue(calculation_input.cloud_cover.is_diffuse(4))
        self.assertTrue(calculation_input.cloud_cover.is_diffuse(10))
        self.assertTrue(calculation_input.cloud_cover.is_diffuse(15))

        calculation_input = CalculationInput(
            InputParameters(0, Angstrom(0, 0), 0),
            File("uv/logic/test/uv_example"),
            File("dummy"),
            File("dummy"),
            File("dummy"),
            parameter_file_name=None,
        )

        self.assertTrue(isinstance(calculation_input.cloud_cover, DefaultCloudCover))
        self.assertFalse(calculation_input.cloud_cover.is_diffuse(4))
        self.assertFalse(calculation_input.cloud_cover.is_diffuse(10))
        self.assertFalse(calculation_input.cloud_cover.is_diffuse(15))
