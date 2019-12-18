from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from logging import getLogger
from os import listdir, makedirs
from os.path import join, exists, isdir
from pprint import PrettyPrinter
from typing import Dict, List, Tuple, Callable, Pattern, Match, Optional

from buvic.logic.calculation_input import InputParameters, CalculationInput
from buvic.logic.file import File
from buvic.logic.utils import days_to_date, date_range, date_to_days

LOG = getLogger(__name__)

pp = PrettyPrinter(indent=2)


class FileUtils:
    UV_FILE_NAME_REGEX = re.compile("UV(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)")
    B_FILE_NAME_REGEX = re.compile("B(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)")
    ARF_FILE_NAME_REGEX = re.compile("arf_[a-zA-Z]*(?P<brewer_id>\d+)\.dat")
    UVR_FILE_NAME_REGEX = re.compile("(:?UVR|uvr)\S+\.(?P<brewer_id>\d+)")
    PARAMETER_FILE_NAME_REGEX = re.compile("(?P<year>\d+)\.par")

    _instr_dir: str
    _uvdata_dir: str
    _file_dict: Dict[str, InstrumentFiles]
    _parameter_files: List[File]

    def __init__(self, input_dir: str):
        self._instr_dir = join(input_dir, "instr")
        self._uvdata_dir = join(input_dir, "uvdata")
        self.refresh()

    def refresh(self) -> None:
        """
        Scan the files to find all relevant files
        """

        self._file_dict = {}
        self._parameter_files = []

        if not exists(self._instr_dir):
            makedirs(self._instr_dir)
        if not exists(self._uvdata_dir):
            makedirs(self._uvdata_dir)

        # Find all arf files
        self._find_file_recursive(
            self._instr_dir,
            self.ARF_FILE_NAME_REGEX,
            self._match_arf_file
        )

        # Find all uvr files
        self._find_file_recursive(
            self._instr_dir,
            self.UVR_FILE_NAME_REGEX,
            lambda file_path, res: self._match_file(file_path, res, self._instr_dir, lambda i: i.uvr_files)
        )

        # Find all uv files
        self._find_file_recursive(
            self._uvdata_dir,
            self.UV_FILE_NAME_REGEX,
            lambda file_path, res: self._match_file(file_path, res, self._uvdata_dir, lambda i: i.uv_files)
        )

        # Find all b files
        self._find_file_recursive(
            self._uvdata_dir,
            self.B_FILE_NAME_REGEX,
            lambda file_path, res: self._match_file(file_path, res, self._uvdata_dir, lambda i: i.b_files)
        )

        # Find all parameter files
        self._find_file_recursive(
            self._instr_dir,
            self.PARAMETER_FILE_NAME_REGEX,
            self._match_parameter_file
        )

        for brewer_id, instrument_files in list(self._file_dict.items()):
            if len(instrument_files.uvr_files) == 0:
                # Remove the instruments without UVR files
                LOG.warning(f"No UVR file exists for brewer id {brewer_id}, skipping")
                del self._file_dict[brewer_id]
            elif len(instrument_files.uv_files) == 0:
                # Remove the instruments without UV files
                LOG.warning(f"No UV file exists for brewer id {brewer_id}, skipping")
                del self._file_dict[brewer_id]

    def get_calculation_inputs_between(self, start_date: date, end_date: date, brewer_id, parameters: InputParameters,
                                       uvr_file: Optional[str] = None) -> List[CalculationInput]:
        """
        Create inputs for all UV Files found for between a start date and an end date for a given brewer id.

        :param start_date: the dates' lower bound (inclusive) for the measurements
        :param end_date: the dates' upper bound (inclusive) for the measurements
        :param brewer_id: the id of the brewer instrument
        :param parameters: the parameters to use for the calculation
        :param uvr_file: the uvr file to use for the calculation or None to use the default
        :return: the calculation inputs
        """

        if uvr_file is None:
            uvr_file = self._file_dict[brewer_id].uvr_files[0].file_name

        input_list = []
        for d in date_range(start_date, end_date):
            year = d.year - 2000
            days = date_to_days(d)

            LOG.debug("Creating input for date %s as days %d and year %d", d.isoformat(), days, year)
            calculation_input = self._input_from_files(f"{days:03}", f"{year:02}", brewer_id, parameters, uvr_file)
            if calculation_input is not None:
                input_list.append(calculation_input)

        return input_list

    def get_calculation_inputs(self, parameters: InputParameters) -> List[CalculationInput]:
        """
        Create inputs for all UV Files found in a given directory.

        :param parameters: the parameters to use for the calculation
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

                calculation_input = self._input_from_files(f"{days}", f"{year:02}", brewer_id, parameters, uvr_file)
                if calculation_input is not None:
                    LOG.debug("Creating input for %s", file.file_name)
                    input_list.append(calculation_input)

        return input_list

    def _input_from_files(
            self,
            days: str,
            year: str,
            brewer_id: str,
            parameters: InputParameters,
            uvr_file: str
    ) -> Optional[CalculationInput]:
        """
        Create calculation inputs for a given date given as days since new year and the year, for a given brewer id, for given parameters
        and for a given uvr file name.

        This looks for registered files matching the date and brewer id and uvr file name. If no UV file matches, None is returned

        :param days: the days since new year
        :param year: the year
        :param brewer_id: the id of the brewer instrument
        :param parameters: the parameter to pass in the input
        :param uvr_file: the name of the uvr file
        :return: a calculation input or None if no corresponding file was found
        """

        uv_file = self.get_uv_file(brewer_id, f"UV{days}{year}.{brewer_id}")
        if uv_file is None:
            return None

        b_file = self.get_b_file(brewer_id, f"B{days}{year}.{brewer_id}")

        arf_file = self.get_arf_file(brewer_id)

        calibration_file = self.get_uvr_file(brewer_id, uvr_file)

        parameter_file_name = year + ".par"
        parameter_file = self.get_parameter_file(parameter_file_name)

        return CalculationInput(
            parameters,
            uv_file,
            b_file,
            calibration_file,
            arf_file,
            parameter_file_name=parameter_file
        )

    def _find_file_recursive(self, directory: str, pattern: Pattern, match_handler: Callable[[str, Match[str]], None]) -> None:
        """
        Recursively search in a given directory for all files matching a pattern. Call a handler for each of the file matching this pattern.

        :param directory: the directory to search for the files in
        :param pattern: the file name pattern
        :param match_handler: the handler to call on the files matching the pattern
        """
        for file_name in listdir(directory):
            file_path = join(directory, file_name)
            if isdir(file_path):
                self._find_file_recursive(file_path, pattern, match_handler)
            else:
                res = re.match(pattern, file_name)
                if res is not None:
                    # File is matching the patter. Call the handler.
                    match_handler(file_path, res)

    def _match_arf_file(self, file_path: str, res: Match[str]) -> None:
        """
        Action to perform on matched arf files.

        See `_find_file_recursive`
        :param file_path: the path of the matched file
        :param res: the result of the regex match
        """
        brewer_id: str = res.group("brewer_id")
        if brewer_id in self._file_dict:
            raise ValueError(f"Multiple ARF files found for brewer with id {brewer_id}.")
        self._file_dict[brewer_id] = InstrumentFiles(File(file_path, self._uvdata_dir))

    def _match_file(
            self,
            file_path: str,
            res: Match[str],
            parent_dir: str,
            field_getter: Callable[[InstrumentFiles], List[File]]
    ) -> None:
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

    def _match_parameter_file(self, file_path: str, res: Match[str]):
        """
        Action to perform on matched parameter files.

        See `_find_file_recursive`
        :param file_path: the path of the matched file
        :param res: the result of the regex match
        """
        year = res.group("year")
        if year in self._parameter_files:
            raise ValueError(f"Multiple parameter files found for year {year}.")
        self._parameter_files.append(File(file_path, self._instr_dir))

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

        A ValueError is raised if the file is not found

        :param brewer_id: the id of the brewer to get the file for
        :return: the file if found, None otherwise
        """
        if brewer_id is None or brewer_id not in self._file_dict:
            raise ValueError(f"Invalid brewer id {brewer_id}.")
        return self._file_dict[brewer_id].arf_file

    def get_parameter_file(self, parameter_file_name: str) -> Optional[File]:
        """
        Search if a parameter file with the given name exists and return it if it exists or None otherwise

        :param parameter_file_name: the name of the file
        :return: the file if found, None otherwise
        """
        try:
            return next(file for file in self._parameter_files if file.file_name == parameter_file_name)
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
            raise ValueError(f"Invalid brewer id {brewer_id}.")
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
    """
    The arf, uvr, uv and b files for one brewer instrument
    """
    arf_file: Optional[File]
    uvr_files: List[File] = field(default_factory=list)
    uv_files: List[File] = field(default_factory=list)
    b_files: List[File] = field(default_factory=list)


@dataclass
class UVFileCombo:
    uv_file: File
    b_file: Optional[File]
