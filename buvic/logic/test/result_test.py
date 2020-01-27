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
from typing import Optional

from buvic.logic.calculation_input import CalculationInput
from buvic.logic.file import File
from buvic.logic.result import Result, Spectrum
from buvic.logic.settings import Settings


class ResultTestCase(unittest.TestCase):
    def test(self):
        self._test_paths("0010110G.033", File("dummy"), File("dummy"))

        self._test_paths("path/to/0010110G.033", File("path/to/dummy"), File("path/to/dummy"))
        self._test_paths("path/to/0010110G.033", File("path/to/uv/dummy"), File("path/to/b/dummy"))

        self._test_paths("nocoscor/path/to/0010110G.033", File("path/to/uv/dummy"), File("path/to/b/dummy"), no_coscor=True)

        self._test_paths("path/to/b/0010110G.033", None, File("path/to/b/dummy"))

        self._test_paths("path/to/uv/0010110G.033", File("path/to/uv/dummy"))

        self._test_paths("033/2019/0010110G.033")

    def _test_paths(self, expected_output_path: str, uv_file: Optional[File] = None, b_file: Optional[File] = None, **kwargs):
        result = Result(
            0,
            CalculationInput("033", date(2019, 1, 1), Settings(**kwargs), uv_file, b_file, File("dummy"), File("dummy"), None),
            44.4,
            0.0,
            0.0,
            Spectrum([], [70], [], [], [], []),
        )
        name = result.get_qasume_name()
        self.assertEqual(expected_output_path, name)
