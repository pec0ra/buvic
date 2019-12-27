from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from enum import Enum
from logging import getLogger
from os import path

from buvic.brewer_infos import StraylightCorrection
from buvic.logic.parameter_file import Angstrom

LOG = getLogger(__name__)

SETTINGS_FILE_PATH = path.join(path.expanduser("~"), '.buvic-settings.conf')

DEFAULT_MANUAL_MODE = False
DEFAULT_ARF_COLUMN = 3
DEFAULT_NO_COSCOR = False
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

    no_coscor: bool = DEFAULT_NO_COSCOR

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
                dict_settings["no_coscor"],
                dict_settings["default_albedo"],
                Angstrom(dict_settings["default_aerosol"][0], dict_settings["default_aerosol"][1]),
                dict_settings["default_ozone"],
                StraylightCorrection(dict_settings["default_straylight_correction"]),
                DataSource(dict_settings["uv_data_source"]),
                DataSource(dict_settings["ozone_data_source"]),
                DataSource(dict_settings["uvr_data_source"])
            )
