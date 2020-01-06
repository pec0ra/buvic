import unittest
from datetime import date

from buvic.logic.file import File
from buvic.logic.file_utils import FileUtils, InstrumentFiles
from buvic.logic.settings import Settings


class FileUtilsTestCase(unittest.TestCase):

    def test(self):
        file_utils = FileUtils("buvic/logic/test/")
        self.assertEqual(0, len(file_utils.get_calculation_inputs_between(date(2010, 1, 1), date(2020, 1, 1), "033", Settings())))
        self.assertEqual(0, len(file_utils.get_calculation_inputs(Settings())))

        file_utils._file_dict["033"] = InstrumentFiles(
            None,
            [File("UVR00119.033"), File("UVR00219.033")],
            [File("UV00119.033"), File("UV00219.033"), File("UV00319.033"), File("UV00419.033")],
            [File("B00119.033"), File("B00219.033"), File("B00319.033"), File("B00419.033"), File("B00519.033")]
        )

        file_utils._file_dict["070"] = InstrumentFiles(
            None,
            [File("UVR00119.070")],
            [File("UV00119.070")],
            [File("B00119.070")]
        )

        self.assertEqual(4, len(file_utils.get_calculation_inputs_between(date(2010, 1, 1), date(2020, 1, 1), "033", Settings())))
        self.assertEqual(2, len(file_utils.get_calculation_inputs_between(date(2019, 1, 1), date(2019, 1, 2), "033", Settings())))
        self.assertEqual(2, len(file_utils.get_calculation_inputs_between(date(2019, 1, 3), date(2019, 1, 4), "033", Settings())))
        self.assertEqual(2, len(file_utils.get_calculation_inputs_between(date(2019, 1, 3), date(2019, 1, 5), "033", Settings())))
        self.assertEqual(5, len(file_utils.get_calculation_inputs(Settings())))

        self.assertEqual(["033", "070"], file_utils.get_brewer_ids())

        self.assertEqual(["UVR00119.033", "UVR00219.033"], [u.file_name for u in file_utils.get_uvr_files("033")])
        self.assertEqual(["UVR00119.070"], [u.file_name for u in file_utils.get_uvr_files("070")])

        date_start, date_end = file_utils.get_date_range("033")
        self.assertEqual(1, date_start.day)
        self.assertEqual(1, date_start.month)
        self.assertEqual(2019, date_start.year)

        self.assertEqual(4, date_end.day)
        self.assertEqual(1, date_end.month)
        self.assertEqual(2019, date_end.year)
