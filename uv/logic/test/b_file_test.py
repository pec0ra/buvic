import unittest

from uv.logic.b_file import Ozone


class UVFileReaderTestCase(unittest.TestCase):

    def test_interpolation(self):
        ozone = Ozone(
            [10, 12, 14],
            [300, 320, 350]
        )

        self.assertEqual(300, ozone.interpolated_value(10, 200))
        self.assertEqual(300, ozone.interpolated_value(9, 200))
        self.assertEqual(300, ozone.interpolated_value(11, 200))
        self.assertEqual(300, ozone.interpolated_value(0, 200))

        self.assertEqual(320, ozone.interpolated_value(11.0001, 200))
        self.assertEqual(320, ozone.interpolated_value(12, 200))
        self.assertEqual(320, ozone.interpolated_value(13, 200))

        self.assertEqual(350, ozone.interpolated_value(13.0001, 200))
        self.assertEqual(350, ozone.interpolated_value(14, 200))
        self.assertEqual(350, ozone.interpolated_value(15, 200))
        self.assertEqual(350, ozone.interpolated_value(100, 200))

        ozone = Ozone(
            [],
            []
        )

        self.assertEqual(200, ozone.interpolated_value(0, 200))
        self.assertEqual(200, ozone.interpolated_value(10, 200))
        self.assertEqual(200, ozone.interpolated_value(100, 200))
        self.assertEqual(200, ozone.interpolated_value(1000, 200))
