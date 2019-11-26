from datetime import timedelta, date, time


def days_to_date(days: int, year: int) -> date:
    if days < 1 or days > 366:
        raise ValueError("Days must be between 1 and 365")
    if year < 2000:
        year += 2000
    return date(year, 1, 1) + timedelta(days=days - 1)


def date_to_days(d: date) -> int:
    return d.timetuple().tm_yday


def minutes_to_time(minutes: float) -> time:
    td = timedelta(minutes=minutes)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hour=hours, minute=minutes, second=seconds)


def time_to_minutes(t: time) -> float:
    td = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    return td.seconds / 60
