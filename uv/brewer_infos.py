from __future__ import annotations

from dataclasses import dataclass
from warnings import warn


@dataclass
class BrewerInfo:
    id: str
    uvr_file_name: str or None


DEFAULT_BREWER_INFO: BrewerInfo = BrewerInfo("0", None)

brewer_infos = {
    "033": BrewerInfo("033", "UVR17419.033"),
    "070": BrewerInfo("070", "UVR17319.070"),
    "117": BrewerInfo("117", "UVR17319.117"),
    "151": BrewerInfo("151", "UVR17419.151"),
    "166": BrewerInfo("166", "UVR17319.166"),
    "186": BrewerInfo("186", "UVR17419.186")
}

# Map brewer types to whether they need straylight correction
brewer_types = {
    "mki": True,
    "mkii": True,
    "mkiii": False,
    "mkvi": True,
}


def correct_straylight(brewer_type: str):
    if brewer_type in brewer_types:
        return brewer_types[brewer_type]
    else:
        return True


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
