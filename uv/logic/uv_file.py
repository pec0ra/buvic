from __future__ import annotations

import re
from collections import namedtuple
from dataclasses import dataclass
from datetime import date
from typing import List, TextIO
from warnings import warn

from numpy import divide, sqrt

from .brewer_infos import get_brewer_info, BrewerInfo


class UVFileReader(object):
    """
    A utility class to read and parse UV files.

    A UV file is composed of multiple sections, each with the following structure:
        * A Header (see `RawUVFileHeader`)
        * Multiple lines of values grouped by 4 (e.g. "308.58 3600 9143 92.5" - see `RawUVValue`)
        * The keyword "end" (optional)

    For each of the section, this utility will create a "UVFileEntry" object. The list of these objects can be retrieved
    with `get_uv_file_entries()`
    """

    def __init__(self, file_name: str):
        """
        Create an instance of this class and parse the given file
        :param file_name: the name of the file to read
        """

        self._file_name: str = file_name
        with open(file_name, newline='\r\n') as file:
            self._uv_file_entries: List[UVFileEntry] = self.__parse(file)

    def __parse(self, file: TextIO) -> List[UVFileEntry]:
        """
        Parse the given file and return the corresponding instances of `UVFileEntry`
        :param file: the file to parse
        :return the list of `UVFileEntry`
        """

        entries = []
        header_line = self.__read_line(file)

        # Loop until end of file. Each iteration in the loop corresponds to one entry (header + values)
        while header_line.strip() != '\x1A' and header_line.strip() != '':

            # Parse the header
            header = UVFileHeader(header_line)

            # Parse the values
            values = []
            next_line = self.__read_line(file)
            while "end" not in next_line and next_line != '':
                values.append(RawUVValue(next_line))
                next_line = self.__read_line(file)

            # Create the resulting entry and add it to the result
            entry = UVFileEntry(
                get_brewer_info(self.__get_brewer_id()),
                header,
                values
            )
            entries.append(entry)

            header_line = self.__read_line(file)

        return entries

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

    def __get_brewer_id(self) -> str:
        return self._file_name.split('.')[-1]


@dataclass
class UVFileHeader:
    HEADER_REGEX = re.compile(
        "^"  # Matches the beginning of the line
        "(?P<type>[a-z]{2})\s+"  # The type is composed of two lower case letters (e.g. ux).
        "Integration time is (?P<integration_time>\S+) seconds.+"  # We match any non blank chars ("\S")
        "dt\s+(?P<dead_time>\S+).+"  # We match any non blank chars ("\S") for the dead time to allow scientific 
        # notation 
        "cy\s+(?P<cycles>\d+).+"  # The number of cycles can be any integer (multiple digits "\d")
        "dh\s+(?P<day>\d+) (?P<month>\d+) (?P<year>\d+)\s+"  # Day, month and year are all integers
        "(?P<place>(?: ?[a-zA-Z])+)\s+"  # The localisation name is composed of 1 or more words followed by spaces. 
        # NOTE: special chars (é, ö, ä,etc) are not matched 
        "(?P<latitude>\S+) +(?P<longitude>\S+) +(?P<temperature>\S+)\s+"
        # TODO: Check that this is really an int:
        "pr\s*(?P<pressure>\d+).*"  # Pressure is an integer
        "dark\s*(?P<dark>\S+)\s*"  # We match any non blank chars ("\S") for the dark to allow scientific notation
        "$"  # Matches the end of the line
    )

    raw_header_line: str
    type: str
    integration_time: float
    dead_time: float
    cycles: int
    date: date
    place: str
    position: Position
    temperature: float
    pressure: int
    dark: float

    def __init__(self, header_line: str):
        """
        Init from a given header line

        The given header line will be parsed against `HEADER_REGEX` and a `UVFileParsingError` will be thrown if the line
        doesn't have the correct format.

        :param header_line: the line to parse
        """

        res = re.match(self.HEADER_REGEX, header_line)
        if res is None:
            raise UVFileParsingError("Unable to parse header.\nHeader: '" + header_line + "'")

        self.raw_header_line = header_line
        self.type = res.group('type')
        self.integration_time = float(res.group('integration_time'))
        self.dead_time = float(res.group('dead_time'))
        self.cycles = int(res.group('cycles'))
        self.date = date(int(res.group('year')), int(res.group('month')), int(res.group('day')))
        self.place = res.group('place')
        self.position = Position(float(res.group('latitude')), float(res.group('longitude')))
        self.temperature = float(res.group('temperature'))  # TODO: Temperature might need a conversion
        self.pressure = int(res.group('pressure'))  # TODO: Check that this is really always an int
        self.dark = float(res.group('dark'))

        if self.integration_time == 0.1147:
            warn("Integration time is 0.1147. This might be correct but there is a high chance that the value that you"
                 "want is 0.2294 instead.")

    @property
    def day_of_year(self) -> int:
        """
        The number of days since the beginning of the year
        """
        return self.date.timetuple().tm_yday


@dataclass
class RawUVValue:
    VALUE_REGEX = re.compile(
        "^\s*"  # Matches the beginning of the line
        "(?P<time>\S+)\s+"  # Time can be any combination of non blank chars
        "(?P<wavelength>\S+)\s+"  # Wavelength can be any combination of non blank chars
        "(?P<step>\d+)\s+"  # Step can be any combination of digits
        "(?P<events>\S+)\s*"  # Events can be any combination of non blank chars
        "$"  # Matches the end of the line
    )

    time: float
    wavelength: float
    step: int
    events: float
    std: float

    def __init__(self, value_line):
        """
        Init from a given line
        :param value_line: the line to parse
        """

        res = re.match(self.VALUE_REGEX, value_line)
        if res is None:
            raise UVFileParsingError("Unable to parse value line.\nLine: '" + value_line + "'")

        self.time = float(res.group("time"))
        self.wavelength = float(res.group("wavelength")) / 10
        self.step = int(res.group("step"))
        events = float(res.group("events"))
        self.events = events
        if events == 0:
            self.std = 0
        else:
            self.std = divide(1, sqrt(events))


@dataclass
class UVFileEntry:
    brewer_info: BrewerInfo
    header: UVFileHeader
    raw_values: List[RawUVValue]

    @property
    def wavelengths(self) -> List[float]:
        return [v.wavelength for v in self.raw_values]

    @property
    def events(self) -> List[float]:
        return [v.events for v in self.raw_values]


Position = namedtuple('Position', ['latitude', 'longitude'])


class UVFileParsingError(ValueError):
    pass
