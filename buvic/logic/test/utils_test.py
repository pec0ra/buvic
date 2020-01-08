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
from datetime import date, time

from buvic.logic.utils import days_to_date, date_to_days, minutes_to_time, time_to_minutes, name_to_date_and_brewer_id


class UtilsTestCase(unittest.TestCase):

    def test_days_to_date(self):
        d = days_to_date(1, 2019)
        self.assertEqual(d.year, 2019)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 1)

        d = days_to_date(1, 19)
        self.assertEqual(d.year, 2019)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 1)

        d = days_to_date(365, 19)
        self.assertEqual(d.year, 2019)
        self.assertEqual(d.month, 12)
        self.assertEqual(d.day, 31)

        d = days_to_date(71, 19)
        self.assertEqual(d.year, 2019)
        self.assertEqual(d.month, 3)
        self.assertEqual(d.day, 12)

        with self.assertRaises(ValueError):
            days_to_date(0, 19)

        with self.assertRaises(ValueError):
            days_to_date(367, 19)

    def test_date_to_days(self):
        days = date_to_days(date(2019, 1, 1))
        self.assertEqual(days, 1)

        days = date_to_days(date(19, 1, 1))
        self.assertEqual(days, 1)

        days = date_to_days(date(19, 12, 31))
        self.assertEqual(days, 365)

        days = date_to_days(date(19, 3, 12))
        self.assertEqual(days, 71)

    def test_minutes_to_time(self):
        t = minutes_to_time(0)
        self.assertEqual(t.hour, 0)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)

        t = minutes_to_time(0.5)
        self.assertEqual(t.hour, 0)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 30)

        t = minutes_to_time(30)
        self.assertEqual(t.hour, 0)
        self.assertEqual(t.minute, 30)
        self.assertEqual(t.second, 0)

        t = minutes_to_time(30.5)
        self.assertEqual(t.hour, 0)
        self.assertEqual(t.minute, 30)
        self.assertEqual(t.second, 30)

        t = minutes_to_time(59)
        self.assertEqual(t.hour, 0)
        self.assertEqual(t.minute, 59)
        self.assertEqual(t.second, 0)

        t = minutes_to_time(60)
        self.assertEqual(t.hour, 1)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)

        t = minutes_to_time(1439)
        self.assertEqual(t.hour, 23)
        self.assertEqual(t.minute, 59)
        self.assertEqual(t.second, 0)

        t = minutes_to_time(1439.5)
        self.assertEqual(t.hour, 23)
        self.assertEqual(t.minute, 59)
        self.assertEqual(t.second, 30)

    def test_time_to_minutes(self):
        minutes = time_to_minutes(time(0, 0, 0))
        self.assertEqual(minutes, 0)

        minutes = time_to_minutes(time(0, 0, 30))
        self.assertEqual(minutes, 0.5)

        minutes = time_to_minutes(time(0, 1, 0))
        self.assertEqual(minutes, 1)

        minutes = time_to_minutes(time(1, 0, 0))
        self.assertEqual(minutes, 60)

        minutes = time_to_minutes(time(1, 0, 30))
        self.assertEqual(minutes, 60.5)

        minutes = time_to_minutes(time(23, 59, 30))
        self.assertEqual(minutes, 1439.5)

    def test_name_to_date_and_brewer_id(self):
        d, brewer_id = name_to_date_and_brewer_id("UV00119.033")
        self.assertEqual(1, d.day)
        self.assertEqual(1, d.month)
        self.assertEqual(2019, d.year)
        self.assertEqual("033", brewer_id)

        d, brewer_id = name_to_date_and_brewer_id("UV36519.033")
        self.assertEqual(31, d.day)
        self.assertEqual(12, d.month)
        self.assertEqual(2019, d.year)
        self.assertEqual("033", brewer_id)

        d, brewer_id = name_to_date_and_brewer_id("B00119.033")
        self.assertEqual(1, d.day)
        self.assertEqual(1, d.month)
        self.assertEqual(2019, d.year)
        self.assertEqual("033", brewer_id)

        d, brewer_id = name_to_date_and_brewer_id("B36519.033")
        self.assertEqual(31, d.day)
        self.assertEqual(12, d.month)
        self.assertEqual(2019, d.year)
        self.assertEqual("033", brewer_id)

        with self.assertRaises(ValueError):
            # Day too big
            name_to_date_and_brewer_id("B36719.033")

        with self.assertRaises(ValueError):
            # Day too small
            name_to_date_and_brewer_id("B00019.033")

        # Wrong patterns
        with self.assertRaises(ValueError):
            name_to_date_and_brewer_id("00119.033")
        with self.assertRaises(ValueError):
            name_to_date_and_brewer_id("UV00119.03")
        with self.assertRaises(ValueError):
            name_to_date_and_brewer_id("UV0011.033")
