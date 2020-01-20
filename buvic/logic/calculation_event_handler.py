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
import re
from logging import getLogger
from typing import Callable, List

from watchdog.events import FileSystemEventHandler, FileSystemMovedEvent, FileSystemEvent

from buvic.logic.calculation_input import CalculationInput
from buvic.logic.file_utils import FileUtils
from buvic.logic.result import Result
from buvic.logic.settings import Settings

LOG = getLogger(__name__)


class CalculationEventHandler(FileSystemEventHandler):
    DATE_AND_BREWER_REGEX = re.compile(r"(B|UV)(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)$")

    def __init__(self, input_dir: str, on_new_file: Callable[[CalculationInput], List[Result]], settings: Settings):
        self._on_new_file = on_new_file
        self._settings = settings
        self._file_utils = FileUtils(input_dir)
        self._file_utils.refresh(False)

    def on_modified(self, event):
        self._on_created_or_modified(event)

    def on_moved(self, event: FileSystemMovedEvent):
        self._on_created_or_modified(event)

    def on_deleted(self, event):
        self._file_utils.untrack_file(event.src_path)

    def _on_created_or_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return

        if isinstance(event, FileSystemMovedEvent):
            self._file_utils.untrack_file(event.src_path)
            file_path = event.dest_path
        else:
            file_path = event.src_path

        LOG.info("File matched for event " + type(event).__name__)
        try:
            self._handle_file(file_path)
        except Exception:
            LOG.error("An error occurred while handling file", exc_info=True)

    def _handle_file(self, file_path):
        # Add file to file utils
        must_calculate = self._file_utils.handle_file(file_path)
        if must_calculate:
            res = re.search(self.DATE_AND_BREWER_REGEX, file_path)
            if res is None:
                LOG.warning(f"Incorrect file name: {file_path}")
            else:
                brewer_id = res.group("brewer_id")
                uvr_files = self._file_utils.get_uvr_files(brewer_id)
                if len(uvr_files) == 0:
                    uvr_file_name = None
                else:
                    uvr_file_name = uvr_files[0].file_name
                calculation_input = self._file_utils.input_from_files(
                    res.group("days"), res.group("year"), brewer_id, self._settings, uvr_file_name
                )
                if calculation_input is not None:
                    self._on_new_file(calculation_input)
