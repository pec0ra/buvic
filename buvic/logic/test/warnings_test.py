import unittest
from concurrent.futures.thread import ThreadPoolExecutor

from buvic.logic.warnings import warn, get_warnings, clear_warnings


class FileUtilsTestCase(unittest.TestCase):

    def test(self):
        clear_warnings()
        self._test_warnings()

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = []
            for i in range(0, 8):
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
