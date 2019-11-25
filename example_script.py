import os
import sys
from shutil import rmtree

import matplotlib.pyplot as plt
from matplotlib import rcParams

from uv.logic import IrradianceEvaluation

rcParams.update({'figure.autolayout': True})
rcParams['figure.figsize'] = 10, 7

uv_file_name = sys.argv[1]
calibration_file_name = sys.argv[2]
arf_file_name = sys.argv[3]

plot_output_dir = "plots/"
if len(sys.argv) > 4:
    plot_output_dir = sys.argv[4]

ie = IrradianceEvaluation(uv_file_name, calibration_file_name, "../B04916.156", arf_file_name)
results = ie.calculate()

if os.path.exists(plot_output_dir):
    print('Overwriting last output')
    rmtree(plot_output_dir)

os.makedirs(plot_output_dir)

i = 0
for result in results:
    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="Irradiance (Wm-2 nm-1)")
    ax.grid()

    ax.semilogy(result.wavelengths, result.original_spectrum, label="Spectrum")

    ax.semilogy(result.wavelengths, result.cos_corrected_spectrum, label="Cos corrected spectrum")

    plt.title("Irradiance for SZA: " + str(result.sza))
    ax.legend()
    fig.savefig(plot_output_dir + "spectrum_" + str(i) + ".eps")

    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="c")
    ax.grid()

    ax.plot(result.wavelengths, result.cos_correction, label="Cglo")

    plt.title("Correction factor for SZA: " + str(result.sza))
    ax.legend()
    fig.savefig(plot_output_dir + "spectrum_" + str(i) + "_correction.eps")
    i += 1

# sorted_results = sorted(results, key=lambda x: x.sza)[:-1]
sorted_results = results[1:]

szas = [r.sza for r in sorted_results]

fig, ax = plt.subplots()
ax.set(xlabel="SZA", ylabel="Irradiance (Wm-2 nm-1)")
ax.grid()

wl_300 = [r.cos_corrected_spectrum[r.wavelengths.index(300)] for r in sorted_results]
wl_320 = [r.cos_corrected_spectrum[r.wavelengths.index(320)] for r in sorted_results]
wl_340 = [r.cos_corrected_spectrum[r.wavelengths.index(340)] for r in sorted_results]

ax.plot(szas, wl_300, label="WL = 300nm")
ax.plot(szas, wl_320, label="WL = 320nm")
ax.plot(szas, wl_340, label="WL = 340nm")

plt.title("Irradiance")
ax.legend()
fig.savefig(plot_output_dir + "spectrum_szas.eps")

sorted_results = sorted(sorted_results, key=lambda x: x.sza)
szas = [r.sza for r in sorted_results]
fig, ax = plt.subplots()
ax.set(xlabel="SZA", ylabel="Correction factor")
ax.grid()

wl_300 = [r.cos_correction[r.wavelengths.index(300)] for r in sorted_results]
wl_320 = [r.cos_correction[r.wavelengths.index(320)] for r in sorted_results]
wl_340 = [r.cos_correction[r.wavelengths.index(340)] for r in sorted_results]

ax.plot(szas, wl_300, label="WL = 300nm")
ax.plot(szas, wl_320, label="WL = 320nm")
ax.plot(szas, wl_340, label="WL = 340nm")

plt.title("Correction factor")
ax.legend()
fig.savefig(plot_output_dir + "correction_szas.eps")
