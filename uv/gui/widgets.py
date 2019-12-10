from datetime import date, timedelta
from enum import Enum
from os import path
from threading import Lock
from typing import Any, Callable, List, Dict

import remi.gui as gui

from uv.logic.result import Result
from .utils import show, hide
from ..brewer_infos import brewer_infos
from ..const import TMP_FILE_DIR, OUTPUT_DIR, DEFAULT_BETA_VALUE, DEFAULT_ALPHA_VALUE, DEFAULT_ALBEDO_VALUE, DEFAULT_OZONE_VALUE
from ..logic.calculation_input import CalculationInput, Angstrom, InputParameters
from ..logic.calculation_utils import CalculationUtils


class Button(gui.Button):
    """
    A button with corrected padding
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_style("padding-left: 18px; padding-right: 18px")


class VBox(gui.VBox):
    """
    A Vertical Box with left alignment
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_style("align-items: flex-start")


class Level(Enum):
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4


class Title(gui.Label):
    """
    A title with a `Level`
    """

    def __init__(self, level: Level, text, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.set_style("font-weight: normal")
        if level == Level.H1:
            self.set_style("font-size: 20pt; margin-top: 10px; margin-bottom: 30px")
        elif level == Level.H2:
            self.set_style("font-size: 18pt; margin-top: 10px; margin-bottom: 30px")
        elif level == Level.H3:
            self.set_style(
                "font-size: 15pt; margin-top: 10px; margin-bottom: 20px")
        else:
            self.set_style("font-size: 10pt; margin-top: 5px; margin-bottom: 10px")


class FileSelector(VBox):
    """
    A file selector.

    When a file is selected, a `Change` button will be shown and it will allow to clear the selector and choose a new file.
    """

    def __init__(self, title: str, handler=None):
        super().__init__(width=300)
        self.handler = handler
        self.title = title
        self.label = gui.Label(title)
        self.file_selector = gui.FileUploader("tmp/")
        self.file_selector.ondata.do(self._on_file_changed)
        self.change_file_button = Button("Change")
        hide(self.change_file_button)
        self.change_file_button.onclick.do(self._on_change_file_button_click)
        self.append(self.label)
        self.append(self.file_selector)
        self.append(self.change_file_button)

    def _on_file_changed(self, file_uploader, file_data, file_name):
        self.label.set_text(self.title + " " + file_name)
        show(self.change_file_button)
        hide(self.file_selector)

        if self.handler is not None:
            self.handler(file_uploader, file_data, file_name)

    def _on_change_file_button_click(self, widget: gui.Widget):
        del widget  # remove unused parameter
        self.label.set_text(self.title)
        hide(self.change_file_button)
        show(self.file_selector)

        if self.handler is not None:
            self.handler(self.file_selector, None, None)


class ResultInfo(gui.HBox):
    """
    An result info with a label and a value
    """

    def __init__(self, label: str, value: Any):
        super().__init__()
        info_label = gui.Label(label + ":\t")
        info_label.set_style("font-weight: bold; width: 110px")
        info_value = gui.Label(str(value))
        self.append(info_label)
        self.append(info_value)


class Loader(VBox):
    """
    A loading bar with text
    """

    def __init__(self):
        super().__init__()
        hide(self)
        self._label = gui.Label("Calculating...")
        self._bar = gui.Progress(0, 100, width=400)
        self.append(self._label)
        self.append(self._bar)
        self._current_value = 0

    def reset(self):
        self._current_value = 0
        self._bar.set_value(0)

    def init(self, total: int):
        self._bar.set_max(total)

    def progress(self, value: float):
        self._current_value = self._current_value + value
        self._bar.set_value(self._current_value)


class MainForm(VBox):
    parameters: InputParameters

    def __init__(self, calculate: Callable[[Callable[[CalculationUtils], List[Result]]], None]):
        """
        Initialize a main form.

        The given callable will be called when the `Calculate` button is clicked with a CalculationInput created from
        the values of this form's fields
        :param calculate: the function to call on `Calculate` click
        """

        super().__init__()
        self.parameters = InputParameters(
            DEFAULT_ALBEDO_VALUE,
            Angstrom(DEFAULT_ALPHA_VALUE, DEFAULT_BETA_VALUE),
            DEFAULT_OZONE_VALUE
        )

        self.set_style("align-items: flex-end")

        self._init_elements()

        self._calculate_button = Button("Calculate")
        self._calculate_button.set_enabled(False)
        self._calculate_button.set_style("margin-bottom: 20px")

        self._calculate_button.onclick.do(
            lambda w: calculate(self.start_calculation))

        self.append(self._calculate_button)

    def start_calculation(self, calculation_utils: CalculationUtils) -> List[Result]:
        pass

    def extra_param_change_callback(self, parameters: InputParameters) -> None:
        """
        Update the inner representation of the extra params.

        This is supposed to be called from outside when the extra params are changed.
        :param parameters: the new parameter values
        """

        self.parameters = parameters
        self.check_fields()

    def _init_elements(self) -> None:
        """
        Initialize the widgets and add them `self`
        """
        pass

    def check_fields(self) -> None:
        """
        Check the fields' values and enable or disable the `Calculate` button accordingly
        """
        pass


class PathMainForm(MainForm):
    _calculation_input: CalculationInput or None = None
    _uv_file: str = None
    _calibration_file: str = None
    _b_file: str = None
    _arf_file: str = None

    def _init_elements(self):

        file_form = gui.HBox()
        file_form.set_style("margin-bottom: 20px")
        self._uv_file_selector = FileSelector("UV File:", handler=self._on_uv_file_change)
        self._calibration_file_selector = FileSelector("Calibration File:", handler=self._on_calibration_file_change)
        self._b_file_selector = FileSelector("B File:", handler=self._on_b_file_change)
        self._arf_file_selector = FileSelector("ARF File:", handler=self._on_arf_file_change)

        file_form.append(self._uv_file_selector)
        file_form.append(self._calibration_file_selector)
        file_form.append(self._b_file_selector)
        file_form.append(self._arf_file_selector)

        self.append(file_form)

    def _on_uv_file_change(self, file_uploader: gui.Widget, file_data: bytes, file_name):
        """
        UV file upload handler
        """
        del file_uploader, file_data  # remove unused parameters
        self._uv_file = TMP_FILE_DIR + file_name
        self.check_fields()

    def _on_calibration_file_change(self, file_uploader: gui.Widget, file_data: bytes, file_name):
        """
        Calibration (UVR) file upload handler
        """
        del file_uploader, file_data  # remove unused parameters
        self._calibration_file = TMP_FILE_DIR + file_name
        self.check_fields()

    def _on_b_file_change(self, file_uploader: gui.Widget, file_data: bytes, file_name):
        """
        B file upload handler
        """
        del file_uploader, file_data  # remove unused parameters
        self._b_file = TMP_FILE_DIR + file_name
        self.check_fields()

    def _on_arf_file_change(self, file_uploader: gui.Widget, file_data: bytes, file_name):
        """
        ARF file upload handler
        """
        del file_uploader, file_data  # remove unused parameters
        self._arf_file = TMP_FILE_DIR + file_name
        self.check_fields()

    def check_fields(self):
        if (self._uv_file is not None and
                self._calibration_file is not None and
                self._arf_file is not None):

            # If all fields are valid, we initialize a CalculationInput and enable the button
            self._calculation_input = CalculationInput(
                self.parameters,
                self._uv_file,
                self._b_file,
                self._calibration_file,
                self._arf_file
            )
            self._calculate_button.set_enabled(True)
        else:
            self._calculate_button.set_enabled(False)
            self._calculation_input = None

    def start_calculation(self, calculation_utils: CalculationUtils) -> List[Result]:
        return calculation_utils.calculate_and_output(self._calculation_input)


class SimpleMainForm(MainForm):
    _brewer_id: str = None
    _date_start: date or None = None
    _date_end: date or None = None

    def __init__(self, calculate: Callable[[Callable[[CalculationUtils], List[Result]]], None]):
        super().__init__(calculate)
        self.check_fields()

    def _init_elements(self):
        self._brewer_id = list(brewer_infos.keys())[0]
        self._date_start = date(2019, 6, 24)
        self._date_end = date(2019, 6, 27)

        file_form = gui.HBox()
        file_form.set_style("margin-bottom: 20px")

        brewer_dd = gui.DropDown()
        for bid in brewer_infos.keys():
            item = gui.DropDownItem(bid)
            brewer_dd.append(item)
        brewer_dd.onchange.do(self._on_bid_change)
        self._brewer_input = Input("Brewer id", brewer_dd)

        date_start_selector = gui.Date(default_value="2019-06-24")
        date_start_selector.onchange.do(self._on_date_start_change)
        self._date_start_input = Input("Start date", date_start_selector)

        date_end_selector = gui.Date(default_value="2019-06-27")
        date_end_selector.onchange.do(self._on_date_end_change)
        self._date_end_input = Input("End date", date_end_selector)

        file_form.append(self._brewer_input)
        file_form.append(self._date_start_input)
        file_form.append(self._date_end_input)

        self.append(file_form)

    @property
    def brewer_id(self):
        return self._brewer_id

    @property
    def date_start(self):
        return self._date_start

    @property
    def date_end(self):
        return self._date_end

    def _on_bid_change(self, widget: gui.Widget, value: str):
        del widget  # remove unused parameter
        self._brewer_id = value
        self.check_fields()

    def _on_date_start_change(self, widget: gui.Widget, value: str):
        del widget  # remove unused parameter
        if value is not '' and value is not None:
            self._date_start = date.fromisoformat(value)
        else:
            self._date_start = None
        self.check_fields()

    def _on_date_end_change(self, widget: gui.Widget, value: str):
        del widget  # remove unused parameter
        if value is not '' and value is not None:
            self._date_end = date.fromisoformat(value)
        else:
            self._date_end = None
        self.check_fields()

    def check_fields(self):
        if self._brewer_id is not None and self._date_start is not None and self._date_end is not None:

            # If all fields are valid, we enable the button
            self._calculate_button.set_enabled(True)
        else:
            self._calculate_button.set_enabled(False)

    def start_calculation(self, calculation_utils: CalculationUtils) -> List[Result]:
        return calculation_utils.calculate_for_all_between(self._date_start, self._date_end, self._brewer_id, self.parameters)


class Input(VBox):
    """
    An input with a label above an input widget
    """

    def __init__(self, label: str, input_widget: gui.Widget):
        super().__init__()
        self.set_style("width: 280px; padding-left: 10px; padding-right: 10px")
        lw = gui.Label(label + ":")
        self.append(lw)
        self.append(input_widget)
        input_widget.set_style("height: 25px")


class ResultWidget(VBox):
    """
    A result widget containing a title, a list of generated files and other infos
    """

    def __init__(self):
        super().__init__()
        self.set_style("margin-bottom: 20px; width: 100%")
        hide(self)
        self.result_title = Title(Level.H2, "Results")
        self._results = None
        self._progress_callback = None
        self._current_progress = 0
        self._current_progress_lock = Lock()

    def display(self, results: List[Result], duration: float) -> None:
        """
        Replace the widgets content with new content created from the given results
        :param results: the results to display in this widget
        :param duration: the duration taken for the calculation
        """
        self._results = results

        self.empty()
        self.append(self.result_title)

        files: Dict[str, List[Result]] = {}
        for result in results:
            if result.calculation_input.uv_file_name not in files:
                files[result.calculation_input.uv_file_name] = []

            files[result.calculation_input.uv_file_name].append(result)

        self.append(self._create_result_overview(files, duration))

        for file in files:
            file_gui = self._create_result_gui(file, files[file])
            self.append(file_gui)

    @staticmethod
    def _create_result_overview(files: Dict[str, List[Result]], duration: float) -> VBox:
        vbox = VBox()
        vbox.set_style("margin-bottom: 20px")

        # Convert the duration into something human readable
        duration = timedelta(seconds=duration)
        hours, rem = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        hours_str = ""
        if hours > 0:
            hours_str = f"{hours}h "

        min_str = ""
        if minutes > 0:
            min_str = f"{minutes}m "

        sec_str = f"{seconds}s"

        info = ResultInfo("Duration", f"{hours_str}{min_str}{sec_str}")
        vbox.append(info)

        info = ResultInfo("Total files", len(files))
        vbox.append(info)

        info = ResultInfo("Total sections", sum([len(r) for r in files.values()]))
        vbox.append(info)

        return vbox

    @staticmethod
    def _create_result_gui(file: str, results: List[Result]) -> VBox:
        """
        Create a section's GUI with a title and a list of files
        :param file: the file for which to create the gui
        :param results: the results for the given file
        :return: the GUI's widget
        """
        vbox = VBox()
        vbox.set_style("margin-bottom: 20px")

        result_title = Title(Level.H3, f"Input file '{path.basename(file)}'")
        vbox.append(result_title)

        info = ResultInfo("Sections", len(results))
        vbox.append(info)

        info_label = gui.Label("Output files:")
        info_label.set_style("font-weight: bold")
        vbox.append(info_label)

        for result in results:
            download_button = gui.FileDownloader(result.get_name(), OUTPUT_DIR + result.get_name(), width=130)
            download_button.set_style("margin-top: 5px; color: rgb(4, 90, 188)")
            vbox.append(download_button)

        return vbox


class ImagePlot(gui.Image):
    """
    An image from the `plots` resource
    """

    def __init__(self, filename: str):
        super().__init__("/plots:" + filename)
        self.set_style("width: 50%")


class ExtraParamForm(gui.HBox):
    """
    The form for the extra parameters albedo and aerosol
    """
    _handler: Callable[[InputParameters], None] = None

    _albedo: float = DEFAULT_ALBEDO_VALUE
    _alpha: float = DEFAULT_ALPHA_VALUE
    _beta: float = DEFAULT_BETA_VALUE
    _default_ozone: float = DEFAULT_OZONE_VALUE
    _no_coscor: bool = False

    def __init__(self):
        super().__init__()
        self.set_style("margin-bottom: 15px")

        # Albedo field
        albedo_spin = gui.SpinBox(DEFAULT_ALBEDO_VALUE, 0, 1, 0.01)
        albedo_spin.onchange.do(self._on_albedo_change)
        albedo_input = Input("Albedo", albedo_spin)
        self.append(albedo_input)

        # Aerosol dual field
        aerosol = gui.HBox()
        aerosol.set_style("justify-content: stretch; width: 100%")
        alpha_spin = gui.SpinBox(DEFAULT_ALPHA_VALUE, 0, 2, 0.01)
        alpha_spin.set_style("width: 120px; height: 25px")
        alpha_spin.onchange.do(self._on_alpha_change)
        beta_spin = gui.SpinBox(DEFAULT_BETA_VALUE, 0, 1.5, 0.01)
        beta_spin.set_style("width: 120px; height: 25px")
        beta_spin.onchange.do(self._on_beta_change)
        alpha_label = gui.Label("α:")
        alpha_label.set_style("flex-grow: 1")
        aerosol.append(alpha_label)
        aerosol.append(alpha_spin)
        beta_label = gui.Label("β:")
        beta_label.set_style("margin-left: 8px; flex-grow: 1")
        aerosol.append(beta_label)
        aerosol.append(beta_spin)
        aerosol_input = Input("Aerosol", aerosol)
        self.append(aerosol_input)

        # Ozone field
        ozone_spin = gui.SpinBox(DEFAULT_OZONE_VALUE, 200, 600, 0.5)
        ozone_spin.onchange.do(self._on_ozone_change)
        ozone_input = Input("Ozone (Used if no value found in B file)", ozone_spin)
        self.append(ozone_input)

        no_coscor_checkbox = gui.CheckBoxLabel("Skip cos correction")
        no_coscor_checkbox.set_style("align-self: flex-end; height: 30px")
        no_coscor_checkbox.onchange.do(self._on_no_coscor_change)
        self.append(no_coscor_checkbox)

    def _on_albedo_change(self, widget: gui.Widget, value: float):
        del widget  # remove unused parameter
        self._albedo = value
        self._on_value_change()

    def _on_alpha_change(self, widget: gui.Widget, value: float):
        del widget  # remove unused parameter
        self._alpha = value
        self._on_value_change()

    def _on_beta_change(self, widget: gui.Widget, value: float):
        del widget  # remove unused parameter
        self._beta = value
        self._on_value_change()

    def _on_ozone_change(self, widget: gui.Widget, value: float):
        del widget  # remove unused parameter
        self._default_ozone = value
        self._on_value_change()

    def _on_no_coscor_change(self, widget: gui.Widget, value: bool):
        del widget  # remove unused parameter
        self._no_coscor = value
        self._on_value_change()

    def _on_value_change(self):
        parameters = InputParameters(
            self._albedo,
            Angstrom(self._alpha, self._beta),
            self._default_ozone,
            self._no_coscor
        )
        self._handler(parameters)

    def register_handler(self, handler: Callable[[InputParameters], None]) -> None:
        """
        Registers a given handler which will be called every time one of the values of the fields is changed
        :param handler: the handler to register
        """
        self._handler = handler

        # Call the handler to update it with the current values
        self._on_value_change()
