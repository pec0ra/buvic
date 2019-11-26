from concurrent.futures import ThreadPoolExecutor
from datetime import date
from enum import Enum
from threading import Lock
from typing import Any, Callable, List, Tuple

import remi.gui as gui

from .utils import show, hide
from ..brewer_infos import brewer_infos
from ..const import TMP_FILE_DIR, DATA_DIR, PLOT_DIR
from ..logic.calculation_input import CalculationInput
from ..logic.irradiance_evaluation import Result
from ..logic.utils import create_spectrum_plots, create_sza_plot


class Button(gui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_style("padding-left: 18px; padding-right: 18px")


class VBox(gui.VBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_style("align-items: flex-start")


class Level(Enum):
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4


class Title(gui.Label):
    def __init__(self, level: Level, text, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.set_style("font-weight: normal")
        if level == Level.H1:
            self.set_style("font-size: 20pt; margin-top: 10px; margin-bottom: 30px")
        elif level == Level.H2:
            self.set_style("font-size: 18pt; margin-top: 10px; margin-bottom: 30px")
        elif level == Level.H3:
            self.set_style(
                "font-size: 15pt; margin-top: 10px; margin-bottom: 20px; color: rgb(4, 90, 188); font-weight: bold")
        else:
            self.set_style("font-size: 10pt; margin-top: 5px; margin-bottom: 10px")


class FileSelector(VBox):

    def __init__(self, title: str, handler=None):
        super().__init__(width=300)
        self.handler = handler
        self.title = title
        self.label = gui.Label(title)
        self.file_selector = gui.FileUploader("tmp/")
        self.file_selector.ondata.do(self.handle_data)
        self.change_file_button = Button("Change")
        hide(self.change_file_button)
        self.change_file_button.onclick.do(self.change_file)
        self.append(self.label)
        self.append(self.file_selector)
        self.append(self.change_file_button)

    def handle_data(self, file_uploader, file_data, file_name):
        self.label.set_text(self.title + " " + file_name)
        show(self.change_file_button)
        hide(self.file_selector)

        if self.handler is not None:
            self.handler(file_uploader, file_data, file_name)

    def change_file(self, widget):
        self.set_error(False)
        self.label.set_text(self.title)
        hide(self.change_file_button)
        show(self.file_selector)

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
        info_label = gui.Label(label + ":\t")
        info_label.set_style("font-weight: bold; width: 110px")
        info_value = gui.Label(str(value))
        self.append(info_label)
        self.append(info_value)


class Loader(VBox):
    def __init__(self):
        super().__init__()
        hide(self)
        self._label = gui.Label("Starting...")
        self._bar = gui.Progress(0, 100, width=400)
        self.append(self._label)
        self.append(self._bar)

    def set_progress(self, value: int):
        self._bar.set_value(value)

    def set_label(self, label: str):
        self._label.set_text(label)


class ExpertMainForm(VBox):

    def __init__(self, calculate: Callable[[CalculationInput], None]):
        super().__init__()
        self.uv_file = None
        self.calibration_file = None
        self.b_file = None
        self.arf_file = None
        self.calculation_input = None

        self.set_style("align-items: flex-end")

        file_form = gui.HBox()
        file_form.set_style("margin-bottom: 20px")
        self._uv_file_selector = FileSelector("UV File:", handler=self.handle_uv_file)
        self._calibration_file_selector = FileSelector("Calibration File:", handler=self.handle_calibration_file)
        self._b_file_selector = FileSelector("B File:", handler=self.handle_b_file)
        self._arf_file_selector = FileSelector("ARF File:", handler=self.handle_arf_file)

        self._calculate_button = Button("Calculate")
        self._calculate_button.set_enabled(False)
        self._calculate_button.set_style("margin-bottom: 20px")

        self._calculate_button.onclick.do(
            lambda w: calculate(self.calculation_input))

        file_form.append(self._uv_file_selector)
        file_form.append(self._calibration_file_selector)
        file_form.append(self._b_file_selector)
        file_form.append(self._arf_file_selector)

        self.append(file_form)
        self.append(self._calculate_button)

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
            self.calculation_input = CalculationInput(
                date.today(),
                self.uv_file,
                self.b_file,
                self.calibration_file,
                self.arf_file
            )
            self._calculate_button.set_enabled(True)
        else:
            self._calculate_button.set_enabled(False)
            self.calculation_input = None

    def set_uv_file_error(self):
        self._uv_file_selector.set_error(True)

    def set_calibration_file_error(self):
        self._calibration_file_selector.set_error(True)

    def set_b_file_error(self):
        self._b_file_selector.set_error(True)

    def set_arf_file_error(self):
        self._arf_file_selector.set_error(True)

    def reset_errors(self):
        self._uv_file_selector.set_error(False)
        self._calibration_file_selector.set_error(False)
        self._b_file_selector.set_error(False)
        self._arf_file_selector.set_error(False)


class SimpleMainForm(VBox):

    def __init__(self, calculate: Callable[[CalculationInput], None]):
        super().__init__()
        self.set_style("align-items: flex-end")
        self._brewer_id = list(brewer_infos.keys())[0]
        self._date = date(2019, 6, 24)

        self._calculation_input = None

        file_form = gui.HBox()
        file_form.set_style("margin-bottom: 20px")

        brewer_dd = gui.DropDown()
        for bid in brewer_infos.keys():
            item = gui.DropDownItem(bid)
            brewer_dd.append(item)
        brewer_dd.onchange.do(self._on_bid_change)
        self._brewer_input = Input("Brewer id", brewer_dd)

        date_selector = gui.Date(default_value="2019-06-24")
        date_selector.onchange.do(self._on_date_change)
        self._date_input = Input("Date", date_selector)

        self._calculate_button = Button("Calculate")
        self._calculate_button.set_enabled(False)
        self._calculate_button.set_style("margin-bottom: 20px")
        self._calculate_button.onclick.do(
            lambda w: calculate(self._calculation_input))

        file_form.append(self._brewer_input)
        file_form.append(self._date_input)

        self.append(file_form)
        self.append(self._calculate_button)
        self.check_files()

    @property
    def brewer_id(self):
        return self._brewer_id

    @property
    def date(self):
        return self._date

    def _on_bid_change(self, widget, value: str):
        self._brewer_id = value
        self.check_files()

    def _on_date_change(self, widget, value: str):
        if value is not '' and value is not None:
            self._date = date.fromisoformat(value)
        else:
            self._date = None
        self.check_files()

    def check_files(self):
        if self._brewer_id is not None and self._date is not None:
            self._calculation_input = CalculationInput.from_date_and_bid(DATA_DIR, self._brewer_id, self._date)
            self._calculate_button.set_enabled(True)
        else:
            self._calculation_input = None
            self._calculate_button.set_enabled(False)


class Input(VBox):
    def __init__(self, label: str, input_widget: gui.Widget):
        super().__init__()
        self.set_style("width: 280px; padding-left: 10px; padding-right: 10px")
        l = gui.Label(label + ":")
        self.append(l)
        self.append(input_widget)


class ResultWidget(VBox):

    def __init__(self):
        super().__init__()
        self.set_style("margin-bottom: 20px")
        hide(self)
        self.result_title = Title(Level.H2, "Results")
        self._results = None
        self._progress_callback = None
        self._current_progress = 0
        self._current_progress_lock = Lock()

    def display(self, results: List[Result], progress: Callable[[int, int], None] = None):
        self._results = results
        self._progress_callback = progress
        self._current_progress = 0

        with ThreadPoolExecutor() as pool:
            result_guis = pool.map(self._create_result_gui, enumerate(results))

        self.empty()
        self.append(self.result_title)

        sza_correction_plot = create_sza_plot(PLOT_DIR, results)
        pic = ImagePlot(sza_correction_plot)
        self.append(pic)

        for result_gui in result_guis:
            self.append(result_gui)

    def _create_result_gui(self, entry: Tuple[int, Result]) -> VBox:
        index, result = entry
        vbox = VBox()
        vbox.set_style("margin-bottom: 20px")

        result_title = Title(Level.H3, "Section " + str(index))
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

        time = result.spectrum.measurement_times[0]
        info = ResultInfo("Ozone", result.ozone.interpolated_value(time))
        vbox.append(info)

        file_name = TMP_FILE_DIR + result.get_name("spectrum_", ".csv")
        with open(file_name, "w") as csv_file:
            result.to_csv(csv_file)

        download_button = gui.FileDownloader("Download as csv", file_name, width=130)
        download_button.set_style("margin-bottom: 10px; margin-top: 5px; color: rgb(4, 90, 188)")
        vbox.append(download_button)

        hbox = gui.HBox()

        spectrum_plot, spectrum_correction_plot = create_spectrum_plots(PLOT_DIR, result)
        pic = ImagePlot(spectrum_plot)
        hbox.append(pic)

        pic = ImagePlot(spectrum_correction_plot)
        hbox.append(pic)
        vbox.append(hbox)

        self._progress_callback(len(self._results) + self._get_next_progress(), len(self._results))
        return vbox

    def _get_next_progress(self) -> int:
        with self._current_progress_lock:
            self._current_progress += 1
            return self._current_progress


class ImagePlot(gui.Image):
    def __init__(self, filename: str):
        super().__init__("/plots:" + filename)
        self.set_style("width: 50%")
