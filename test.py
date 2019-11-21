import os
import sys

import matplotlib.pyplot as plt

from calibration_file import read_calibration_file
from uv_file import UVFileReader

file = sys.argv[1]
uv_file_name = sys.argv[1]
calibration_file_name = sys.argv[2]

uv_file_reader = UVFileReader(uv_file_name)
uv_file_entry = uv_file_reader.get_uv_file_entries()[1]

calibration = read_calibration_file(calibration_file_name)

fig, ax = plt.subplots()
ax.set(xlabel="Wavelength (nm)", ylabel="Event counts")
ax.grid()

ax.semilogy(uv_file_entry.wavelengths, uv_file_entry.events)

fig.savefig("plots/" + os.path.basename(uv_file_name) + "_raw.eps")
plt.show()

fig, ax = plt.subplots()
ax.set(xlabel="Wavelength (nm)", ylabel="Irradiance (Wm-2 nm-1)")
ax.grid()

abs_values = uv_file_entry.to_calibrated_spectrum(calibration)
ax.semilogy(uv_file_entry.wavelengths, abs_values)

fig.savefig("plots/" + os.path.basename(uv_file_name) + "_corrected.eps")
plt.show()
