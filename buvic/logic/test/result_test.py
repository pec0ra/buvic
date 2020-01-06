import unittest
from datetime import date

from buvic.brewer_infos import StraylightCorrection
from buvic.logic.calculation_input import CalculationInput
from buvic.logic.file import File
from buvic.logic.result import Result, Spectrum
from buvic.logic.settings import Settings


class FileUtilsTestCase(unittest.TestCase):

    def test(self):
        result = Result(
            0,
            CalculationInput(
                "033",
                date(2019, 1, 1),
                Settings(),
                File("dummy"),
                File("dummy"),
                File("dummy"),
                File("dummy"),
                StraylightCorrection.UNDEFINED
            ),
            44.4,
            Spectrum([], [70], [], [], [], [])
        )
        name = result.get_name()
        self.assertEqual("0010110G.033", name)

        result = Result(
            0,
            CalculationInput(
                "033",
                date(2019, 1, 1),
                Settings(),
                File("path/to/dummy"),
                File("path/to/dummy"),
                File("dummy"),
                File("dummy"),
                StraylightCorrection.UNDEFINED
            ),
            44.4,
            Spectrum([], [70], [], [], [], [])
        )
        name = result.get_name()
        self.assertEqual("path/to/0010110G.033", name)

        result = Result(
            0,
            CalculationInput(
                "033",
                date(2019, 1, 1),
                Settings(),
                None,
                File("path/to/b/dummy"),
                File("dummy"),
                File("dummy"),
                StraylightCorrection.UNDEFINED
            ),
            44.4,
            Spectrum([], [70], [], [], [], [])
        )
        name = result.get_name()
        self.assertEqual("path/to/b/0010110G.033", name)

        result = Result(
            0,
            CalculationInput(
                "033",
                date(2019, 1, 1),
                Settings(),
                File("path/to/uv/dummy"),
                None,
                File("dummy"),
                File("dummy"),
                StraylightCorrection.UNDEFINED
            ),
            44.4,
            Spectrum([], [70], [], [], [], [])
        )
        name = result.get_name()
        self.assertEqual("path/to/uv/0010110G.033", name)

        result = Result(
            0,
            CalculationInput(
                "033",
                date(2019, 1, 1),
                Settings(),
                None,
                None,
                File("dummy"),
                File("dummy"),
                StraylightCorrection.UNDEFINED
            ),
            44.4,
            Spectrum([], [70], [], [], [], [])
        )
        name = result.get_name()
        self.assertEqual("033/2019/0010110G.033", name)
