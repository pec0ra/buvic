from __future__ import annotations

import itertools
import json
import re
import urllib.request
from collections import namedtuple
from dataclasses import dataclass
from datetime import date
from logging import getLogger
from statistics import mean
from typing import List, TextIO
from urllib.error import HTTPError
from warnings import warn

from numpy import divide, sqrt

LOG = getLogger(__name__)


class UVProvider:
    def get_uv_file_entries(self) -> List[UVFileEntry]:
        """
        Get the list of `UVFileEntry`
        :return: the list of `UVFileEntry`
        """
        raise NotImplementedError("'get_uv_file_entries' should be implemented in a child class")

    @staticmethod
    def mean_of_duplicates(values: List[RawUVValue]) -> List[RawUVValue]:
        ret_list = []
        for wavelength, values_of_group in itertools.groupby(sorted(values, key=lambda v: v.wavelength), lambda v: v.wavelength):
            value_list = list(values_of_group)
            if len(value_list) == 1:
                ret_list.append(value_list[0])
            else:
                time = mean([v.time for v in value_list])
                step = mean([v.step for v in value_list])
                events = mean([v.events for v in value_list])
                if events == 0:
                    std = 0
                else:
                    std = divide(1, sqrt(events))
                ret_list.append(RawUVValue(
                    time,
                    wavelength,
                    step,
                    events,
                    std
                ))
        return ret_list


class UVFileUVProvider(UVProvider):
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

        LOG.debug("Parsing file: %s", self._file_name)

        entries = []
        header_line = self.__read_line(file)

        # Loop until end of file. Each iteration in the loop corresponds to one entry (header + values)
        while header_line.strip() != '\x1A' and header_line.strip() != '':

            # Parse the header
            header = UVFileHeader.from_header_line(header_line)

            LOG.debug("Parsed header: %s", header.raw_header_line)

            # Parse the values
            values = []
            next_line = self.__read_line(file)
            while "dark" not in next_line and "end" not in next_line and next_line != '':
                values.append(RawUVValue.from_value_line(next_line))
                next_line = self.__read_line(file)

            dark_match = re.match("^dark\s+(?P<dark>\S+)\s+$", next_line)
            if dark_match is not None:
                header.dark = (header.dark + float(dark_match.group("dark"))) / 2
                next_line = self.__read_line(file)
                for i in range(len(values) - 1, -1, -1):
                    old_value = values[i]
                    new_value = RawUVValue.from_value_line(next_line)
                    old_value.time = (old_value.time + new_value.time) / 2
                    old_value.events = (old_value.events + new_value.events) / 2
                    old_value.time = (old_value.step + new_value.step) / 2
                    old_value.std = divide(1, sqrt(old_value.events))
                    next_line = self.__read_line(file)

                if "end" not in next_line and next_line != '':
                    raise UVFileParsingError("Failed parsing uv section. Expected 'end' but found " + next_line)

            # Create the resulting entry and add it to the result
            entry = UVFileEntry(
                header,
                values
            )
            entries.append(entry)

            header_line = self.__read_line(file)

        LOG.debug("Parsed %s entries from file '%s'", len(entries), self._file_name)
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


