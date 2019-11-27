from uv.logic import Libradtran, LibradtranInput

libradtran = Libradtran()
libradtran.add_input(LibradtranInput.WAVELENGTH, [290, 360])
libradtran.add_input(LibradtranInput.LATITUDE, ['N', 46.7828])
libradtran.add_input(LibradtranInput.LONGITUDE, ['E', 9.6754])
libradtran.add_input(LibradtranInput.TIME, [2019, 11, 21, 13, 20, 30])

libradtran.add_output("lambda")
libradtran.add_output("edir")
libradtran.add_output("eglo")
libradtran.add_output("sza")
libradtran_result = libradtran._calculate()

print(libradtran_result.columns["sza"])
