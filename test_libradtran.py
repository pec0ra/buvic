from libradtran import Libradtran, LibradtranInput

libradtran = Libradtran()
libradtran.add_input(LibradtranInput.WAVELENGTH, [290, 360])
libradtran.add_output("lambda")
libradtran.add_output("edir")
libradtran.add_output("edn")
libradtran.add_output("eglo")
libradtran_result = libradtran.calculate()
print(libradtran_result)
