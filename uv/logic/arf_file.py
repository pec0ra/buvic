from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from typing import List

LOG = getLogger(__name__)


def read_arf_file(file_name: str, direction: Direction) -> ARF:
    """
    Parse a given arf file into a `ARF` object.
    :param file_name: the name of the file to parse
    :param direction: the direction to get the value for
    :return: the `ARF` object
    """

    LOG.debug("Parsing file: %s", file_name)

    with open(file_name) as file:
        try:
            szas = []
            values = []
            for line in file:
                # Skip header
                if line.strip().startswith("%"):
                    continue
                # Each line consists of at least five values separated by spaces
                line_values = re.split("\s+", line.strip())
                szas.append(float(line_values[0]))
                if len(line_values) == 2:
                    values.append(float(line_values[1]))
                else:
                    values.append(float(line_values[direction.value]))
            szas.append(90)
            values.append(0)

            LOG.debug("Finished parsing file: %s", file_name)

            return ARF(
                szas,
                values
            )
        except Exception as e:
            raise ARFFileParsingError(str(e))


@dataclass
class ARF:
    szas: List[float]
    values: List[float]


class Direction(Enum):
    NORTH = 1
    WEST = 2
    SOUTH = 3
    EAST = 4


class ARFFileParsingError(ValueError):
    pass
