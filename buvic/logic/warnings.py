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
