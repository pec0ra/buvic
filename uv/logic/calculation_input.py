from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List

from cached_property import threaded_cached_property

from uv.logic.b_file import read_ozone_from_b_file, Ozone
from uv.logic.calibration_file import read_calibration_file
from uv.logic.darksky import get_cloud_cover, CloudCover
from uv.logic.uv_file import UVFileReader, UVFileEntry
from .arf_file import Direction, read_arf_file


@dataclass(unsafe_hash=True)
class CalculationInput:
    """
    An input for the `IrradianceCalculation`
    """
    albedo: float
    aerosol: Tuple[float, float]
    default_ozone: float
    uv_file_name: str
    b_file_name: str
    calibration_file_name: str
    arf_file_name: str
    no_coscor: bool = False  # TODO
    arf_direction: Direction = Direction.SOUTH

    @threaded_cached_property
    def uv_file_entries(self) -> List[UVFileEntry]:
        uv_file_reader = UVFileReader(self.uv_file_name)
        return uv_file_reader.get_uv_file_entries()

    @threaded_cached_property
    def ozone(self) -> Ozone:
        return read_ozone_from_b_file(self.b_file_name)

    @threaded_cached_property
    def calibration(self):
        return read_calibration_file(self.calibration_file_name)

    @threaded_cached_property
    def arf(self):
        return read_arf_file(self.arf_file_name, self.arf_direction)

    @threaded_cached_property
    def cloud_cover(self) -> CloudCover:
        position = self.uv_file_entries[0].header.position
        date = self.uv_file_entries[0].header.date
        return get_cloud_cover(position.latitude, position.longitude, date)

    def cos_correction_to_apply(self, time: float) -> CosCorrection:
        if self.no_coscor:
            return CosCorrection.NONE
        elif self.cloud_cover.is_diffuse(time):
            return CosCorrection.DIFFUSE
        else:
            return CosCorrection.CLEAR_SKY

    def to_hash(self) -> str:
        return hex(hash(self))[-6:]


class CosCorrection(Enum):
    DIFFUSE = "diffuse"
    CLEAR_SKY = "clear_sky"
    NONE = "none"
