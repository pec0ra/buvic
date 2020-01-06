import unittest

from buvic.logic.file import File


class FileUtilsTestCase(unittest.TestCase):

    def test(self):
        file = File("full/path/to/file.txt")
        self.assertEqual("full/path/to/file.txt", file.full_path)
        self.assertEqual("file.txt", file.file_name)
        self.assertEqual("full/path/to", file.path)

        file = File("full/path/to/file.txt", "full")
        self.assertEqual("full/path/to/file.txt", file.full_path)
        self.assertEqual("file.txt", file.file_name)
        self.assertEqual("path/to", file.path)

        file = File("full/path/to/file.txt", "full/path/")
        self.assertEqual("full/path/to/file.txt", file.full_path)
        self.assertEqual("file.txt", file.file_name)
        self.assertEqual("to", file.path)
