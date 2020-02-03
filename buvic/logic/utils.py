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
import re
from datetime import timedelta, date, time
from typing import Iterable, Tuple


def days_to_date(days: int, year: int) -> date:
    """
    Converts a number of days since new year and a year to a date object
    :param days: the number of days since new year
    :param year: the year
    :return: the date
    """
    if days < 1 or days > 366:
        raise ValueError("Days must be between 1 and 365")
    if year < 2000:
        year += 2000
    return date(year, 1, 1) + timedelta(days=days - 1)


def date_to_days(d: date) -> int:
    """
    Converts a date object to the number of days since new year (January 1st is 1)
    :param d: the date to convert
    :return: the number of days
    """
    return d.timetuple().tm_yday


def minutes_to_time(minutes: float) -> time:
    """
    Converts a number of minutes since midnight to a time object
    :param minutes: the number of minutes since midnight
    :return: the time object
    """
    td = timedelta(minutes=minutes)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hour=hours, minute=minutes, second=seconds)


def time_to_minutes(t: time) -> float:
    """
    Converts a time object to minutes since midnight
    :param t: the time to convert
    :return: the number of minutes since midnight
    """
    td = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    return td.seconds / 60


def date_range(start_date: date, end_date: date) -> Iterable[date]:
    """
    Create a range between a start date (inclusive) and end date (inclusive) to loop through day per day
    :param start_date: the range's lower bound
    :param end_date: the range's upper bound
    :return:
    """
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


_FILE_NAME_REGEX = re.compile(r"[a-zA-Z]+(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d{3})")


def name_to_date_and_brewer_id(file_name: str) -> Tuple[date, str]:
    """
    Find the date and brewer id from a file name of the form XXDDDYY.bid
    :param file_name: the name to find the date and brewer id from
    :return: the date and the brewer id
    """
    res = re.search(_FILE_NAME_REGEX, file_name)
    if res is None:
        raise ValueError(f"Unknown file name {file_name}")
    year = int(res.group("year"))
    days = res.group("days")
    d = days_to_date(int(days), year)
    brewer_id = res.group("brewer_id")
    return d, brewer_id
