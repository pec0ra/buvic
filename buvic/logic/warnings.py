import threading
from typing import List

local = threading.local()
local.warnings = []


def warn(message: str) -> None:
    """
    Record a thread local warning message.
    :param message: the message to store
    """
    if not hasattr(local, "warnings"):
        local.warnings = []
    local.warnings.append(message)


def get_warnings() -> List[str]:
    """
    Get all recorded warning messages recorded for the current thread
    :return: the warning messages
    """
    if hasattr(local, "warnings"):
        return local.warnings
    else:
        return []


def clear_warnings() -> None:
    """
    Clear all recorded warning messages for the current thread
    """
    if hasattr(local, "warnings"):
        local.warnings.clear()
