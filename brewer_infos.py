from __future__ import annotations

from dataclasses import dataclass
from warnings import warn


@dataclass
class BrewerInfo:
    id: str
    dual: bool


DEFAULT_BREWER_INFO: BrewerInfo = BrewerInfo("0", False)

brewer_infos = {
    "156": BrewerInfo("156", True),
    "163": BrewerInfo("163", True)
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
