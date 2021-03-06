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

from ..uv_file import UVFileHeader, RawUVValue, UVProvider


class UVFileReaderTestCase(unittest.TestCase):
    def test_header_parsing(self):
        h = UVFileHeader.from_header_line(
            "ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo  " "37.1 6.73 3 pr 1000dark 1.2"
        )
        self.assertEqual(h.type, "ux")
        self.assertEqual(h.integration_time, 0.2294)
        self.assertEqual(h.dead_time, 0.000000031)
        self.assertEqual(h.cycles, 3)
        self.assertEqual(h.date.day, 20)
        self.assertEqual(h.date.month, 2)
        self.assertEqual(h.date.year, 2017)
        self.assertEqual(h.place, "Arenosillo")
        self.assertEqual(h.position.latitude, 37.1)
        self.assertEqual(h.position.longitude, 6.73)
        self.assertEqual(h.temperature, -33.27 + 3 * 18.64)
        self.assertEqual(h.pressure, 1000)
        self.assertEqual(h.dark, 1.2)

        # Negative latitude / longitude
        h = UVFileHeader.from_header_line(
            "ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo " "-6.7828 -9.6754 3 pr 1000dark 1.2"
        )
        self.assertEqual(h.position.latitude, -6.7828)
        self.assertEqual(h.position.longitude, -9.6754)

        # Single space after place
        h = UVFileHeader.from_header_line(
            "ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo " "37.1 6.73 3 pr 1000dark 1.2"
        )
        self.assertEqual(h.place, "Arenosillo")

        # Double space before place
        h = UVFileHeader.from_header_line(
            "ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17  Arenosillo " "37.1 6.73 3 pr 1000dark 1.2"
        )
        self.assertEqual(h.place, "Arenosillo")

        # Double space before and after place
        h = UVFileHeader.from_header_line(
            "ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17  Arenosillo  " "37.1 6.73 3 pr 1000dark 1.2"
        )
        self.assertEqual(h.place, "Arenosillo")

        # Scientific notation
        UVFileHeader.from_header_line(
            "ux Integration time is 3.1E-08 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo  "
            "3.1E-08 3.1E-08 3 pr 1000dark 3.1E-08"
        )

        # Two words place
        h = UVFileHeader.from_header_line(
            "ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Davos Dorf  " "37.1 6.73 3 pr 1000dark 1.2"
        )
        self.assertEqual(h.place, "Davos Dorf")

        # Two words place with single space after
        h = UVFileHeader.from_header_line(
            "ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Davos Dorf " "37.1 6.73 3 pr 1000dark 1.2"
        )
        self.assertEqual(h.place, "Davos Dorf")

        # Space between pr and dark
        h = UVFileHeader.from_header_line(
            "ux Integration time is 0.2294 seconds per sample dt 0.000000031 cy 3 dh 20 02 17 " "Arenosillo  37.1 6.73 3 pr 44 dark 1.2"
        )
        self.assertEqual(h.pressure, 44)

    def test_header_failures(self):
        # Three letter type
        with self.assertRaises(ValueError):
            UVFileHeader.from_header_line(
                "uvx Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo  " "37.1 6.73 3 pr 1000dark 1.2"
            )

    def test_value_parsing(self):
        v = RawUVValue.from_value_line("0 0 0 0")
        self.assertEqual(v.time, 0)
        self.assertEqual(v.wavelength, 0)
        self.assertEqual(v.step, 0)
        self.assertEqual(v.events, 0)
        self.assertEqual(v.std, 0)

        v = RawUVValue.from_value_line("3.1E-08 3.1E-08 44444444 3.1E-08")
        self.assertEqual(v.time, 0.000000031)
        self.assertEqual(v.wavelength, 0.0000000031)
        self.assertEqual(v.step, 44444444)
        self.assertEqual(v.events, 0.000000031)
        self.assertAlmostEqual(v.std, 5679.618342471, 9)

        v = RawUVValue.from_value_line("123.4567 0.0043 1 40000.0")
        self.assertEqual(v.time, 123.4567)
        self.assertEqual(v.wavelength, 0.00043)
        self.assertEqual(v.step, 1)
        self.assertEqual(v.events, 40000)
        self.assertEqual(v.std, 0.005)

    def test_mean_of_duplicates(self):
        values = [
            RawUVValue(1, 0, 3, 3, 3),
            RawUVValue(3, 0, 1, 1, 1),
            RawUVValue(1, 1, 1, 1, 1),
            RawUVValue(2, 1, 3, 2, 2),
            RawUVValue(4, 2, 4, 4, 4),
            RawUVValue(6, 2, 6, 6, 6),
        ]
        new_values = UVProvider.mean_of_duplicates(values)
        self.assertEqual(3, len(new_values))

        self.assertEqual(0, new_values[0].wavelength)
        self.assertEqual(2, new_values[0].time)
        self.assertEqual(2, new_values[0].step)
        self.assertEqual(2, new_values[0].events)

        self.assertEqual(1, new_values[1].wavelength)
        self.assertEqual(1.5, new_values[1].time)
        self.assertEqual(2, new_values[1].step)
        self.assertEqual(1.5, new_values[1].events)

        self.assertEqual(2, new_values[2].wavelength)
        self.assertEqual(5, new_values[2].time)
        self.assertEqual(5, new_values[2].step)
        self.assertEqual(5, new_values[2].events)

        values = [
            RawUVValue(1, 0, 1, 1, 1),
            RawUVValue(2, 1, 2, 2, 2),
            RawUVValue(3, 2, 3, 3, 3),
        ]
        new_values = UVProvider.mean_of_duplicates(values)
        self.assertEqual(3, len(new_values))

        self.assertEqual(0, new_values[0].wavelength)
        self.assertEqual(1, new_values[0].time)
        self.assertEqual(1, new_values[0].step)
        self.assertEqual(1, new_values[0].events)
        self.assertEqual(1, new_values[0].std)

        self.assertEqual(1, new_values[1].wavelength)
        self.assertEqual(2, new_values[1].time)
        self.assertEqual(2, new_values[1].step)
        self.assertEqual(2, new_values[1].events)
        self.assertEqual(2, new_values[1].std)

        self.assertEqual(2, new_values[2].wavelength)
        self.assertEqual(3, new_values[2].time)
        self.assertEqual(3, new_values[2].step)
        self.assertEqual(3, new_values[2].events)
        self.assertEqual(3, new_values[2].std)
