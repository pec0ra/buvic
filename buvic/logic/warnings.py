import threading
from typing import List

local = threading.local()
local.warnings = []


def warn(message: str) -> None:
    if not hasattr(local, "warnings"):
        local.warnings = []
    local.warnings.append(message)


def get_warnings() -> List[str]:
    if hasattr(local, "warnings"):
        return local.warnings
    else:
        return []


def clear_warnings() -> None:
    if hasattr(local, "warnings"):
        local.warnings.clear()
