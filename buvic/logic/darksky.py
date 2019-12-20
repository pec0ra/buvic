from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time, date
from logging import getLogger
from typing import List, Callable
from urllib.error import HTTPError
from warnings import warn

from scipy.interpolate import interp1d

from buvic.logic.utils import date_to_days
from ..const import DARKSKY_TOKEN

LOG = getLogger(__name__)


def get_cloud_cover(latitude: float, longitude: float, d: date) -> CloudCover:
    if DARKSKY_TOKEN is None:
        LOG.warning("DARKSKY_TOKEN environment variable is not defined. Functionality will be deactivated and 'clear_sky' will be used as "
                    "default")
        warn(f"DARKSKY_TOKEN environment variable is not defined. Functionality is deactivated and 'clear_sky' "
             f"is used as default for cos correction.")
        return DefaultCloudCover()

    t = datetime.combine(d, time(0, 0, 0, 0)).isoformat()
    url_string = f"https://api.darksky.net/forecast/{DARKSKY_TOKEN}/{latitude},{-longitude},{t}?exclude=minutely,currently,daily&units=si"
    LOG.debug("Retrieved weather data from %s", url_string)
    try:
        with urllib.request.urlopen(url_string) as url:
            data = json.loads(url.read().decode())
    except HTTPError as e:
        raise Exception("Error while trying to access darksky. Please check your configuration and your quota.") from e

    # Display a warning if madis isn't in the data sources
    if "madis" not in data["flags"]["sources"]:
        LOG.warning("The data used as weather to choose between clear sky or diffuse correction might be imprecise. The data used came from"
                    "unknown sources: %s", " ".join(data["flags"]["sources"]))
        warn(f"The data used as weather to choose between clear sky or diffuse correction might be imprecise. The data"
             f" used came from unknown sources: {' '.join(data['flags']['sources'])}")

    # Display a warning if the nearest weather station used is too far away
    nearest_station_distance = data["flags"]["nearest-station"]
    if nearest_station_distance > 30:
        LOG.warning("The data used as weather to choose between clear sky or diffuse correction might be imprecise.\nThe nearest weather "
                    "station found was %f km away from UV measurement.", nearest_station_distance)
        warn(f"The data used as weather to choose between clear sky or diffuse correction might be imprecise.\n"
             f"The nearest weather station found was {nearest_station_distance} km away from UV measurement.")

    i = 0
    times = []
    values = []
    for hour_data in data["hourly"]["data"]:
        if "cloudCover" not in hour_data:
            LOG.warning("No cloud cover data found for hour %d at date %s (%d). Value will be interpolated.", i, d.isoformat(),
                        date_to_days(d))
            warn(f"No cloud cover data found for hour {i}. Value is interpolated.")
            i += 1
            continue
        times.append(float(i * 60))
        values.append(hour_data["cloudCover"])
        i += 1

    if len(values) == 0:
        LOG.warning("No cloud cover data found for date %s (%d). Default value will be used", d.isoformat(), date_to_days(d))
        warn(f"No cloud cover data found for date {d.isoformat()} ({date_to_days(d)}). Default value is used.")
        return DefaultCloudCover()

    return DarkskyCloudCover(times, values)


@dataclass
class CloudCover:
    DIFFUSE_THRESHOLD = 0.9

    def is_diffuse(self, t: float) -> bool:
        """
        Whether the sky is cloudy at a given time given time.

        :param t: the time to get the value for
        :return: True iff the sky is cloudy
        """
        raise NotImplementedError("CloudCover should not be used directly. Use one of its descendent class instead")

    def is_value_diffuse(self, value) -> bool:
        return value >= self.DIFFUSE_THRESHOLD


@dataclass
class DefaultCloudCover(CloudCover):

    def is_diffuse(self, t: float) -> bool:
        LOG.debug("Using default cloud cover")
        return False


@dataclass
class DarkskyCloudCover(CloudCover):
    times: List[float]
    values: List[float]

    def is_diffuse(self, t: float) -> bool:
        LOG.debug("Using darksky cloud cover")
        if len(self.values) == 0:
            raise ValueError("No cloud cover value found in DarkskyCloudCover")
        if len(self.values) == 1:
            return self.is_value_diffuse(self.values[0])
        interpolator = self._get_interpolator()
        return self.is_value_diffuse(interpolator(t))

    def darksky_value(self, t: float) -> float:
        """
        Get the cloud cover value returned by darksky for a given time.

        This value is extrapolated from the hourly darksky data
        :param t: the time to get the value for
        :return: the cloud cover value
        """
        interpolator = self._get_interpolator()
        return interpolator(t)

    def _get_interpolator(self) -> Callable[[float], float]:
        return interp1d(self.times, self.values, kind='nearest', fill_value='extrapolate')


@dataclass
class ParameterCloudCover(CloudCover):
    fix_value: float

    def is_diffuse(self, t: float) -> bool:
        LOG.debug("Using parameter cloud cover")
        return self.is_value_diffuse(self.fix_value)
