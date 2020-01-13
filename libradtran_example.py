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
from buvic.logic.libradtran import Libradtran, LibradtranInput

libradtran = Libradtran()
libradtran.add_input(LibradtranInput.WAVELENGTH, [290, 360])
libradtran.add_input(LibradtranInput.LATITUDE, ["N", 46.7828])
libradtran.add_input(LibradtranInput.LONGITUDE, ["E", 9.6754])
libradtran.add_input(LibradtranInput.TIME, [2019, 11, 21, 13, 20, 30])

libradtran.add_output("lambda")
libradtran.add_output("edir")
libradtran.add_output("eglo")
libradtran.add_output("sza")
libradtran_result = libradtran.calculate()

print(libradtran_result.columns["sza"])
