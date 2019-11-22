import sys, os

from shutil import rmtree

import matplotlib.pyplot as plt

from irradiance_evaluation import IrradianceEvaluation

uv_file_name = sys.argv[1]
calibration_file_name = sys.argv[2]
arf_file_name = sys.argv[3]

plot_output_dir = "plots/"
if len(sys.argv) > 4:
    plot_output_dir = sys.argv[4]

ie = IrradianceEvaluation(uv_file_name, calibration_file_name, arf_file_name)
results = ie.calculate()


if os.path.exists(plot_output_dir):
    print('Overwriting last output')
    rmtree(plot_output_dir)

os.makedirs(plot_output_dir)

i = 0
for result in results:
    print(i)
    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="Irradiance (Wm-2 nm-1)", title="Irradiance for SZA: " + str(result.sza))
    ax.grid()

    ax.semilogy(result.wavelengths, result.original_spectrum, label="Spectrum")

    ax.semilogy(result.wavelengths, result.cos_corrected_spectrum, label="Cos corrected spectrum")

    fig.legend()
    fig.savefig(plot_output_dir + "spectrum_" + str(i) + ".eps")
    plt.show()

    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="c", title="Correction factor for SZA: " + str(result.sza))
    ax.grid()

    ax.plot(result.wavelengths, result.cos_correction, label="Cglo")

    fig.legend()
    fig.savefig(plot_output_dir + "spectrum_" + str(i) + "_correction.eps")
    plt.show()
    i += 1
