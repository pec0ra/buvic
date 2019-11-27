from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Tuple

from uv.logic.utils import days_to_date
from .arf_file import Direction
from ..brewer_infos import get_brewer_info


@dataclass(unsafe_hash=True)
class CalculationInput:
    albedo: float
    aerosol: Tuple[float, float]
    measurement_date: date
    uv_file_name: str
    b_file_name: str
    calibration_file_name: str
    arf_file_name: str
    arf_direction: Direction = Direction.SOUTH

    @staticmethod
    def from_days_and_bid(
            albedo: float,
            aerosol: Tuple[float, float],
            data_dir: str,
            brewer_id: str,
            days: int,
            year: int = 19
    ) -> CalculationInput:
        if year > 2000:
            year -= 2000
        brewer = get_brewer_info(brewer_id)
        uv_file_name = data_dir + "UV" + str(days) + str(year) + "." + brewer_id
        b_file_name = data_dir + "B" + str(days) + str(year) + "." + brewer_id
        calibration_file_name = data_dir + brewer.uvr_file_name
        arf_file_name = data_dir + brewer.arf_file_name
        measurement_date = days_to_date(days, year)
        return CalculationInput(
            albedo,
            aerosol,
            measurement_date,
            uv_file_name,
            b_file_name,
            calibration_file_name,
            arf_file_name
        )

    @staticmethod
    def from_day_month_and_bid(
            albedo: float,
            aerosol: Tuple[float, float],
            data_dir: str,
            brewer_id: str,
            day: int,
            month: int,
            year: int = 19
    ) -> CalculationInput:
        d = date(year, month, day)
        days = d.timetuple().tm_yday
        return CalculationInput.from_days_and_bid(albedo, aerosol, data_dir, brewer_id, days, year)

    @staticmethod
    def from_date_and_bid(
            albedo: float,
            aerosol: Tuple[float, float],
            data_dir: str,
            brewer_id: str,
            d: date
    ) -> CalculationInput:
        days = d.timetuple().tm_yday
        return CalculationInput.from_days_and_bid(albedo, aerosol, data_dir, brewer_id, days, d.year)

    def to_hash(self) -> str:
        return hex(hash(self))[-6:]
