from __future__ import annotations

from os.path import join, relpath, dirname, basename


class File:
    """
    An object representing a file
    """

    # The path to the file, relative to its root container directory (`uvdata` or `instr` - exclusive)
    path: str

    # The name of the file
    file_name: str

    # The path of the file, relative to the working directory
    full_path: str

    def __init__(self, full_path: str, start_path: str = "") -> None:
        self.path = dirname(relpath(full_path, start=start_path))
        self.file_name = basename(full_path)
        self.full_path = full_path

    def __str__(self):
        return join(self.path, self.file_name)

    def __repr__(self):
        return join(self.path, self.file_name)
