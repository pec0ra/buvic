from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import date
from typing import Tuple, List, TextIO

import numpy


class UVFileReader(object):
    """
    A utility class to read and parse UV files.

    A UV file is composed of multiple sections, each with the following structure:
        * A Header (see `HEADER_REGEX` and `__parse_header()`)
        * Multiple lines of values grouped by 4 (e.g. "308.58 3600 9143 92.5")
        * The keyword "end" (optional)

    For each of the section, this utility will create a "UVFileEntry" object. The list of these objects can be retrieved
    with `get_uv_file_entries()`
    """

    HEADER_REGEX = re.compile(
        "^"  # Matches the beginning of the line
        "(?P<type>[a-z]{2})\s+"  # The type is composed of two lower case letters (e.g. ux).
        "Integration time is (?P<integration_time>\S+) seconds.+"  # We match any non blank chars ("\S") for the integration time
        "dt\s+(?P<dead_time>\S+).+"  # We match any non blank chars ("\S") for the dead time to allow scientific 
        # notation 
        "cy\s+(?P<cycles>\d+).+"  # The number of cycles can be any integer (multiple digits "\d")
        "dh\s+(?P<day>\d+) (?P<month>\d+) (?P<year>\d+) "  # Day, month and year are all integers
        "(?P<place>(?:[a-zA-Z] ?)+)\s\s+"  # The localisation name is composed of 1 or more words followed by spaces. 
        # NOTE: special chars (é, ö, ä,etc) are not matched 
        "(?P<latitude>\S+) +(?P<longitude>\S+) +(?P<temp>\S+)\s+"
        "pr\s*(?P<pr>\d+).*"  # Pr is an integer
        "dark\s*(?P<dark>\S+)\s*"  # We match any non blank chars ("\S") for the dark to allow scientific notation
        "$"  # Matches the end of the line
    )

    def __init__(self, file_name: str):
        """
        Create an instance of this class and parse the given file
        :param file_name: the name of the given file
        """

        self._file_name: str = file_name
        self._uv_file_entries: List[UVFileEntry] = []
        with open(file_name, newline='\r\n') as file:
            self.__parse(file)

    def __parse(self, file: TextIO) -> None:
        """
        Parse the given file and create the corresponding instances of `UVFileEntry`
        :param file: the file to parse
        """

        header_line = self.__read_line(file)

        # Loop until end of file. Each iteration in the loop corresponds to one entry (header + values)
        while header_line.strip() != '\x1A' and header_line.strip() != '':

            # Parse the header
            header = self.__handle_header(header_line)

            # Parse the values
            values = []
            next_line = self.__read_line(file)
            while "end" not in next_line and next_line != '':
                values.append(self.__handle_value_line(next_line))
                next_line = self.__read_line(file)

            # Create the resulting entry
            entry = UVFileEntry(
                header_line,
                header.get('type'),
                float(header.get('integration_time')),
                float(header.get('dead_time')),
                int(header.get('cycles')),
                date(int(header.get('day')), int(header.get('month')), int(header.get('year'))),
                header.get('place'),
                (float(header.get('latitude')), float(header.get('longitude'))),
                float(header.get('temp')),
                int(header.get('pr')),  # TODO: Check that this is really an int
                float(header.get('dark')),
                values
            )
            self._uv_file_entries.append(entry)

            header_line = self.__read_line(file)

    def get_uv_file_entries(self) -> List[UVFileEntry]:
        """
        Get the list of parsed `UVFileEntry`
        :return: the list of `UVFileEntry`
        """

        if len(self._uv_file_entries) == 0:
            raise AssertionError("Object has not been initialized correctly")
        return self._uv_file_entries

    @staticmethod
    def __read_line(file: TextIO) -> str:
        """
        Read the next line of the file

        The resulting line will have its Carriage Returns ('\r') replaced by spaces and the new line ('\n') at the end
        removed

        :param file: the file to read the line from
        :return: the line
        """
        return file.readline().replace('\r', ' ').replace('\n', '')

    def __handle_header(self, header_line: str) -> dict:
        """
        Parse a given header line into a map of name-value pairs

        The given header line will be parsed against `HEADER_REGEX` and a `ValueError` will be thrown if the line doesn't
        have the correct format.

        :param header_line: the line to parse
        :return: the map
        """

        res = re.match(self.HEADER_REGEX, header_line)
        if res is None:
            raise ValueError("Unable to parse header in file '" + self._file_name + "'\nHeader: '" + header_line + "'")
        return res.groupdict()

    @staticmethod
    def __handle_value_line(line: str) -> UVFileEntryValue:
        """
        Parse value from a given line into a `UVFileEntryValue`
        :param line: the line to parse
        :return: the created `UVFileEntryValue`
        """

        # Split the line by everything that is not a space (\S+ matches any group of non blank chars)
        re_res = re.findall("\\S+", line),
        line_values = re_res[0]

        return UVFileEntryValue(
            float(line_values[0]),
            float(line_values[1]) / 10,
            int(line_values[2]),
            float(line_values[3]),
            numpy.divide(1, numpy.sqrt(float(line_values[3])))
        )


@dataclass
class UVFileEntryValue:
    time: float
    wavelength: float
    step: int
    events: float
    std: float


@dataclass
class UVFileEntry:
    raw_header_line: str
    type: str
    integration_time: float
    dead_time: float
    cycles: int
    date: date
    place: str
    position: Tuple[float, float]
    temp: float
    pr: int
    dark: float
    values: List[UVFileEntryValue]

    @property
    def day_of_year(self):
        return self.date.timetuple().tm_yday
