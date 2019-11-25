import os, uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List, Any

import matplotlib.pyplot as plt
import remi.gui as gui
from remi import start, App

from arf_file import ARFFileParsingError
from b_file import BFileParsingError
from calibration_file import CalibrationFileParsingError
from irradiance_evaluation import IrradianceEvaluation, Spectrum
from uv_file import UVFileParsingError

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

        self.loader_container = gui.VBox()
        self.loader_container.set_style("display: none")
        self.loader = gui.Progress(0, 100, width=400)
        self.loader_label = gui.Label("Starting...")
        self.loader_container.append(self.loader_label)
        self.loader_container.append(self.loader)

        self.result_container = gui.VBox()
        self.result_container.set_style("display: none")
        self.result_title = gui.Label("Results")
        self.result_title.set_style("font-size: 18pt; margin-top: 30px")
        self.result_container.append(self.result_title)

        self.main_container.append(self.title)
        self.main_container.append(self.loader_container)
        self.main_container.append(self.main_form)
        self.main_container.append(self.result_container)

        self.error_container = gui.HBox()
        self.error_container.set_style("display: none")
        self.error_label = gui.Label("")
        self.error_label.set_style("color: #E00")
        self.error_container.append(self.error_label)
        self.main_container.append(self.error_container)

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
        self.reset_errors()
        self.loader.set_value(0)
        self.loader_label.set_text("Calculating...")
        self.loader_container.set_style("display: flex")
        self.main_form.set_style("display: none")
        self.result_container.set_style("display: none")

        ie = IrradianceEvaluation(self.uv_file, self.calibration_file, self.b_file, self.arf_file,
                                  progress_handler=self.progress_handler)
        self._executor.submit(self.start_calculation, ie)

    def start_calculation(self, ie: IrradianceEvaluation):
        try:
            result = ie.calculate()
            self.show_result(result)
        except UVFileParsingError as e:
            self.uv_file_selector.set_error(True)
            self.show_error(str(e))
            raise e
        except CalibrationFileParsingError as e:
            self.calibration_file_selector.set_error(True)
            self.show_error(str(e))
            raise e
        except BFileParsingError as e:
            self.b_file_selector.set_error(True)
            self.show_error(str(e))
            raise e
        except ARFFileParsingError as e:
            self.arf_file_selector.set_error(True)
            self.show_error(str(e))
            raise e
        except Exception as e:
            self.show_error(str(e))
            raise e

    def reset_errors(self):
        self.uv_file_selector.set_error(False)
        self.calibration_file_selector.set_error(False)
        self.b_file_selector.set_error(False)
        self.arf_file_selector.set_error(False)
        self.error_container.set_style("display: none")
        self.error_label.set_text("")

    def progress_handler(self, current_progress: int, total_progress: int):
        if total_progress == 0:
            self.loader.set_value(0)
        else:
            value = int(current_progress * 80 / total_progress)
            self.loader.set_value(value)

    def show_result(self, results: List[Spectrum]):
        self.result_container.empty()
        self.result_container.append(self.result_title)
        self.loader_label.set_text("Generating result files...")
        i = 0
        self.loader.set_value(80)
        for result in results:
            self.add_result_to_gui(result, i)
            i += 1
            self.loader.set_value(80 + int(i * 20 / len(results)))
        self.check_files()
        self.loader_container.set_style("display: none")
        self.main_form.set_style("display: flex")
        self.result_container.set_style("display: flex")

    def show_error(self, error: str):
        self.check_files()
        self.result_container.set_style("display: none")
        self.loader_container.set_style("display: none")
        self.main_form.set_style("display: flex")
        self.result_container.set_style("display: none")
        self.error_container.set_style("display: flex")
        print(error)
        if error is not None:
            self.error_label.set_text(error)
        else:
            print("Error is None")

    def add_result_to_gui(self, result: Spectrum, i: int):
        vbox = gui.VBox()

        result_title = gui.Label("Section " + str(i))
        result_title.set_style("font-size: 15pt; margin-bottom: 20px; margin-top: 40px; align-self: start")
        vbox.append(result_title)

        info = ResultInfo("SZA", result.sza)
        vbox.append(info)

        header = result.uv_file_entry.header
        info = ResultInfo("Pressure", header.pressure)
        vbox.append(info)

        info = ResultInfo("Position", str(header.position.latitude) + ", " + str(header.position.longitude))
        vbox.append(info)

        file_name = TMP_FILE_DIR + str(uuid.uuid4()) + ".csv"
        with open(file_name, "w") as csv_file:
            result.to_csv(csv_file)

        download_button = gui.FileDownloader("Download as csv", file_name, width=130)
        download_button.set_style("align-self: start; margin-bottom: 10px; margin-top: 5px")
        #download_button.onclick.do(lambda widget: self.download_as_csv(widget, result))
        vbox.append(download_button)

        hbox = gui.HBox()

        fig, ax = plt.subplots()
        ax.set(xlabel="Wavelength (nm)", ylabel="Irradiance (Wm-2 nm-1)")
        ax.grid()

        ax.semilogy(result.wavelengths, result.original_spectrum, label="Spectrum")

        ax.semilogy(result.wavelengths, result.cos_corrected_spectrum, label="Cos corrected spectrum")

        plt.title("Irradiance for SZA: " + str(result.sza))
        ax.legend()
        fig.savefig(PLOT_DIR + "spectrum_" + str(i) + ".png")
        plt.close()

        pic = gui.Image("/plots:spectrum_" + str(i) + ".png")
        hbox.append(pic)

        fig, ax = plt.subplots()
        ax.set(xlabel="Wavelength (nm)", ylabel="c")
        ax.grid()

        ax.plot(result.wavelengths, result.cos_correction, label="Cglo")

        plt.title("Correction factor for SZA: " + str(result.sza))
        ax.legend()
        fig.savefig(PLOT_DIR + "spectrum_" + str(i) + "_correction.png")
        plt.close()

        pic = gui.Image("/plots:spectrum_" + str(i) + "_correction.png")
        hbox.append(pic)
        vbox.append(hbox)
        self.result_container.append(vbox)


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
        self.set_error(False)
        self.label.set_text(self.title)
        self.change_file_button.set_style("display: none")
        self.file_selector.set_style("display: block")

        if self.handler is not None:
            self.handler(self.file_selector, None, None)

    def set_error(self, value: bool):
        if value:
            self.label.set_style("color: #E00")
        else:
            self.label.set_style("color: #000")


class ResultInfo(gui.HBox):

    def __init__(self, label: str, value: Any):
        super().__init__()
        self.set_style("align-self: start")
        info_label = gui.Label(label + ":\t")
        info_label.set_style("font-weight: bold; width: 90px")
        info_value = gui.Label(str(value))
        self.append(info_label)
        self.append(info_value)


# starts the web server
start(MyApp)
