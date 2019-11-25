import os
from concurrent.futures import ThreadPoolExecutor
from typing import List

import matplotlib.pyplot as plt
import remi.gui as gui
from remi import start, App

from irradiance_evaluation import IrradianceEvaluation, Spectrum

TMP_FILE_DIR = "tmp/"
if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)

PLOT_DIR = "plots/"
if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)


class MyApp(App):
    def __init__(self, *args):
        super(MyApp, self).__init__(*args, static_file_path={'plots': PLOT_DIR})
        self._executor = ThreadPoolExecutor(1)
        self.uv_file = None
        self.calibration_file = None
        self.arf_file = None
        self.b_file = None

    def main(self):
        self.main_container = gui.VBox(width="80%")
        self.main_container.set_style("margin: 30px auto; padding: 20px")
        self.main_form = gui.VBox()

        self.title = gui.Label("Irradiance calculation")
        self.title.set_style("font-size: 20pt; margin-bottom: 30px")

        self.file_form = gui.HBox()
        self.file_form.set_style("margin-bottom: 20px")
        self.uv_file_selector = FileSelector("UV File:", handler=self.handle_uv_file)
        self.calibration_file_selector = FileSelector("Calibration File:", handler=self.handle_calibration_file)
        self.b_file_selector = FileSelector("B File:", handler=self.handle_b_file)
        self.arf_file_selector = FileSelector("ARF File:", handler=self.handle_arf_file)

        self.calculate_button = gui.Button("Calculate", width=120)
        self.calculate_button.set_enabled(False)
        self.calculate_button.set_style("align-self: end; margin-bottom: 20px")
        self.calculate_button.onclick.do(self.calculate)

        self.file_form.append(self.uv_file_selector)
        self.file_form.append(self.calibration_file_selector)
        self.file_form.append(self.b_file_selector)
        self.file_form.append(self.arf_file_selector)

        self.main_form.append(self.file_form)
        self.main_form.append(self.calculate_button)

        self.loader = gui.Progress(20, 100)
        self.loader.set_style("display: none")

        self.result_container = gui.VBox()
        self.result_container.set_style("display: none")
        self.main_form.append(self.result_container)

        self.main_container.append(self.title)
        self.main_container.append(self.loader)
        self.main_container.append(self.main_form)

        # returning the root widget
        return self.main_container

    def handle_uv_file(self, file_uploader, file_data, file_name):
        self.uv_file = TMP_FILE_DIR + file_name
        self.check_files()

    def handle_calibration_file(self, file_uploader, file_data, file_name):
        self.calibration_file = TMP_FILE_DIR + file_name
        self.check_files()

    def handle_b_file(self, file_uploader, file_data, file_name):
        self.b_file = TMP_FILE_DIR + file_name
        self.check_files()

    def handle_arf_file(self, file_uploader, file_data, file_name):
        self.arf_file = TMP_FILE_DIR + file_name
        self.check_files()

    def check_files(self):
        if self.uv_file is not None and self.calibration_file is not None and self.arf_file is not None and self.b_file is not None:
            self.calculate_button.set_enabled(True)
        else:
            self.calculate_button.set_enabled(False)

    def calculate(self, widget):
        self.calculate_button.set_enabled(False)
        self.loader.set_style("display: block")
        self.main_form.set_style("display: none")

        ie = IrradianceEvaluation(self.uv_file, self.calibration_file, self.b_file, self.arf_file)
        self._executor.submit(self.start_calculation, ie)

    def start_calculation(self, ie: IrradianceEvaluation):
        result = ie.calculate()
        self.show_result(result)

    def show_result(self, results: List[Spectrum]):
        i = 0
        self.loader.set_value(80)
        for result in results:
            hbox = gui.HBox()

            fig, ax = plt.subplots()
            ax.set(xlabel="Wavelength (nm)", ylabel="Irradiance (Wm-2 nm-1)")
            ax.grid()

            ax.semilogy(result.wavelengths, result.original_spectrum, label="Spectrum")

            ax.semilogy(result.wavelengths, result.cos_corrected_spectrum, label="Cos corrected spectrum")

            plt.title("Irradiance for SZA: " + str(result.sza))
            ax.legend()
            fig.savefig(PLOT_DIR + "spectrum_" + str(i) + ".png")

            pic = gui.Image("/plots:spectrum_" + str(i) + ".png")
            hbox.append(pic)

            fig, ax = plt.subplots()
            ax.set(xlabel="Wavelength (nm)", ylabel="c")
            ax.grid()

            ax.plot(result.wavelengths, result.cos_correction, label="Cglo")

            plt.title("Correction factor for SZA: " + str(result.sza))
            ax.legend()
            fig.savefig(PLOT_DIR + "spectrum_" + str(i) + "_correction.png")
            pic = gui.Image("/plots:spectrum_" + str(i) + "_correction.png")
            hbox.append(pic)
            self.result_container.append(hbox)
            i += 1
            self.loader.set_value(80 + int(i * 20 / len(results)))
        self.calculate_button.set_enabled(True)
        self.loader.set_style("display: none")
        self.main_form.set_style("display: block")
        self.result_container.set_style("display: block")


class FileSelector(gui.VBox):

    def __init__(self, title: str, handler=None):
        super().__init__(width=300)
        self.set_style("align-items: left")
        self.handler = handler
        self.title = title
        self.label = gui.Label(title)
        self.file_selector = gui.FileUploader("tmp/")
        self.file_selector.ondata.do(self.handle_data)
        self.change_file_button = gui.Button("Change", width=80)
        self.change_file_button.set_style("display: none")
        self.change_file_button.onclick.do(self.change_file)
        self.append(self.label)
        self.append(self.file_selector)
        self.append(self.change_file_button)

    def handle_data(self, file_uploader, file_data, file_name):
        self.label.set_text(self.title + " " + file_name)
        self.change_file_button.set_style("display: block")
        self.file_selector.set_style("display: none")

        if self.handler is not None:
            self.handler(file_uploader, file_data, file_name)

    def change_file(self, widget):
        self.label.set_text(self.title)
        self.change_file_button.set_style("display: none")
        self.file_selector.set_style("display: block")

        if self.handler is not None:
            self.handler(self.file_selector, None, None)


# starts the web server
start(MyApp)
