from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Tuple, List, TextIO

import numpy as np


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
        :param file_name: the name of the given file
        """

        self._file_name: str = file_name
        self._uv_file_entries: List[RawUVFileEntry] = []
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
            header = RawUVFileHeader(header_line)

            # Parse the values
            values = []
            next_line = self.__read_line(file)
            while "end" not in next_line and next_line != '':
                values.append(RawUVValue(next_line))
                next_line = self.__read_line(file)

            # Create the resulting entry
            entry = RawUVFileEntry(
                header,
                values
            )
            self._uv_file_entries.append(entry)

            header_line = self.__read_line(file)

    def get_uv_file_entries(self) -> List[RawUVFileEntry]:
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


@dataclass
class RawUVFileHeader:
    HEADER_REGEX = re.compile(
        "^"  # Matches the beginning of the line
        "(?P<type>[a-z]{2})\s+"  # The type is composed of two lower case letters (e.g. ux).
        "Integration time is (?P<integration_time>\S+) seconds.+"  # We match any non blank chars ("\S") for the integration time
        "dt\s+(?P<dead_time>\S+).+"  # We match any non blank chars ("\S") for the dead time to allow scientific 
        # notation 
        "cy\s+(?P<cycles>\d+).+"  # The number of cycles can be any integer (multiple digits "\d")
        "dh\s+(?P<day>\d+) (?P<month>\d+) (?P<year>\d+)\s+"  # Day, month and year are all integers
        "(?P<place>(?: ?[a-zA-Z])+)\s+"  # The localisation name is composed of 1 or more words followed by spaces. 
        # NOTE: special chars (é, ö, ä,etc) are not matched 
        "(?P<latitude>\S+) +(?P<longitude>\S+) +(?P<temp>\S+)\s+"
        # TODO: Check that this is really an int:
        "pr\s*(?P<pr>\d+).*"  # Pr is an integer
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
    position: Tuple[float, float]
    temp: float
    pr: int
    dark: float

    def __init__(self, header_line: str):
        """
        Init from a given header line

        The given header line will be parsed against `HEADER_REGEX` and a `ValueError` will be thrown if the line doesn't
        have the correct format.

        :param header_line: the line to parse
        """

        res = re.match(self.HEADER_REGEX, header_line)
        if res is None:
            raise ValueError("Unable to parse header in file.\nHeader: '" + header_line + "'")
        header = res.groupdict()

        self.raw_header_line = header_line
        self.type = header.get('type')
        self.integration_time = float(header.get('integration_time'))
        self.dead_time = float(header.get('dead_time'))
        self.cycles = int(header.get('cycles'))
        self.date = date(int(header.get('year')), int(header.get('month')), int(header.get('day')))
        self.place = header.get('place')
        self.position = (float(header.get('latitude')), float(header.get('longitude')))
        self.temp = float(header.get('temp'))
        self.pr = int(header.get('pr'))  # TODO: Check that this is really an int
        self.dark = float(header.get('dark'))

    @property
    def day_of_year(self) -> int:
        """
        The number of days since the beginning of the year
        """
        return self.date.timetuple().tm_yday


@dataclass
class RawUVValue:
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

        # Split the line by everything that is not a space (\S+ matches any group of non blank chars)
        re_res = re.findall("\\S+", value_line),
        line_values = re_res[0]

        self.time = float(line_values[0])
        self.wavelength = float(line_values[1]) / 10  # TODO: check if we need angstrom or nm
        self.step = int(line_values[2])
        self.events = float(line_values[3])
        if float(line_values[3]) == 0:
            self.std = 0
        else:
            self.std = np.divide(1, np.sqrt(float(line_values[3])))


@dataclass
class RawUVFileEntry:
    header: RawUVFileHeader
    values: List[RawUVValue]

    def convert_to_abs(self) -> List[float]:
        """
        Convert raw (count) measures to a calibrated spectrum
        :return: the calibrated spectrum
        """

        below_292 = list(filter(lambda x: x.wavelength < 292, self.values))
        straylight_correction = np.mean([v.events for v in below_292])

        # Remove dark signal
        raw_values = [v.events for v in self.values]
        corrected_values = [v - self.header.dark for v in raw_values]

        # Remove straylight
        corrected_values = [v - straylight_correction for v in corrected_values]

        # Convert to photon/sec
        photon_rate = [v * 4 / (self.header.cycles * self.header.integration_time) for v in corrected_values]

        # Correct for linearity
        # TODO: Check that this is the correct way to do it
        photon_rate0 = photon_rate
        for i in range(25):
            photon_rate = np.multiply(photon_rate0, np.exp(np.multiply(photon_rate, self.header.dead_time)))

        # Set negative values to 0
        return np.maximum(0, photon_rate)
