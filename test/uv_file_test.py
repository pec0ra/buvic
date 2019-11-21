import unittest

from uv_file import RawUVFileHeader, RawUVValue


class UVFileReaderTestCase(unittest.TestCase):

    def test_header_parsing(self):
        h = RawUVFileHeader("ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo  "
                            "37.1 6.73 3 pr 1000dark 1.2")
        self.assertEqual(h.type, "ux")
        self.assertEqual(h.integration_time, 0.2294)
        self.assertEqual(h.dead_time, 0.000000031)
        self.assertEqual(h.cycles, 3)
        self.assertEqual(h.date.day, 20)
        self.assertEqual(h.date.month, 2)
        self.assertEqual(h.date.year, 17)
        self.assertEqual(h.day_of_year, 51)
        self.assertEqual(h.place, "Arenosillo")
        self.assertEqual(h.position[0], 37.1)
        self.assertEqual(h.position[1], 6.73)
        self.assertEqual(h.temperature, 3)
        self.assertEqual(h.pressure, 1000)
        self.assertEqual(h.dark, 1.2)

        # Single space after place
        h = RawUVFileHeader("ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo "
                            "37.1 6.73 3 pr 1000dark 1.2")
        self.assertEqual(h.place, "Arenosillo")

        # Double space before place
        h = RawUVFileHeader("ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17  Arenosillo "
                            "37.1 6.73 3 pr 1000dark 1.2")
        self.assertEqual(h.place, "Arenosillo")

        # Double space before and after place
        h = RawUVFileHeader("ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17  Arenosillo  "
                            "37.1 6.73 3 pr 1000dark 1.2")
        self.assertEqual(h.place, "Arenosillo")

        # Scientific notation
        RawUVFileHeader("ux Integration time is 3.1E-08 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo  "
                        "3.1E-08 3.1E-08 3 pr 1000dark 3.1E-08")

        # Two words place
        h = RawUVFileHeader("ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Davos Dorf  "
                            "37.1 6.73 3 pr 1000dark 1.2")
        self.assertEqual(h.place, "Davos Dorf")

        # Two words place with single space after
        h = RawUVFileHeader("ux Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Davos Dorf "
                            "37.1 6.73 3 pr 1000dark 1.2")
        self.assertEqual(h.place, "Davos Dorf")

        # Space between pr and dark
        h = RawUVFileHeader("ux Integration time is 0.2294 seconds per sample dt 0.000000031 cy 3 dh 20 02 17 "
                            "Arenosillo  37.1 6.73 3 pr 44 dark 1.2")
        self.assertEqual(h.pressure, 44)

    def test_header_failures(self):
        # Three letter type
        with self.assertRaises(ValueError):
            RawUVFileHeader("uvx Integration time is 0.2294 seconds per sample dt 3.1E-08 cy 3 dh 20 02 17 Arenosillo  "
                            "37.1 6.73 3 pr 1000dark 1.2")

    def test_value_parsing(self):

        v = RawUVValue("0 0 0 0")
        self.assertEqual(v.time, 0)
        self.assertEqual(v.wavelength, 0)
        self.assertEqual(v.step, 0)
        self.assertEqual(v.events, 0)
        self.assertEqual(v.std, 0)

        v = RawUVValue("3.1E-08 3.1E-08 44444444 3.1E-08")
        self.assertEqual(v.time, 0.000000031)
        self.assertEqual(v.wavelength, 0.000000031)
        self.assertEqual(v.step, 44444444)
        self.assertEqual(v.events, 0.000000031)
        self.assertAlmostEqual(v.std, 5679.618342471, 9)

        v = RawUVValue("123.4567 0.0043 1 40000.0")
        self.assertEqual(v.time, 123.4567)
        self.assertEqual(v.wavelength, 0.0043)
        self.assertEqual(v.step, 1)
        self.assertEqual(v.events, 40000)
        self.assertEqual(v.std, 0.005)
