from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from logging import getLogger
from os import listdir
from os.path import join, exists
from pprint import PrettyPrinter
from typing import Dict, List, Tuple

from uv.logic.utils import days_to_date

LOG = getLogger(__name__)

pp = PrettyPrinter(indent=2)


class FileUtils:
    UV_FILE_NAME_REGEX = re.compile("UV(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)")
    ARF_FILE_NAME_REGEX = re.compile("arf_(?P<brewer_id>\d+)\.dat")
    UVR_FILE_NAME_REGEX = re.compile("UVR\S+\.(?P<brewer_id>\d+)")

    _instr_dir: str
    _uvdata_dir: str
    _file_dict: Dict[str, InstrumentFiles]

    def __init__(self, input_dir: str):
        self._instr_dir = join(input_dir, "instr")
        self._uvdata_dir = join(input_dir, "uvdata")
        self.refresh()

    def refresh(self):

        self._file_dict = {}

        for file_name in listdir(self._instr_dir):
            # ARF file names are like `arf_070.dat`
            res = re.match(self.ARF_FILE_NAME_REGEX, file_name)
            if res is not None:
                brewer_id = res.group("brewer_id")
                if brewer_id in self._file_dict:
                    raise ValueError(f"Multiple ARF files found for brewer with id {brewer_id}.")
                self._file_dict[brewer_id] = InstrumentFiles(file_name)

        for file_name in listdir(self._instr_dir):
            # UVR file names are like `UVR12319.070`
            res = re.match(self.UVR_FILE_NAME_REGEX, file_name)
            if res is not None:
                brewer_id = res.group("brewer_id")
                if brewer_id not in self._file_dict:
                    LOG.warning(f"No arf file exists for brewer id {brewer_id}, skipping")
                    continue
                self._file_dict[brewer_id].uvr_files.append(file_name)

        for brewer_id, instrument_files in list(self._file_dict.items()):
            # Remove the instruments without UVR files
            if len(instrument_files.uvr_files) == 0:
                LOG.warning(f"No UVR file exists for brewer id {brewer_id}, skipping")
                del self._file_dict[brewer_id]

        for file_name in listdir(self._uvdata_dir):
            # UV file names are like `UV12319.070`
            res = re.match(self.UV_FILE_NAME_REGEX, file_name)
            if res is not None:
                days = res.group("days")
                year = res.group("year")
                brewer_id = res.group("brewer_id")
                if brewer_id not in self._file_dict:
                    LOG.warning(f"No arf file exists for brewer id {brewer_id}, skipping")
                    continue

                b_file = "B" + days + year + "." + brewer_id
                b_file_path = join(self._uvdata_dir, b_file)
                if exists(b_file_path):
                    self._file_dict[brewer_id].uv_files_combinations.append(UVFileCombo(file_name, b_file))
                else:
                    self._file_dict[brewer_id].uv_files_combinations.append(UVFileCombo(file_name, None))

    def get_brewer_ids(self) -> List[str]:
        return sorted(self._file_dict.keys())

    def get_uvr_files(self, brewer_id: str) -> List[str]:
        if brewer_id not in self._file_dict:
            raise ValueError(f"No uvr file found for brewer id {brewer_id}.")
        return sorted(self._file_dict[brewer_id].uvr_files)

    def get_date_range(self, brewer_id: str) -> Tuple[date, date]:
        min_date: date or None = None
        max_date: date or None = None
        if brewer_id not in self._file_dict:
            raise ValueError(f"Brewer with id {brewer_id} is not present in the list of files.")

        for comb in self._file_dict[brewer_id].uv_files_combinations:
            res = re.match(self.UV_FILE_NAME_REGEX, comb.uv_file)
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
    arf_file: str or None
    uvr_files: List[str] = field(default_factory=list)
    uv_files_combinations: List[UVFileCombo] = field(default_factory=list)


@dataclass
class UVFileCombo:
    uv_file: str
    b_file: str or None
