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
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from logging import getLogger
from os import listdir, makedirs, path
from os.path import join, exists, isdir
from time import time
from typing import Dict, List, Tuple, Callable, Match, Optional

from buvic.logic.calculation_input import CalculationInput
from buvic.logic.file import File
from buvic.logic.settings import Settings, DataSource
from buvic.logic.utils import days_to_date, date_range, date_to_days

LOG = getLogger(__name__)


class FileUtils:
    UV_FILE_NAME_REGEX = re.compile(r"UV(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)")
    B_FILE_NAME_REGEX = re.compile(r"B(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)")
    ARF_FILE_NAME_REGEX = re.compile(r"arf_[a-zA-Z]*(?P<brewer_id>\d+)\.dat")
    UVR_FILE_NAME_REGEX = re.compile(r"(:?UVR|uvr)\S+\.(?P<brewer_id>\d+)")
    PARAMETER_FILE_NAME_REGEX = re.compile(r"par_(?P<year>\d{2})\.(?P<brewer_id>\d+)")

    _instr_dir: str
    _uvdata_dir: str
    _file_dict: Dict[str, InstrumentFiles]

    def __init__(self, input_dir: str):
        self._instr_dir = join(input_dir, "instr")
        self._uvdata_dir = join(input_dir, "uvdata")

    def refresh(self, remove_empty=True) -> None:
        """
        Scan the files to find all relevant files

        :param remove_empty: If set to true, will ignore brewer ids without UVR nor UV files
        """

        start_time = time()
        self._file_dict = {}

        if not exists(self._instr_dir):
            makedirs(self._instr_dir)
        if not exists(self._uvdata_dir):
            makedirs(self._uvdata_dir)

        self._find_files_recursive(self._instr_dir)
        self._find_files_recursive(self._uvdata_dir)

        if remove_empty:
            for brewer_id, instrument_files in list(self._file_dict.items()):
                if len(instrument_files.uvr_files) == 0:
                    # Remove the instruments without UVR files
                    LOG.warning(f"No UVR file exists for brewer id {brewer_id}, skipping")
                    del self._file_dict[brewer_id]
                elif len(instrument_files.uv_files) == 0:
                    # Remove the instruments without UV files
                    LOG.warning(f"No UV file exists for brewer id {brewer_id}, skipping")
                    del self._file_dict[brewer_id]
        LOG.info(f"Scanned files in {time() - start_time}ms")

    def get_calculation_inputs_between(
        self, start_date: date, end_date: date, brewer_id, settings: Settings, uvr_file: Optional[str] = None
    ) -> List[CalculationInput]:
        """
        Create inputs for all UV Files found for between a start date and an end date for a given brewer id.

        :param start_date: the dates' lower bound (inclusive) for the measurements
        :param end_date: the dates' upper bound (inclusive) for the measurements
        :param brewer_id: the id of the brewer instrument
        :param settings: the settings to use for the calculation
        :param uvr_file: the uvr file to use for the calculation or None to use the default
        :return: the calculation inputs
        """

        if uvr_file is None and settings.uvr_data_source == DataSource.FILES and brewer_id in self._file_dict:
            uvr_file = self._file_dict[brewer_id].uvr_files[0].file_name

        input_list = []
        for d in date_range(start_date, end_date):
            year = d.year - 2000
            days = date_to_days(d)

            LOG.debug("Creating input for date %s as days %d and year %d", d.isoformat(), days, year)
            calculation_input = self.input_from_files(f"{days:03}", f"{year:02}", brewer_id, settings, uvr_file)
            if calculation_input is not None:
                input_list.append(calculation_input)

        return input_list

    def get_calculation_inputs(self, settings: Settings) -> List[CalculationInput]:
        """
        Create inputs for all UV Files found in a given directory.

        :param settings: the settings to use for the calculation
        :return: the calculation inputs
        """

        input_list = []
        for brewer_id in self._file_dict:
            files = self._file_dict[brewer_id]
            for file in files.uv_files:
                res = re.match(self.UV_FILE_NAME_REGEX, file.file_name)
                if res is None:
                    raise ValueError(f"Unknown UV file name {file.file_name}")
                year = int(res.group("year"))
                days = res.group("days")

                uvr_file = files.uvr_files[0].file_name

                calculation_input = self.input_from_files(f"{days}", f"{year:02}", brewer_id, settings, uvr_file)
                if calculation_input is not None:
                    LOG.debug("Creating input for %s", file.file_name)
                    input_list.append(calculation_input)

        return input_list

    def input_from_files(
        self, days: str, year: str, brewer_id: str, settings: Settings, uvr_file: Optional[str] = None
    ) -> Optional[CalculationInput]:
        """
        Create calculation inputs for a given date given as days since new year and the year, for a given brewer id, for given settings
        and for a given uvr file name.

        This looks for registered files matching the date and brewer id and uvr file name. If no UV file matches, None is returned

        :param days: the days since new year
        :param year: the year
        :param brewer_id: the id of the brewer instrument
        :param settings: the parameter to pass in the input
        :param uvr_file: the name of the uvr file
        :return: a calculation input or None if no corresponding file was found
        """

        if settings.uv_data_source == DataSource.FILES:
            uv_file = self.get_uv_file(brewer_id, f"UV{days}{year}.{brewer_id}")
            if uv_file is None:
                return None
        else:
            uv_file = None

        b_file = self.get_b_file(brewer_id, f"B{days}{year}.{brewer_id}")

        arf_file = self.get_arf_file(brewer_id)

        if settings.uvr_data_source == DataSource.FILES:
            if uvr_file is None:
                raise ValueError("UVR file should not be None when the data source is FILES")
            calibration_file: Optional[File] = self.get_uvr_file(brewer_id, uvr_file)
        else:
            calibration_file = None

        parameter_file = self.get_parameter_file(brewer_id, year)

        return CalculationInput(
            brewer_id,
            days_to_date(int(days), int(year)),
            settings,
            uv_file,
            b_file,
            calibration_file,
            arf_file,
            parameter_file_name=parameter_file,
        )

    def handle_file(self, file_path) -> bool:
        """
        Find the type of the given file and add it to the corresponding list
        :param file_path: the file to add
        :return: whether the file is a "uvdata" file
        """

        file_name = path.basename(file_path)

        res = re.match(self.UV_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.debug(f"Matched UV file {file_path}")
            self._match_file(file_path, res, self._uvdata_dir, lambda i: i.uv_files)
            return True

        res = re.match(self.B_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.debug(f"Matched B file {file_path}")
            self._match_file(file_path, res, self._uvdata_dir, lambda i: i.b_files)
            return True

        res = re.match(self.UVR_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.debug(f"Matched UVR file {file_path}")
            self._match_file(file_path, res, self._instr_dir, lambda i: i.uvr_files)
            return False

        res = re.match(self.ARF_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.debug(f"Matched ARF file {file_path}")
            self._match_arf_file(file_path, res)
            return False

        res = re.match(self.PARAMETER_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.debug(f"Matched parameter file {file_path}")
            self._match_file(file_path, res, self._instr_dir, lambda i: i.parameter_files)
            return False

        LOG.info(f"Found an unknown file type: {file_path}")
        return False

    def untrack_file(self, file_path) -> None:
        """
        Remove a given file from the lists
        :param file_path: the file to untrack
        """

        file_name = path.basename(file_path)

        res = re.match(self.UV_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.info(f"Matched UV file to remove {file_path}")
            self._untrack_file(file_path, res, lambda i: i.uv_files)
            return

        res = re.match(self.B_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.info(f"Matched B file to remove {file_path}")
            self._untrack_file(file_path, res, lambda i: i.b_files)
            return

        res = re.match(self.UVR_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.info(f"Matched UVR file to remove {file_path}")
            self._untrack_file(file_path, res, lambda i: i.uvr_files)
            return

        res = re.match(self.ARF_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.info(f"Matched ARF file to remove {file_path}")
            self._untrack_arf_file(file_path, res)
            return

        res = re.match(self.PARAMETER_FILE_NAME_REGEX, file_name)
        if res is not None:
            LOG.info(f"Matched parameter file to remove {file_path}")
            self._untrack_file(file_path, res, lambda i: i.parameter_files)
            return

        LOG.info(f"Found an unknown file type: {file_path}")
        return

    def _find_files_recursive(self, directory: str) -> None:
        """
        Recursively search in a given directory for all files and add them to their corresponding lists.

        :param directory: the directory to search for the files in
        """
        for file_name in listdir(directory):
            file_path = join(directory, file_name)
            if isdir(file_path):
                self._find_files_recursive(file_path)
            else:
                self.handle_file(file_path)

    def _match_arf_file(self, file_path: str, res: Match[str]) -> None:
        """
        Action to perform on matched arf files.

        See `_find_file_recursive`
        :param file_path: the path of the matched file
        :param res: the result of the regex match
        """
        brewer_id: str = res.group("brewer_id")

        if brewer_id not in self._file_dict:
            self._file_dict[brewer_id] = InstrumentFiles(None)

        if self._file_dict[brewer_id].arf_file is not None:
            raise ValueError(f"Multiple ARF files found for brewer with id {brewer_id}.")

        self._file_dict[brewer_id].arf_file = File(file_path, self._uvdata_dir)

    def _match_file(self, file_path: str, res: Match[str], parent_dir: str, field_getter: Callable[[InstrumentFiles], List[File]]) -> None:
        """
        Action to perform when on matched files.

        This adds the file to one of the list of files from an InstrumentFile. The correct list is retrieved with a given getter.

        See `_find_file_recursive`
        :param file_path: the path of the matched file
        :param res: the result of the regex match
        :param parent_dir: the root directory of the search
        :param field_getter: a function to apply on an InstrumentFile to get the list of files of the correct type
        """
        brewer_id = res.group("brewer_id")

        if brewer_id not in self._file_dict:
            self._file_dict[brewer_id] = InstrumentFiles(None)

        field_getter(self._file_dict[brewer_id]).append(File(file_path, parent_dir))

    def _untrack_file(self, file_path: str, res: Match[str], field_getter: Callable[[InstrumentFiles], List[File]]) -> None:
        """
        Remove a given file.

        This from the relevant list of files from an InstrumentFile. The correct list is retrieved with a given getter.

        See `_find_file_recursive`
        :param file_path: the path of the file
        :param res: the result of the regex match
        :param field_getter: a function to apply on an InstrumentFile to get the list of files of the correct type
        """
        brewer_id = res.group("brewer_id")

        if brewer_id not in self._file_dict:
            LOG.warning(f"Trying to remove a file for an unknown brewer: {file_path}")
            return

        LOG.info(f"Removing file {file_path}")
        file_list = field_getter(self._file_dict[brewer_id])
        file = next((file for file in file_list if file.full_path == file_path), None)
        if file is not None:
            file_list.remove(file)

    def _untrack_arf_file(self, file_path: str, res: Match[str]) -> None:
        """
        Remove a given arf files.

        :param file_path: the path of the file
        :param res: the result of the regex match
        """
        brewer_id: str = res.group("brewer_id")

        if brewer_id not in self._file_dict:
            LOG.warning(f"Trying to remove an arf file for an unknown brewer: {file_path}")
            return

        self._file_dict[brewer_id].arf_file = None

    def get_brewer_ids(self) -> List[str]:
        """
        Get the alphabetically sorted list of brewer ids
        :return: the list of ids
        """
        return sorted(self._file_dict.keys())

    def get_uvr_files(self, brewer_id: str) -> List[File]:
        """
        Get the list of all uvr files for a given brewer id, alphabetically sorted by file name
        :param brewer_id: the id of the brewer instrument to get the uvr files from
        :return: the list of files
        """
        if brewer_id is None:
            return []
        if brewer_id not in self._file_dict:
            raise ValueError(f"No uvr file found for brewer id {brewer_id}.")
        return sorted(self._file_dict[brewer_id].uvr_files, key=lambda f: f.file_name)

    def get_uv_file(self, brewer_id, uv_file_name: str) -> Optional[File]:
        """
        Search if a uv file for a given brewer id and with the given name exists and return it if it exists or None otherwise

        Note that the brewer id is included in the file name and therefore wouldn't be necessary to pass as parameter. However, we still
        pass it for simplicity and performance reasons.
        :param brewer_id: the id of the brewer to get the file for
        :param uv_file_name: the name of the file
        :return: the file if found, None otherwise
        """
        return self._get_file(brewer_id, uv_file_name, lambda i: i.uv_files)

    def get_b_file(self, brewer_id, b_file_name: str) -> Optional[File]:
        """
        Search if a b file for a given brewer id and with the given name exists and return it if it exists or None otherwise

        Note that the brewer id is included in the file name and therefore wouldn't be necessary to pass as parameter. However, we still
        pass it for simplicity and performance reasons.
        :param brewer_id: the id of the brewer to get the file for
        :param b_file_name: the name of the file
        :return: the file if found, None otherwise
        """
        return self._get_file(brewer_id, b_file_name, lambda i: i.b_files)

    def get_uvr_file(self, brewer_id, uvr_file_name: str) -> File:
        """
        Search if a uvr file for a given brewer id and with the given name exists and return it.

        A ValueError is raised if the file is not found

        Note that the brewer id is included in the file name and therefore wouldn't be necessary to pass as parameter. However, we still
        pass it for simplicity and performance reasons.
        :param brewer_id: the id of the brewer to get the file for
        :param uvr_file_name: the name of the file
        :return: the file
        """
        file = self._get_file(brewer_id, uvr_file_name, lambda i: i.uvr_files)
        if file is None:
            raise ValueError(f"UVR file {uvr_file_name} does not exist for brewer {brewer_id}")
        return file

    def get_arf_file(self, brewer_id: str) -> Optional[File]:
        """
        Search if a arf file exists for a given brewer id and return it if it exists or None otherwise.

        :param brewer_id: the id of the brewer to get the file for
        :return: the file if found, None otherwise
        """
        if brewer_id is None or brewer_id not in self._file_dict:
            return None
        return self._file_dict[brewer_id].arf_file

    def get_parameter_file(self, brewer_id: str, year: str) -> Optional[File]:
        """
        Search if a parameter file exists for given brewer id and year and return it if it exists or None otherwise

        :param brewer_id: the id of the brewer to get the file for
        :param year: the year to get the file for
        :return: the file if found, None otherwise
        """
        try:
            if brewer_id is None or brewer_id not in self._file_dict:
                return None
            parameter_files = self._file_dict[brewer_id].parameter_files
            parameter_file_name = f"par_{year[-2:]}.{brewer_id}"
            return next(file for file in parameter_files if file.file_name == parameter_file_name)
        except StopIteration:
            return None

    def _get_file(self, brewer_id: str, file_name: str, field_getter: Callable[[InstrumentFiles], List[File]]) -> Optional[File]:
        """
        Search if a file for a given brewer id and with the given name exists and return it if it exists or None otherwise.
        The relevant list in InstrumentFile to search the file in is accessed with a given getter

        :param brewer_id: the id of the brewer to get the file for
        :param file_name: the name of the file
        :param field_getter: the function to call to get the list in InstrumentFile to search the file in
        :return: the file if found, None otherwise
        """
        if brewer_id is None or brewer_id not in self._file_dict:
            return None
        try:
            return next(file for file in field_getter(self._file_dict[brewer_id]) if file.file_name == file_name)
        except StopIteration:
            return None

    def get_date_range(self, brewer_id: str) -> Tuple[date, date]:
        """
        Get the date range for which UV files are available for a given brewer id.

        If no UV file is available, the range 2000-01-01 to today is returned.
        :param brewer_id: the id to get the range for
        :return: the start date and end date of the range
        """
        min_date: Optional[date] = None
        max_date: Optional[date] = None

        if brewer_id is None:
            return date(2000, 1, 1), date.today()

        if brewer_id not in self._file_dict:
            raise ValueError(f"Brewer with id {brewer_id} is not present in the list of files.")

        for uv_file in self._file_dict[brewer_id].uv_files:
            res = re.match(self.UV_FILE_NAME_REGEX, uv_file.file_name)
            if res is None:
                raise ValueError("Invalid UV file format found")

            days = res.group("days")
            year = res.group("year")
            file_date = days_to_date(int(days), int(year))
            if min_date is None or min_date > file_date:
                min_date = file_date
            if max_date is None or max_date < file_date:
                max_date = file_date

        if min_date is None:
            min_date = date(2000, 1, 1)

        if max_date is None:
            max_date = date.today()

        return min_date, max_date


@dataclass
class InstrumentFiles:
    """The arf, uvr, uv, b and parameter files for one brewer instrument"""

    arf_file: Optional[File]
    uvr_files: List[File] = field(default_factory=list)
    uv_files: List[File] = field(default_factory=list)
    b_files: List[File] = field(default_factory=list)
    parameter_files: List[File] = field(default_factory=list)
