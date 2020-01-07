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

from buvic.logic.ozone import Ozone


class UVFileReaderTestCase(unittest.TestCase):

    def test_interpolation(self):
        ozone = Ozone(
            [10, 12, 14],
            [300, 320, 350]
        )

        self.assertEqual(300, ozone.interpolated_ozone(10, 200))
        self.assertEqual(300, ozone.interpolated_ozone(9, 200))
        self.assertEqual(300, ozone.interpolated_ozone(11, 200))
        self.assertEqual(300, ozone.interpolated_ozone(0, 200))

        self.assertEqual(320, ozone.interpolated_ozone(11.0001, 200))
        self.assertEqual(320, ozone.interpolated_ozone(12, 200))
        self.assertEqual(320, ozone.interpolated_ozone(13, 200))

        self.assertEqual(350, ozone.interpolated_ozone(13.0001, 200))
        self.assertEqual(350, ozone.interpolated_ozone(14, 200))
        self.assertEqual(350, ozone.interpolated_ozone(15, 200))
        self.assertEqual(350, ozone.interpolated_ozone(100, 200))

        ozone = Ozone(
            [],
            []
        )

        self.assertEqual(200, ozone.interpolated_ozone(0, 200))
        self.assertEqual(200, ozone.interpolated_ozone(10, 200))
        self.assertEqual(200, ozone.interpolated_ozone(100, 200))
        self.assertEqual(200, ozone.interpolated_ozone(1000, 200))
