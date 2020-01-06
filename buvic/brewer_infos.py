from __future__ import annotations

# Map brewer types to whether they need straylight correction
from enum import Enum


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


def correct_straylight(brewer_type: str) -> StraylightCorrection:
    if brewer_type in brewer_types:
        return brewer_types[brewer_type]
    else:
        return StraylightCorrection.UNDEFINED


eubrewnet_available_brewer_ids = ["001", "005", "006", "008", "010", "016", "017", "030", "033", "037", "039", "040", "043", "044", "047",
                                  "048", "051", "053", "064", "065", "066", "067", "070", "071", "072", "075", "078", "082", "085", "086",
                                  "088", "095", "097", "098", "099", "100", "102", "107", "109", "117", "118", "123", "126", "128", "143",
                                  "145", "149", "150", "151", "152", "155", "156", "157", "158", "161", "163", "164", "165", "166", "171",
                                  "172", "174", "178", "179", "180", "183", "184", "185", "186", "188", "190", "191", "192", "193", "195",
                                  "196", "197", "201", "202", "204", "205", "207", "209", "212", "214", "216", "217", "218", "220", "221",
                                  "225", "226", "227", "228", "229", "230", "232", "233", "246", "300"]
