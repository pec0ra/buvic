#
# Copyright (c) 2020 Basile Maret.
#
# This file is part of BUVIC - Brewer UV Irradiance Calculator
# (see https://github.com/pec0ra/buvic).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from logging import getLogger
from typing import List, Optional, Iterable

from cached_property import cached_property

from buvic.logic.calibration_file import Calibration, EubrewnetCalibrationProvider, UVRFileCalibrationProvider
from buvic.logic.darksky import get_cloud_cover, CloudCover, ParameterCloudCover
from buvic.logic.file import File
from buvic.logic.ozone import EubrewnetOzoneProvider
from buvic.logic.ozone import Ozone, BFileOzoneProvider
from buvic.logic.parameter_file import Parameters, FileParameterProvider
from buvic.logic.settings import Settings, DataSource
from buvic.logic.utils import date_to_days
from buvic.logic.uv_file import UVFileUVProvider, UVFileEntry, EubrewnetUVProvider, UVProvider
from .arf_file import ARF, FileARFProvider
from .brewer_infos import BFileBrewerModelProvider, EubrewnetBrewerModelProvider
from .warnings import warn

LOG = getLogger(__name__)


@dataclass
class CalculationInput:
    """An input for the `IrradianceCalculation`"""

    brewer_id: str
    date: date
    settings: Settings
    uv_file_name: Optional[File]  # None if the data source is EUBREWNET
    b_file_name: Optional[File]
    calibration_file_name: Optional[File]  # None if the data source is EUBREWNET
    arf_file_name: Optional[File]
    parameter_file_name: Optional[File] = None
    warnings: List[str] = field(default_factory=list)

    @cached_property
    def uv_file_entries(self) -> List[UVFileEntry]:
        if self.settings.uv_data_source == DataSource.FILES:
            if self.uv_file_name is None:
                raise ValueError("UV file should not be None when the data source is FILES")
            uv_file_reader: UVProvider = UVFileUVProvider(self.uv_file_name.full_path)
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
    def brewer_type(self) -> Optional[str]:
        if self.settings.brewer_model_data_source == DataSource.FILES:
            return BFileBrewerModelProvider(self.b_file_name).get_brewer_type()
        else:
            return EubrewnetBrewerModelProvider(self.brewer_id, self.date).get_brewer_type()

    @cached_property
    def calibration(self) -> Calibration:
        if self.settings.uvr_data_source == DataSource.FILES:
            if self.calibration_file_name is None:
                raise ValueError("UVR file should not be None when the data source is FILES")
            return UVRFileCalibrationProvider(self.calibration_file_name.full_path).get_calibration_data()
        else:
            return EubrewnetCalibrationProvider(self.brewer_id, self.date).get_calibration_data()

    @cached_property
    def arf(self) -> Optional[ARF]:
        if self.arf_file_name is None:
            LOG.warning("No arf file specified. Cos correction will not be applied")
            warn(f"ARF file was not found. Cos correction has not been applied")
            return None
        return FileARFProvider(self.arf_file_name.full_path, self.settings.arf_column).get_arf()

    @cached_property
    def parameters(self) -> Parameters:
        return FileParameterProvider(self.parameter_file_name).get_parameters()

    @cached_property
    def cloud_cover(self) -> CloudCover:
        position = self.uv_file_entries[0].header.position
        d = self.uv_file_entries[0].header.date

        days = date_to_days(d)
        parameter_value = self.parameters.cloud_cover(days)
        if parameter_value is not None:
            return ParameterCloudCover(parameter_value)
        else:
            return get_cloud_cover(position.latitude, position.longitude, d)

    def cos_correction_to_apply(self, time: float) -> CosCorrection:
        if self.settings.no_coscor or self.arf is None:
            return CosCorrection.NONE
        elif self.cloud_cover.is_diffuse(time):
            return CosCorrection.DIFFUSE
        else:
            return CosCorrection.CLEAR_SKY

    def init_properties(self) -> None:
        """Call all cached properties to initialize them."""
        uv_file_entries = self.uv_file_entries
        if len(uv_file_entries) == 0:
            return
        ozone = self.ozone
        brewer_type = self.brewer_type
        calibration = self.calibration
        arf = self.arf
        coscor_to_apply = self.cos_correction_to_apply(0)
        parameters = self.parameters
        del uv_file_entries
        del ozone
        del brewer_type
        del calibration
        del arf
        del coscor_to_apply
        del parameters

    def add_warnings(self, warnings: Iterable[str]):
        self.warnings.extend(warnings)


class CosCorrection(Enum):
    DIFFUSE = "diffuse"
    CLEAR_SKY = "clear_sky"
    NONE = "none"
