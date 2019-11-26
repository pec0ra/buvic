import os
import sys
from datetime import date
from shutil import rmtree

import matplotlib.pyplot as plt
from matplotlib import rcParams

from uv.logic.irradiance_evaluation import IrradianceEvaluation
from uv.logic.calculation_input import CalculationInput

DATA_DIR = "../Misc/data/"

rcParams.update({'figure.autolayout': True})
rcParams['figure.figsize'] = 10, 7

plot_output_dir = "plots/"
if len(sys.argv) == 3:
    days = sys.argv[1]
    brewer_id = sys.argv[2]
    calculation_input = CalculationInput.from_days_and_bid(DATA_DIR, brewer_id, days)
else:
    calculation_input = CalculationInput(
        date.today(),
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4]
    )

    if len(sys.argv) > 4:
        plot_output_dir = sys.argv[4]

ie = IrradianceEvaluation(calculation_input)
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

    spectrum = result.spectrum
    ax.semilogy(spectrum.wavelengths, spectrum.original_spectrum, label="Spectrum")

    ax.semilogy(spectrum.wavelengths, spectrum.cos_corrected_spectrum, label="Cos corrected spectrum")

    plt.title("Irradiance for SZA: " + str(result.sza))
    ax.legend()
    fig.savefig(plot_output_dir + "spectrum_" + str(i) + ".eps")

    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="c")
    ax.grid()

    ax.plot(spectrum.wavelengths, spectrum.cos_correction, label="Cglo")

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

wl_300 = [r.spectrum.cos_corrected_spectrum[r.spectrum.wavelengths.index(300)] for r in sorted_results]
wl_320 = [r.spectrum.cos_corrected_spectrum[r.spectrum.wavelengths.index(320)] for r in sorted_results]
wl_340 = [r.spectrum.cos_corrected_spectrum[r.spectrum.wavelengths.index(340)] for r in sorted_results]

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

wl_300 = [r.spectrum.cos_correction[r.spectrum.wavelengths.index(300)] for r in sorted_results]
wl_320 = [r.spectrum.cos_correction[r.spectrum.wavelengths.index(320)] for r in sorted_results]
wl_340 = [r.spectrum.cos_correction[r.spectrum.wavelengths.index(340)] for r in sorted_results]

ax.plot(szas, wl_300, label="WL = 300nm")
ax.plot(szas, wl_320, label="WL = 320nm")
ax.plot(szas, wl_340, label="WL = 340nm")

plt.title("Correction factor")
ax.legend()
fig.savefig(plot_output_dir + "correction_szas.eps")
