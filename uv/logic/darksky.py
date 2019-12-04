from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time, date
from logging import getLogger
from typing import List

from scipy.interpolate import interp1d

LOG = getLogger(__name__)


def get_cloud_cover(latitude: float, longitude: float, d: date) -> CloudCover:
    t = datetime.combine(d, time(0, 0, 0, 0)).isoformat()
    url_string = f"https://api.darksky.net/forecast/b025a7da3f7c0de2dfda341cc9a7cc39/{latitude},{-longitude},{t}?exclude=minutely,currently,daily&units=si"
    LOG.debug("Retrieved weather data from %s", url_string)
    with urllib.request.urlopen(url_string) as url:
        data = json.loads(url.read().decode())

    # Display a warning if madis isn't in the data sources
    if "madis" not in data["flags"]["sources"]:
        LOG.warning("The data used as weather to choose between clear sky or diffuse correction might be imprecise. The data used came from"
                    "unknown sources: %s", " ".join(data["flags"]["sources"]))

    # Display a warning if the nearest weather station used is too far away
    nearest_station_distance = data["flags"]["nearest-station"]
    if nearest_station_distance > 30:
        LOG.warning("The data used as weather to choose between clear sky or diffuse correction might be imprecise.\nThe nearest weather "
                    "station found was %f km away from UV measurement.", nearest_station_distance)

    i = 0
    times = []
    values = []
    for hour_data in data["hourly"]["data"]:
        times.append(i * 60)
        values.append(hour_data["cloudCover"])
        i += 1
    return CloudCover(times, values)


@dataclass
class CloudCover:
    times: List[float]
    values: List[float]

    def is_diffuse(self, time: float) -> bool:
        if len(self.values) == 0:
            return False
        interpolator = interp1d(self.times, self.values, kind='nearest', fill_value='extrapolate')
        return interpolator(time) >= 0.9
