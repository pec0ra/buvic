from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List


def read_arf_file(file_name: str, direction: Direction) -> ARF:
    """
    Parse a given arf file into a `ARF` object.
    :param file_name: the name of the file to parse
    :param direction: the direction to get the value for
    :return: the `ARF` object
    """

    with open(file_name) as file:
        szas = []
        values = []
        for line in file:
            # Skip header
            if line.strip().startswith("%"):
                continue
            # Each line consists of at least five values separated by spaces
            line_values = re.split("\s+", line.strip())
            szas.append(float(line_values[0]))
            values.append(float(line_values[direction.value]))
        szas.append(90)
        values.append(0)

        return ARF(
            szas,
            values
        )


@dataclass
class ARF:
    szas: List[float]
    values: List[float]


class Direction(Enum):
    NORTH = 1
    WEST = 2
    SOUTH = 3
    EAST = 4
