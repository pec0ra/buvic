from __future__ import annotations

import functools
from dataclasses import dataclass
from datetime import date
from typing import Tuple

from uv.logic.b_file import read_ozone_from_b_file
from uv.logic.calibration_file import read_calibration_file
from uv.logic.uv_file import UVFileReader
from .arf_file import Direction, read_arf_file
from ..brewer_infos import get_brewer_info


@dataclass(unsafe_hash=True)
class CalculationInput:
    """
    An input for the `IrradianceCalculation`
    """
    albedo: float
    aerosol: Tuple[float, float]
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
        return CalculationInput(
            albedo,
            aerosol,
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

    @property
    @functools.lru_cache()
    def uv_file_entries(self):
        uv_file_reader = UVFileReader(self.uv_file_name)
        return uv_file_reader.get_uv_file_entries()

    @property
    @functools.lru_cache()
    def ozone(self):
        return read_ozone_from_b_file(self.b_file_name)

    @property
    @functools.lru_cache()
    def calibration(self):
        return read_calibration_file(self.calibration_file_name)

    @property
    @functools.lru_cache()
    def arf(self):
        return read_arf_file(self.arf_file_name, self.arf_direction)

    def to_hash(self) -> str:
        return hex(hash(self))[-6:]
