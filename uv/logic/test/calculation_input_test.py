import logging
import unittest

from uv.logic.calculation_input import CalculationInput, InputParameters
from uv.logutils import init_logging


class UVFileReaderTestCase(unittest.TestCase):

    def test_cache(self):
        init_logging(logging.DEBUG)

        calculation_input = CalculationInput(
            InputParameters(0, 0, 0),
            "dummy",
            "dummy",
            "uv/logic/test/calibration_example",
            "dummy",
        )

        c = calculation_input.calibration

        calculation_input.calibration_file_name = "does_not_exist"
        # No exception is thrown since the calibration value used is cached
        c = calculation_input.calibration
