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
