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
import unittest
from datetime import date

from buvic.logic.calculation_input import CalculationInput
from buvic.logic.irradiance_calculation import IrradianceCalculation
from buvic.logic.settings import Settings


class IrradianceCalculationTestCase(unittest.TestCase):
    def test_air_mass_calculation(self):
        calculation = IrradianceCalculationTest(CalculationInput("033", date.today(), Settings(), None, None, None, None, None, None, []))

        air_mass = calculation.calculate_air_mass(75.0)
        self.assertAlmostEqual(3.69, air_mass, 2)

        air_mass = calculation.calculate_air_mass(85.0)
        self.assertAlmostEqual(8.33, air_mass, 2)


class IrradianceCalculationTest(IrradianceCalculation):
    def calculate_air_mass(self, sza: float):
        return self._calculate_air_mass(sza)
