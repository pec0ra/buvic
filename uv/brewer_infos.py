from __future__ import annotations

from dataclasses import dataclass
from warnings import warn


@dataclass
class BrewerInfo:
    id: str
    dual: bool
    uvr_file_name: str
    arf_file_name: str


DEFAULT_BREWER_INFO: BrewerInfo = BrewerInfo("0", False, "UVR17319.151", "arf_151.dat")

brewer_infos = {
    "033": BrewerInfo("033", False, "UVR17419.033", "arf_033.dat"),
    "070": BrewerInfo("070", False, "UVR17319.070", "arf_070.dat"),
    "117": BrewerInfo("117", False, "UVR17319.117", "arf_117.dat"),
    "151": BrewerInfo("151", False, "UVR17419.151", "arf_151.dat"),
    "166": BrewerInfo("166", False, "UVR17319.166", "arf_166.dat"),
    "186": BrewerInfo("186", True, "UVR17419.186", "arf_186.dat")
}


def get_brewer_info(brewer_id: str) -> BrewerInfo:
    """
    Get information about a brewer given by its id
    :param brewer_id: the id of the brewer
    :return: the information
    """
    info = brewer_infos.get(brewer_id)
    if info is None:
        warn("Brewer info was not found for id '" + brewer_id + "'. Using default")
        info = DEFAULT_BREWER_INFO
    return info
