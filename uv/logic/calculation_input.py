from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from .arf_file import Direction


@dataclass
class CalculationInput:
    uv_file_name: str
    b_file_name: str
    calibration_file_name: str
    arf_file_name: str
    arf_direction: Direction = Direction.SOUTH

    @staticmethod
    def from_days_and_bid(data_dir: str, brewer_id: str, days: int, year: int = 19) -> CalculationInput:
        if year > 2000:
            year -= 2000
        uv_file_name = data_dir + "UV" + str(days) + str(year) + "." + brewer_id
        b_file_name = data_dir + "B" + str(days) + str(year) + "." + brewer_id
        calibration_file_name = data_dir + "UVR__1290." + brewer_id
        arf_file_name = data_dir + "arf_" + brewer_id + ".dat"
        return CalculationInput(uv_file_name, b_file_name, calibration_file_name, arf_file_name)

    @staticmethod
    def from_day_month_and_bid(data_dir: str, brewer_id: str, day: int, month: int, year: int = 19) -> CalculationInput:
        d = date(year, month, day)
        days = d.timetuple().tm_yday
        return CalculationInput.from_days_and_bid(data_dir, brewer_id, days, year)

    @staticmethod
    def from_date_and_bid(data_dir: str, brewer_id: str, d: date) -> CalculationInput:
        days = d.timetuple().tm_yday
        print(days)
        return CalculationInput.from_days_and_bid(data_dir, brewer_id, days, d.year)
