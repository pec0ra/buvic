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
from dataclasses import dataclass, asdict
from enum import Enum
from logging import getLogger
from os import path

from buvic.logic.brewer_infos import StraylightCorrection
from buvic.logic.parameter_file import Angstrom
from buvic.logic.weighted_irradiance import WeightedIrradianceType

LOG = getLogger(__name__)

SETTINGS_FILE_PATH = path.join(path.expanduser("~"), '.buvic-settings.conf')

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


class DataSource(str, Enum):
    FILES = "Files"
    EUBREWNET = "EUBREWNET"


@dataclass
class Settings:
    manual_mode: bool = DEFAULT_MANUAL_MODE

    arf_column: int = DEFAULT_ARF_COLUMN

    weighted_irradiance_type: WeightedIrradianceType = DEFAULT_WEIGHTED_IRRADIANCE_TYPE

    no_coscor: bool = DEFAULT_NO_COSCOR

    temperature_correction_factor: float = DEFAULT_TEMPERATURE_CORRECTION_FACTOR
    temperature_correction_ref: float = DEFAULT_TEMPERATURE_CORRECTION_REF

    default_albedo: float = DEFAULT_ALBEDO_VALUE
    default_aerosol: Angstrom = Angstrom(DEFAULT_ALPHA_VALUE, DEFAULT_BETA_VALUE)
    default_ozone: float = DEFAULT_OZONE_VALUE
    default_straylight_correction: StraylightCorrection = StraylightCorrection.APPLIED

    uv_data_source: DataSource = DataSource.FILES
    ozone_data_source: DataSource = DataSource.FILES
    uvr_data_source: DataSource = DataSource.FILES

    def write(self):
        with open(SETTINGS_FILE_PATH, 'w') as config_file:
            json.dump(asdict(self), config_file)
        LOG.debug(f"Settings saved successfully to {SETTINGS_FILE_PATH}")

    @staticmethod
    def load() -> Settings:
        if not path.exists(SETTINGS_FILE_PATH):
            LOG.debug(f"No setting file found, using default")
            return Settings()

        with open(SETTINGS_FILE_PATH, 'r') as config_file:
            dict_settings = json.load(config_file)
            LOG.debug(f"Settings loaded from {SETTINGS_FILE_PATH}")
            return Settings(
                dict_settings["manual_mode"],
                dict_settings["arf_column"],
                WeightedIrradianceType(dict_settings["weighted_irradiance_type"])
                if "weighted_irradiance_type" in dict_settings else DEFAULT_WEIGHTED_IRRADIANCE_TYPE,
                dict_settings["no_coscor"],
                dict_settings["temperature_correction_factor"]
                if "temperature_correction_factor" in dict_settings else DEFAULT_TEMPERATURE_CORRECTION_FACTOR,
                dict_settings["temperature_correction_ref"]
                if "temperature_correction_ref" in dict_settings else DEFAULT_TEMPERATURE_CORRECTION_REF,
                dict_settings["default_albedo"],
                Angstrom(dict_settings["default_aerosol"][0], dict_settings["default_aerosol"][1]),
                dict_settings["default_ozone"],
                StraylightCorrection(dict_settings["default_straylight_correction"]),
                DataSource(dict_settings["uv_data_source"]),
                DataSource(dict_settings["ozone_data_source"]),
                DataSource(dict_settings["uvr_data_source"])
            )
