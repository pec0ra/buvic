from __future__ import annotations

from dataclasses import dataclass
from warnings import warn


@dataclass
class BrewerInfo:
    id: str
    dual: bool


DEFAULT_BREWER_INFO: BrewerInfo = BrewerInfo("0", False)

brewer_infos = {
    "033": BrewerInfo("033", False),
    "070": BrewerInfo("070", False),
    "117": BrewerInfo("117", False),
    "151": BrewerInfo("151", False),
    "156": BrewerInfo("156", True),
    "163": BrewerInfo("163", True),
    "166": BrewerInfo("166", False),
    "186": BrewerInfo("186", True)
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
