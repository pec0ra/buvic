from datetime import timedelta, date, time
from typing import Tuple, List, Any

import matplotlib.pyplot as plt


def days_to_date(days: int, year: int) -> date:
    if days < 1 or days > 366:
        raise ValueError("Days must be between 1 and 365")
    if year < 2000:
        year += 2000
    return date(year, 1, 1) + timedelta(days=days - 1)


def date_to_days(d: date) -> int:
    return d.timetuple().tm_yday


def minutes_to_time(minutes: float) -> time:
    td = timedelta(minutes=minutes)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hour=hours, minute=minutes, second=seconds)


def time_to_minutes(t: time) -> float:
    td = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    return td.seconds / 60


def create_spectrum_plots(saving_dir: str, result, file_type: str = "png") -> Tuple[str, str]:
    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="Irradiance (Wm-2 nm-1)")
    ax.grid()

    ax.semilogy(result.spectrum.wavelengths, result.spectrum.original_spectrum, label="Spectrum")

    ax.semilogy(result.spectrum.wavelengths, result.spectrum.cos_corrected_spectrum, label="Cos corrected spectrum")

    ax.legend()
    file_path = result.get_name("spectrum_", "." + file_type)
    fig.savefig(saving_dir + file_path)
    plt.close()

    fig, ax = plt.subplots()
    ax.set(xlabel="Wavelength (nm)", ylabel="Correction factor")
    ax.grid()

    ax.plot(result.spectrum.wavelengths, result.spectrum.cos_correction, label="Correction factor")

    ax.legend()
    file_path_correction = result.get_name("spectrum_", "_correction." + file_type)
    fig.savefig(saving_dir + file_path_correction)
    plt.close()

    return file_path, file_path_correction


def create_sza_plot(saving_dir: str, results: List[Any], file_type: str = "png") -> str:
    # sorted_results = sorted(results, key=lambda x: x.sza)[:-1]
    wavelengths = [295, 310, 325]

    sorted_results = sorted(results, key=lambda x: x.sza)
    szas = [r.sza for r in sorted_results]
    fig, ax = plt.subplots()
    ax.set(xlabel="SZA", ylabel="Correction factor")
    ax.grid()

    for wl in wavelengths:
        data = [r.spectrum.cos_correction[r.spectrum.wavelengths.index(wl)] for r in sorted_results]
        ax.plot(szas, data, label="WL = " + str(wl) + "nm")

    plt.title("Correction factor")
    ax.legend()
    bid = results[0].uv_file_entry.brewer_info.id
    sza_plot_name_correction = "correction_" + bid + "_" + results[
        0].calculation_input.measurement_date.isoformat().replace('-',
                                                                  '') + "_" + results[
                                   0].calculation_input.to_hash() + "." + file_type
    fig.savefig(saving_dir + sza_plot_name_correction)

    return sza_plot_name_correction
