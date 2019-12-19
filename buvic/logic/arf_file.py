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
                sza = float(line_values[0])
                if sza < 0 or sza > 90:
                    raise ValueError(f"Invalid value found in the first column. Sza must be between 0 and 90. Found {sza}")
                szas.append(sza)
                if len(line_values) <= 4:
                    values.append(float(line_values[-1]))
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
            raise ARFFileParsingError(f"An error occurred while parsing the arf file: {e}") from e


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