class EubrewnetUVProvider(UVProvider):

    def __init__(self, brewer_id: str, d: date):
        self._brewer_id = brewer_id
        self._date = d

    def get_uv_file_entries(self) -> List[UVFileEntry]:

        url_string = f"http://rbcce.aemet.es/eubrewnet/getdataold/getUVAvailableScanTypes?brewerid={self._brewer_id}&date={self._date.isoformat()}"
        LOG.info("Retrieved scan types from %s", url_string)
        try:
            with urllib.request.urlopen(url_string) as url:
                scan_types = json.loads(url.read().decode())
        except HTTPError as e:
            raise Exception(f"Error while trying to access eubrewnet. {e}") from e

        file_entries = []
        for scan_type in scan_types:
            url_string = f"http://rbcce.aemet.es/eubrewnet/getdataold/getUV?scantype={scan_type}&brewerid={self._brewer_id}&date={self._date.isoformat()}"
            LOG.info("Retrieved uv data from %s", url_string)
            try:
                with urllib.request.urlopen(url_string) as url:
                    data = json.loads(url.read().decode())
                    for d in [data[i:i + 5] for i in range(0, len(data), 5)]:
                        header_list = d[0]
                        times = d[1]
                        wavelengths = d[2]
                        steps = d[3]
                        counts = d[4]
                        header = UVFileHeader(
                            raw_header_line=url_string,
                            type=scan_type,
                            integration_time=header_list[2],
                            dead_time=header_list[3],
                            cycles=header_list[4],
                            date=date.fromisoformat(header_list[5]),
                            place=header_list[6],
                            position=Position(header_list[7], header_list[8]),
                            temperature=header_list[9],  # TODO: Temperature might need a conversion
                            pressure=header_list[10],
                            dark=header_list[11]
                        )
                        values = []
                        for i in range(0, len(times)):
                            events = counts[i]
                            if events == 0:
                                std = 0
                            else:
                                std = divide(1, sqrt(events))
                            values.append(RawUVValue(
                                times[i],
                                wavelengths[i] / 10,
                                steps[i],
                                events,
                                std
                            ))

                        file_entries.append(UVFileEntry(
                            header,
                            self.mean_of_duplicates(values)
                        ))
            except HTTPError as e:
                raise Exception(f"Error while trying to access eubrewnet. {e}") from e
        return file_entries


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
    pressure: float
    dark: float

    @staticmethod
    def from_header_line(header_line: str) -> UVFileHeader:
        """
        Init from a given header line

        The given header line will be parsed against `HEADER_REGEX` and a `UVFileParsingError` will be thrown if the line
        doesn't have the correct format.

        :param header_line: the line to parse
        """

        res = re.match(UVFileHeader.HEADER_REGEX, header_line)
        if res is None:
            raise UVFileParsingError("Unable to parse header.\nHeader: '" + header_line + "'")

        integration_time = float(res.group('integration_time'))
        if integration_time == 0.1147:
            warn("Integration time is 0.1147. This might be correct but there is a high chance that the value that you"
                 "want is 0.2294 instead.")

        return UVFileHeader(
            raw_header_line=header_line,
            type=res.group('type'),
            integration_time=float(res.group('integration_time')),
            dead_time=float(res.group('dead_time')),
            cycles=int(res.group('cycles')),
            date=date(int(2000 + int(res.group('year'))), int(res.group('month')), int(res.group('day'))),
            place=res.group('place'),
            position=Position(float(res.group('latitude')), float(res.group('longitude'))),
            temperature=float(res.group('temperature')),  # TODO: Temperature might need a conversion
            pressure=float(res.group('pressure')),
            dark=float(res.group('dark'))
        )


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

    @staticmethod
    def from_value_line(value_line: str):
        """
        Init from a given line
        :param value_line: the line to parse
        """

        res = re.match(RawUVValue.VALUE_REGEX, value_line)
        if res is None:
            raise UVFileParsingError("Unable to parse value line.\nLine: '" + value_line + "'")

        time = float(res.group("time"))
        wavelength = float(res.group("wavelength")) / 10
        step = int(res.group("step"))
        events = float(res.group("events"))
        if events == 0:
            std = 0
        else:
            std = divide(1, sqrt(events))
        return RawUVValue(
            time,
            wavelength,
            step,
            events,
            std
        )


@dataclass
class UVFileEntry:
    header: UVFileHeader
    raw_values: List[RawUVValue]

    @property
    def wavelengths(self) -> List[float]:
        return [v.wavelength for v in self.raw_values]

    @property
    def events(self) -> List[float]:
        return [v.events for v in self.raw_values]

    @property
    def times(self) -> List[float]:
        return [v.time for v in self.raw_values]


Position = namedtuple('Position', ['latitude', 'longitude'])


class UVFileParsingError(ValueError):
    pass
