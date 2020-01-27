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

import json
import re
from datetime import date
from enum import Enum
from logging import getLogger
from os import path
from typing import Optional

import requests
import requests.auth

from buvic.logic.file import File
from .ozone import BFileParsingError
from .warnings import warn

LOG = getLogger(__name__)


class BrewerModelProvider:
    def get_brewer_type(self) -> Optional[str]:
        raise NotImplementedError("'get_brewer_type' must be implemented in a subclass")


class EubrewnetBrewerModelProvider(BrewerModelProvider):

    def __init__(self, brewer_id: str, d: date):
        self._url_string = f"http://rbcce.aemet.es/eubrewnet/data/get/ConfigbyDate?brewerid={brewer_id}&date={d.isoformat()}&fields=brewer_model"

    def get_brewer_type(self) -> Optional[str]:

        LOG.info("Retrieving brewer model from %s", self._url_string)
        try:
            response = requests.get(self._url_string, auth=requests.auth.HTTPBasicAuth("are2019", "arework"))
            data = json.loads(response.text)
            brewer_number = data[1][0]
            if brewer_number == "1":
                return "mki"
            elif brewer_number == "2":
                return "mkii"
            elif brewer_number == "3":
                return "mkiii"
            elif brewer_number == "4":
                return "mkiv"
            else:
                LOG.warning(f"Unknown brewer model found on eubrewnet: {brewer_number}")
                warn(f"Unknown brewer model found on eubrewnet: {brewer_number}")
            return brewer_number
        except Exception as e:
            raise Exception(f"Error while trying to access eubrewnet ({self._url_string}). {e}") from e


class BFileBrewerModelProvider(BrewerModelProvider):
    INSTRUMENT_CONSTANTS_LINE_REGEX = re.compile(r"inst\s+" r"(?:\S+\s+){22}" r"(?P<brewer_type>\S+)\s+")

    def __init__(self, file: Optional[File]):
        self._file = file

    def get_brewer_type(self) -> Optional[str]:
        if self._file is None or not path.exists(self._file.full_path):
            return None

        LOG.debug("Parsing file: %s", self._file.file_name)

        with open(self._file.full_path, newline="\r\n") as f:
            try:
                brewer_type = None
                for raw_line in f:
                    line = raw_line.replace("\r", " ").replace("\n", "").strip()
                    res_constants = re.match(self.INSTRUMENT_CONSTANTS_LINE_REGEX, line)
                    if res_constants is not None:
                        brewer_type = res_constants.group("brewer_type")
                        break

                LOG.debug("Finished parsing file: %s", self._file.file_name)

                if brewer_type is None:
                    LOG.warning(f"No brewer type found in b file {self._file.file_name}")
                    warn(f"No brewer type found in b file {self._file.file_name}")
                    return None

                return brewer_type
            except Exception as e:
                raise BFileParsingError("An error occurred while parsing the B File") from e


class StraylightCorrection(str, Enum):
    APPLIED = "Applied"
    NOT_APPLIED = "Not applied"
    UNDEFINED = "Undefined"


brewer_types = {
    "mki": StraylightCorrection.APPLIED,
    "mkii": StraylightCorrection.APPLIED,
    "mkiii": StraylightCorrection.NOT_APPLIED,
    "mkiv": StraylightCorrection.APPLIED,
}


def correct_straylight(brewer_type: Optional[str]) -> StraylightCorrection:
    if brewer_type in brewer_types:
        return brewer_types[brewer_type]
    else:
        return StraylightCorrection.UNDEFINED


eubrewnet_available_brewer_ids = [
    "001",
    "005",
    "006",
    "008",
    "010",
    "016",
    "017",
    "030",
    "033",
    "037",
    "039",
    "040",
    "043",
    "044",
    "047",
    "048",
    "051",
    "053",
    "064",
    "065",
    "066",
    "067",
    "070",
    "071",
    "072",
    "075",
    "078",
    "082",
    "085",
    "086",
    "088",
    "095",
    "097",
    "098",
    "099",
    "100",
    "102",
    "107",
    "109",
    "117",
    "118",
    "123",
    "126",
    "128",
    "143",
    "145",
    "149",
    "150",
    "151",
    "152",
    "155",
    "156",
    "157",
    "158",
    "161",
    "163",
    "164",
    "165",
    "166",
    "171",
    "172",
    "174",
    "178",
    "179",
    "180",
    "183",
    "184",
    "185",
    "186",
    "188",
    "190",
    "191",
    "192",
    "193",
    "195",
    "196",
    "197",
    "201",
    "202",
    "204",
    "205",
    "207",
    "209",
    "212",
    "214",
    "216",
    "217",
    "218",
    "220",
    "221",
    "225",
    "226",
    "227",
    "228",
    "229",
    "230",
    "232",
    "233",
    "246",
    "300",
]
