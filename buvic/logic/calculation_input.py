from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from typing import List, Optional

from cached_property import cached_property

from buvic.logic.b_file import read_b_file, BFile
from buvic.logic.calibration_file import read_calibration_file, Calibration
from buvic.logic.darksky import get_cloud_cover, CloudCover, ParameterCloudCover
from buvic.logic.file import File
from buvic.logic.parameter_file import Parameters, read_parameter_file, Angstrom
from buvic.logic.utils import date_to_days
from buvic.logic.uv_file import UVFileReader, UVFileEntry
from .arf_file import Direction, read_arf_file, ARF

LOG = getLogger(__name__)


@dataclass
class CalculationInput:
    """
    An input for the `IrradianceCalculation`
    """
    input_parameters: InputParameters
    uv_file_name: File
    b_file_name: Optional[File]
    calibration_file_name: File
    arf_file_name: Optional[File]
    arf_direction: Direction = Direction.SOUTH
    parameter_file_name: Optional[File] = None

    @cached_property
    def uv_file_entries(self) -> List[UVFileEntry]:
        uv_file_reader = UVFileReader(self.uv_file_name.full_path)
        return uv_file_reader.get_uv_file_entries()

    @cached_property
    def b_file(self) -> BFile:
        return read_b_file(self.b_file_name)

    @cached_property
    def calibration(self) -> Calibration:
        return read_calibration_file(self.calibration_file_name.full_path)

    @cached_property
    def arf(self) -> Optional[ARF]:
        if self.arf_file_name is None:
            LOG.warning("No arf file specified. Cos correction will not be applied")
            return None
        return read_arf_file(self.arf_file_name.full_path, self.arf_direction)

    @cached_property
    def parameters(self) -> Parameters:
        return read_parameter_file(self.parameter_file_name)

    @cached_property
    def cloud_cover(self) -> CloudCover:
        position = self.uv_file_entries[0].header.position
        date = self.uv_file_entries[0].header.date

        days = date_to_days(date)
        parameter_value = self.parameters.cloud_cover(days)
        if parameter_value is not None:
            return ParameterCloudCover(parameter_value)
        else:
            return get_cloud_cover(position.latitude, position.longitude, date)

    def cos_correction_to_apply(self, time: float) -> CosCorrection:
        if self.input_parameters.no_coscor or self.arf is None:
            return CosCorrection.NONE
        elif self.cloud_cover.is_diffuse(time):
            return CosCorrection.DIFFUSE
        else:
            return CosCorrection.CLEAR_SKY

    def init_properties(self) -> None:
        """
        Call all cached properties to initialize them.
        """
        uv_file_entries = self.uv_file_entries
        b_file = self.b_file
        calibration = self.calibration
        arf = self.arf
        cloud_cover = self.cloud_cover
        del uv_file_entries
        del b_file
        del calibration
        del arf
        del cloud_cover


@dataclass
class InputParameters:
    default_albedo: float
    default_aerosol: Angstrom
    default_ozone: float
    no_coscor: bool = False


class CosCorrection(Enum):
    DIFFUSE = "diffuse"
    CLEAR_SKY = "clear_sky"
    NONE = "none"
