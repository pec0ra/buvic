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
from datetime import date

from buvic.logic.brewer_infos import StraylightCorrection
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
