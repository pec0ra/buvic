import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List

import matplotlib.pyplot as plt
import remi.gui as gui
from remi import App

from uv.logic.calculation_input import CalculationInput
from .const import PLOT_DIR, TMP_FILE_DIR
from .gui.utils import show, hide
from .gui.widgets import VBox, Title, Level, ResultInfo, Loader, SimpleMainForm
from .logic.irradiance_evaluation import IrradianceEvaluation, Spectrum


class UVApp(App):
    def __init__(self, *args):
        super(UVApp, self).__init__(*args, static_file_path={'plots': PLOT_DIR})
        self._executor = ThreadPoolExecutor(1)
        self.uv_file = None
        self.calibration_file = None
        self.arf_file = None
        self.b_file = None

    def main(self):
        self.main_container = gui.VBox(width="80%")
        self.main_container.set_style("margin: 30px auto; padding: 20px")

        self.title = Title(Level.H1, "Irradiance calculation")

        self.main_form = SimpleMainForm(self.calculate)

        self.loader = Loader()

        self.result_container = VBox()
        self.result_container.set_style("margin-bottom: 20px")
        hide(self.result_container)
        self.result_title = Title(Level.H2, "Results")
        self.result_container.append(self.result_title)

        self.main_container.append(self.title)
        self.main_container.append(self.loader)
        self.main_container.append(self.main_form)
        self.main_container.append(self.result_container)

        self.error_label = gui.Label("")
        self.error_label.set_style("color: #E00; font-size: 12pt; font-weight: bold")
        hide(self.error_label)
        self.main_container.append(self.error_label)

        # returning the root widget
        return self.main_container

    def calculate(self, calculation_input: CalculationInput):
        self.reset_errors()
        self.loader.set_progress(0)
        self.loader.set_label("Calculating...")
        show(self.loader)
        hide(self.main_form)
        hide(self.result_container)

        ie = IrradianceEvaluation(calculation_input,
                                  progress_handler=self.progress_handler)
        self._executor.submit(self.start_calculation, ie)

    def start_calculation(self, ie: IrradianceEvaluation):
        try:
            result = ie.calculate()
            self.show_result(result)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            self.show_error(str(e))
            raise e

    def reset_errors(self):
        hide(self.error_label)
        self.error_label.set_text("")

    def progress_handler(self, current_progress: int, total_progress: int):
        if total_progress == 0:
            self.loader.set_progress(0)
        else:
            value = int(current_progress * 80 / total_progress)
            self.loader.set_progress(value)

    def show_result(self, results: List[Spectrum]):
        self.result_container.empty()
        self.result_container.append(self.result_title)
        self.loader.set_label("Generating result files...")
        i = 0
        self.loader.set_progress(80)
        for result in results:
            self.add_result_to_gui(result, i)
            i += 1
            self.loader.set_progress(80 + int(i * 20 / len(results)))
        self.main_form.check_files()
        hide(self.loader)
        show(self.main_form)
        show(self.result_container)

    def show_error(self, error: str):
        self.main_form.check_files()
        hide(self.result_container)
        hide(self.loader)
        show(self.main_form)
        show(self.error_label)
        if error is not None:
            self.error_label.set_text(error)
        else:
            print("Error is None")

    def add_result_to_gui(self, result: Spectrum, i: int):
        vbox = VBox()
        vbox.set_style("margin-bottom: 20px")

        result_title = Title(Level.H3, "Section " + str(i))
        vbox.append(result_title)

        header = result.uv_file_entry.header

        info = ResultInfo("Measure type", header.type)
        vbox.append(info)

        info = ResultInfo("SZA", result.sza)
        vbox.append(info)

        info = ResultInfo("Pressure", header.pressure)
        vbox.append(info)

        info = ResultInfo("Position", str(header.position.latitude) + ", " + str(header.position.longitude))
        vbox.append(info)

        info = ResultInfo("Dark", header.dark)
        vbox.append(info)

        time = result.measurement_times[0]
        info = ResultInfo("Ozone", result.ozone.interpolated_value(time))
        vbox.append(info)

        file_name = TMP_FILE_DIR + str(uuid.uuid4()) + ".csv"
        with open(file_name, "w") as csv_file:
            result.to_csv(csv_file)

        download_button = gui.FileDownloader("Download as csv", file_name, width=130)
        download_button.set_style("margin-bottom: 10px; margin-top: 5px")
        # download_button.onclick.do(lambda widget: self.download_as_csv(widget, result))
        vbox.append(download_button)

        hbox = gui.HBox()

        fig, ax = plt.subplots()
        ax.set(xlabel="Wavelength (nm)", ylabel="Irradiance (Wm-2 nm-1)")
        ax.grid()

        ax.semilogy(result.wavelengths, result.original_spectrum, label="Spectrum")

        ax.semilogy(result.wavelengths, result.cos_corrected_spectrum, label="Cos corrected spectrum")

        ax.legend()
        fig.savefig(PLOT_DIR + "spectrum_" + str(i) + ".png")
        plt.close()

        pic = gui.Image("/plots:spectrum_" + str(i) + ".png")
        hbox.append(pic)

        fig, ax = plt.subplots()
        ax.set(xlabel="Wavelength (nm)", ylabel="Correction factor")
        ax.grid()

        ax.plot(result.wavelengths, result.cos_correction, label="Cglo")

        ax.legend()
        fig.savefig(PLOT_DIR + "spectrum_" + str(i) + "_correction.png")
        plt.close()

        pic = gui.Image("/plots:spectrum_" + str(i) + "_correction.png")
        hbox.append(pic)
        vbox.append(hbox)
        self.result_container.append(vbox)
