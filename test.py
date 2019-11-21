import sys

import matplotlib.pyplot as plt

from uv_file import UVFileReader

file = sys.argv[1]

uv_file_reader = UVFileReader(file)

uv_file_entry = uv_file_reader.get_uv_file_entries()[2]

fig, ax = plt.subplots()
ax.set(xlabel="Wavelength", ylabel="Events")
ax.grid()

ax.semilogy([v.wavelength for v in uv_file_entry.values], [v.events for v in uv_file_entry.values])

plt.show()

fig, ax = plt.subplots()
ax.set(xlabel="Wavelength", ylabel="Photos/sec")
ax.grid()

abs_values = uv_file_entry.convert_to_abs()
ax.semilogy([v.wavelength for v in uv_file_entry.values], abs_values)

plt.show()
