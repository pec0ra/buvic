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

# Map brewer types to whether they need straylight correction
from enum import Enum
from typing import Optional


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
