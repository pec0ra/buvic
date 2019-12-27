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
