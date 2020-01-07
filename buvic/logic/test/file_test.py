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
