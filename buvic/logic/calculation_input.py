from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from logging import getLogger
from typing import List, Optional, Iterable
from warnings import warn, WarningMessage

from cached_property import cached_property

from buvic.brewer_infos import StraylightCorrection
from buvic.logic.calibration_file import Calibration, EubrewnetCalibrationProvider, UVRFileCalibrationProvider
from buvic.logic.darksky import get_cloud_cover, CloudCover, ParameterCloudCover
from buvic.logic.file import File
from buvic.logic.ozone import EubrewnetOzoneProvider
from buvic.logic.ozone import Ozone, BFileOzoneProvider
from buvic.logic.parameter_file import Parameters, read_parameter_file
from buvic.logic.settings import Settings, DataSource
from buvic.logic.utils import date_to_days
from buvic.logic.uv_file import UVFileUVProvider, UVFileEntry, EubrewnetUVProvider
from .arf_file import read_arf_file, ARF

LOG = getLogger(__name__)


@dataclass
class CalculationInput:
    """
    An input for the `IrradianceCalculation`
    """
    brewer_id: str
    date: date
    settings: Settings
    uv_file_name: Optional[File]  # None if the data source is EUBREWNET
    b_file_name: Optional[File]
    calibration_file_name: Optional[File]  # None if the data source is EUBREWNET
    arf_file_name: Optional[File]
    straylight_correction: StraylightCorrection
    parameter_file_name: Optional[File] = None
    warnings: List[WarningMessage] = field(default_factory=list)

    @cached_property
    def uv_file_entries(self) -> List[UVFileEntry]:
        if self.settings.uv_data_source == DataSource.FILES:
            uv_file_reader = UVFileUVProvider(self.uv_file_name.full_path)
        else:
            uv_file_reader = EubrewnetUVProvider(self.brewer_id, self.date)
        return uv_file_reader.get_uv_file_entries()

    @cached_property
    def ozone(self) -> Ozone:
        if self.settings.ozone_data_source == DataSource.FILES:
            return BFileOzoneProvider(self.b_file_name).get_ozone_data()
        else:
            return EubrewnetOzoneProvider(self.brewer_id, self.date).get_ozone_data()

    @cached_property
    def calibration(self) -> Calibration:
        if self.settings.uvr_data_source == DataSource.FILES:
            return UVRFileCalibrationProvider(self.calibration_file_name.full_path).get_calibration_data()
        else:
            return EubrewnetCalibrationProvider(self.brewer_id, self.date).get_calibration_data()

    @cached_property
    def arf(self) -> Optional[ARF]:
        if self.arf_file_name is None:
            LOG.warning("No arf file specified. Cos correction will not be applied")
            warn(f"ARF file was not found. Cos correction has not been applied")
            return None
        return read_arf_file(self.arf_file_name.full_path, self.settings.arf_column)

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
        if self.settings.no_coscor or self.arf is None:
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
        if len(uv_file_entries) == 0:
            return
        ozone = self.ozone
        calibration = self.calibration
        arf = self.arf
        cloud_cover = self.cloud_cover
        del uv_file_entries
        del ozone
        del calibration
        del arf
        del cloud_cover

    def add_warnings(self, warnings: Iterable[WarningMessage]):
        self.warnings.extend(warnings)


class CosCorrection(Enum):
    DIFFUSE = "diffuse"
    CLEAR_SKY = "clear_sky"
    NONE = "none"
