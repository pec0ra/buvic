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

import json
from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from os import path

from dataclasses_json import dataclass_json

from buvic.logic.brewer_infos import StraylightCorrection
from buvic.logic.weighted_irradiance import WeightedIrradianceType

LOG = getLogger(__name__)

SETTINGS_FILE_PATH = path.join(path.expanduser("~"), ".buvic-settings.conf")

DEFAULT_MANUAL_MODE = False
DEFAULT_ARF_COLUMN = 3
DEFAULT_WEIGHTED_IRRADIANCE_TYPE = WeightedIrradianceType.ERYTHEMAL
DEFAULT_NO_COSCOR = False
DEFAULT_TEMPERATURE_CORRECTION_FACTOR = 0.0
DEFAULT_TEMPERATURE_CORRECTION_REF = 0.0
DEFAULT_ALBEDO_VALUE = 0.04
DEFAULT_ALPHA_VALUE = 1.3
DEFAULT_BETA_VALUE = 0.1
DEFAULT_OZONE_VALUE = 300
DEFAULT_ACTIVATE_WOUDC = False
DEFAULT_WOUDC_VERSION = "1.0"


class DataSource(str, Enum):
    FILES = "Files"
    EUBREWNET = "EUBREWNET"


@dataclass_json
@dataclass
class WOUDCInfo:
    # Data generation info
    agency: str = ""
    version: str = DEFAULT_WOUDC_VERSION
    scientific_authority: str = ""

    # Platform info
    platform_id: str = ""
    platform_name: str = ""
    country_iso3: str = ""
    gaw_id: str = ""
    altitude: int = 0


@dataclass_json
@dataclass
class Angstrom:
    alpha: float = DEFAULT_ALPHA_VALUE
    beta: float = DEFAULT_BETA_VALUE


@dataclass_json
@dataclass
class Settings:
    manual_mode: bool = DEFAULT_MANUAL_MODE

    arf_column: int = DEFAULT_ARF_COLUMN

    weighted_irradiance_type: WeightedIrradianceType = DEFAULT_WEIGHTED_IRRADIANCE_TYPE

    no_coscor: bool = DEFAULT_NO_COSCOR

    temperature_correction_factor: float = DEFAULT_TEMPERATURE_CORRECTION_FACTOR
    temperature_correction_ref: float = DEFAULT_TEMPERATURE_CORRECTION_REF

    default_albedo: float = DEFAULT_ALBEDO_VALUE
    default_aerosol: Angstrom = Angstrom()
    default_ozone: float = DEFAULT_OZONE_VALUE
    default_straylight_correction: StraylightCorrection = StraylightCorrection.APPLIED

    uv_data_source: DataSource = DataSource.FILES
    ozone_data_source: DataSource = DataSource.FILES
    uvr_data_source: DataSource = DataSource.FILES
    brewer_model_data_source: DataSource = DataSource.FILES

    activate_woudc: bool = DEFAULT_ACTIVATE_WOUDC
    woudc_info: WOUDCInfo = WOUDCInfo()

    def write(self, file_path: str = SETTINGS_FILE_PATH):
        with open(file_path, "w") as config_file:
            config_file.write(self.to_json())  # type: ignore
        LOG.debug(f"Settings saved successfully to {file_path}")

    @staticmethod
    def load(file_path: str = SETTINGS_FILE_PATH) -> Settings:
        if not path.exists(file_path):
            LOG.info(f"No setting file found, using default")
            return Settings()

        with open(file_path, "r") as config_file:
            dict_settings = json.load(config_file)
            try:
                settings = Settings.from_dict(dict_settings)  # type: ignore
                LOG.debug(f"Settings loaded from {file_path}")
                return settings
            except AttributeError:
                LOG.warning("Setting file could not be parsed. Using default settings")
                return Settings()
