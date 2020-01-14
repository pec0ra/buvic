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
from dataclasses import dataclass
from typing import Generic, Callable, TypeVar

INPUT = TypeVar("INPUT")
RETURN = TypeVar("RETURN")


@dataclass
class Job(Generic[INPUT, RETURN]):
    _fn: Callable[[INPUT], RETURN]
    _args: INPUT

    def run(self) -> RETURN:
        """
        Execute the job
        :return: the job's return value
        """
        return self._fn(self._args)  # type: ignore
