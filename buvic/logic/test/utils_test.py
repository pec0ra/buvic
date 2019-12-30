import unittest
from datetime import date, time

from buvic.logic.utils import days_to_date, date_to_days, minutes_to_time, time_to_minutes


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
