from datetime import timedelta, date, time


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
