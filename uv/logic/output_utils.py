from os import path
from typing import Tuple, List

from matplotlib import pyplot as plt

from uv.logic.result import Result


def create_csv(saving_dir: str, result: Result) -> str:
    file_name = result.get_name()
    with open(path.join(saving_dir, file_name), "w") as csv_file:
        result.to_qasume(csv_file)
    return file_name


def create_spectrum_plots(saving_dir: str, result: Result, file_type: str = "png") -> Tuple[str, str]:
    """
    Plots the correction factor and the uv spectrum against wavelengths.

    This creates two plot:
        1. the UV spectrum (both cos corrected and non cos corrected) against wavelengths
        2. the correction factor against the wavelengths

    This gets the required data from the given result and saves the plots in the given directory with the given
    format

    :param saving_dir: the directory to save the plots in
    :param result: the result to get the data from
    :param file_type: the extension of the plots to save (e.g. 'png', 'svg', 'pdf')
    :return: the file names of the created plots
    """
    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="Irradiance (Wm-2 nm-1)")
    ax.grid()

    ax.semilogy(result.spectrum.wavelengths, result.spectrum.original_spectrum, label="Spectrum")

    ax.semilogy(result.spectrum.wavelengths, result.spectrum.cos_corrected_spectrum, label="Cos corrected spectrum")

    ax.legend()
    file_path = get_spectrum_plot_name(result, file_type)
    fig.savefig(path.join(saving_dir, file_path))

    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="Correction factor")
    ax.grid()

    ax.plot(result.spectrum.wavelengths, result.spectrum.cos_correction, label="Correction factor")

    ax.legend()
    file_path_correction = get_corrected_spectrum_plot_name(result, file_type)
    fig.savefig(path.join(saving_dir, file_path_correction))
    plt.close('all')

    return file_path, file_path_correction


def create_sza_plot(saving_dir: str, results: List[Result], file_type: str = "png") -> str:
    """
    Plots the correction factor against solar zenith angles.

    This gets the required data from the given result list and saves the plot in the given directory with the given
    format

    :param saving_dir: the directory to save the plot in
    :param results: the list of results to get the data from
    :param file_type: the extension of the plot to save (e.g. 'png', 'svg', 'pdf')
    :return: the file name of the created plot
    """
    wavelengths = [295, 310, 325]

    sorted_results = sorted([*results], key=lambda x: x.sza)
    szas = [r.sza for r in sorted_results]
    fig, ax = plt.subplots()
    ax.set(xlabel="SZA", ylabel="Correction factor")
    ax.grid()

    for wl in wavelengths:
        data = [r.spectrum.cos_correction[r.spectrum.wavelengths.index(wl)] for r in sorted_results]
        ax.plot(szas, data, label="WL = " + str(wl) + "nm")

    plt.title("Correction factor")
    ax.legend()
    first_result = results[0]
    sza_plot_name_correction = get_sza_correction_plot_name(first_result, file_type)
    fig.savefig(path.join(saving_dir, sza_plot_name_correction))
    plt.close('all')

    return sza_plot_name_correction


def get_spectrum_plot_name(result: Result, file_type: str = "png") -> str:
    return result.get_name(suffix=".spectrum." + file_type)


def get_corrected_spectrum_plot_name(result: Result, file_type: str = "png") -> str:
    return result.get_name(suffix=".corrected_spectrum." + file_type)


def get_sza_correction_plot_name(result: Result, file_type: str = "png") -> str:
    return result.get_name(suffix=".correction." + file_type)
