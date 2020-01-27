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
from concurrent.futures.thread import ThreadPoolExecutor

from buvic.logic.warnings import warn, get_warnings, clear_warnings


class FileUtilsTestCase(unittest.TestCase):
    def test(self):
        clear_warnings()
        self._test_warnings()

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = []
            for _ in range(0, 8):
                results.append(pool.submit(self._test_warnings))
            for result in results:
                result.result(timeout=5)

    def _test_warnings(self) -> None:
        warn("warning 1")
        warn("warning 2")
        warn("warning 3")
        warnings = get_warnings()

        self.assertEqual(3, len(warnings))
        self.assertEqual("warning 1", warnings[0])
        self.assertEqual("warning 2", warnings[1])
        self.assertEqual("warning 3", warnings[2])

        clear_warnings()
        self.assertEqual(0, len(warnings))
