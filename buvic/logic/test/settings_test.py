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
import os
import unittest

from buvic.logic.brewer_infos import StraylightCorrection
from buvic.logic.settings import Settings, DataSource, WOUDCInfo, Angstrom
from buvic.logic.weighted_irradiance import WeightedIrradianceType


class SettingsTestCase(unittest.TestCase):
    def test_json(self):

        woudc_info = WOUDCInfo(
            agency="Agency",
            version="2.3",
            scientific_authority="SA",
            platform_id="ID",
            platform_name="PN",
            country_iso3="CHE",
            gaw_id="444",
            altitude=444,
        )

        settings = Settings(
            manual_mode=True,
            arf_column=4,
            weighted_irradiance_type=WeightedIrradianceType.VITAMIN_D3,
            no_coscor=True,
            temperature_correction_factor=0.2,
            temperature_correction_ref=24,
            default_albedo=0.2,
            default_aerosol=Angstrom(0.2, 0.4),
            default_ozone=244,
            default_straylight_correction=StraylightCorrection.NOT_APPLIED,
            uv_data_source=DataSource.EUBREWNET,
            ozone_data_source=DataSource.EUBREWNET,
            uvr_data_source=DataSource.EUBREWNET,
            brewer_model_data_source=DataSource.EUBREWNET,
            activate_woudc=True,
            woudc_info=woudc_info,
        )

        settings.write("test_settings.json")

        try:
            loaded_settings = Settings.load("test_settings.json")
            self.assertEqual(settings, loaded_settings)
        finally:
            os.remove("test_settings.json")

        partial_loaded_settings = Settings.load("buvic/logic/test/partial_settings.json")
        self.assertEqual(False, partial_loaded_settings.manual_mode)
        self.assertEqual(4, partial_loaded_settings.arf_column)
        self.assertEqual(1.3, partial_loaded_settings.default_aerosol.alpha)
        self.assertEqual(0.4, partial_loaded_settings.default_aerosol.beta)
        self.assertEqual(StraylightCorrection.NOT_APPLIED, partial_loaded_settings.default_straylight_correction)
        self.assertEqual(DataSource.EUBREWNET, settings.brewer_model_data_source)
        self.assertEqual(True, partial_loaded_settings.activate_woudc)
        self.assertEqual("Agency", partial_loaded_settings.woudc_info.agency)
        self.assertEqual("2.3", partial_loaded_settings.woudc_info.version)
        self.assertEqual("", partial_loaded_settings.woudc_info.scientific_authority)
        self.assertEqual("", partial_loaded_settings.woudc_info.platform_id)
        self.assertEqual("", partial_loaded_settings.woudc_info.platform_name)
        self.assertEqual("", partial_loaded_settings.woudc_info.country_iso3)
        self.assertEqual("", partial_loaded_settings.woudc_info.gaw_id)
        self.assertEqual(444, partial_loaded_settings.woudc_info.altitude)
