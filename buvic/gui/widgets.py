#
# Copyright (c) 2020 Basile Maret.
#
# This file is part of BUVIC - Brewer UV Irradiance Calculator
# (see https://github.com/pec0ra/buvic).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from datetime import date, timedelta
from enum import Enum
from os import path
from threading import Lock
from typing import Any, Callable, List, Dict, Optional, Tuple

import remi.gui as gui

from buvic.logic.brewer_infos import StraylightCorrection, eubrewnet_available_brewer_ids
from buvic.logic.file import File
from buvic.logic.file_utils import FileUtils
from buvic.logic.ozone import BFileOzoneProvider
from buvic.logic.parameter_file import Angstrom
from buvic.logic.result import Result
from buvic.logic.settings import Settings, DataSource
from buvic.logic.utils import name_to_date_and_brewer_id
from buvic.logic.weighted_irradiance import WeightedIrradianceType
from .utils import show, hide
from ..const import TMP_FILE_DIR, OUTPUT_DIR
from ..logic.calculation_input import CalculationInput
from ..logic.calculation_utils import CalculationUtils
from ..logic.utils import date_to_days


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
            self.set_style("font-size: 23pt; margin-top: 10px; margin-bottom: 30px")
        elif level == Level.H2:
            self.set_style("font-size: 19pt; margin-top: 10px; margin-bottom: 30px")
        elif level == Level.H3:
            self.set_style("font-size: 16pt; margin-top: 10px; margin-bottom: 20px")
        else:
            self.set_style("font-size: 12pt; margin-top: 5px; margin-bottom: 8px; font-weight: bold")


class FileSelector(VBox):
    """
    A file selector.

    When a file is selected, a `Change` button will be shown and it will allow to clear the selector and choose a new file.
    """

    def __init__(self, title: str, handler=None):
        super().__init__(width=280)
        self.handler = handler
        self.title = title
        self.label = gui.Label(title)
        self.file_selector = gui.FileUploader("tmp/", width=280)
        self.file_selector.ondata.do(self._on_file_changed)
        self.change_file_button = gui.Button("Change")
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
        info_label = gui.Label(label + ":\t", style="font-weight: bold; width: 110px")
        info_value = gui.Label(str(value))
        self.append(info_label)
        self.append(info_value)


class Loader(VBox):
    """
    A loading bar with text
    """

    def __init__(self):
        super().__init__(style="width: 100%; max-width: 500px")
        hide(self)
        self._label = gui.Label("Calculating...")
        self._bar = gui.Progress(0, 100, style="width:100%")
        self.append(self._label)
        self.append(self._bar)
        self._current_value = 0

    def reset(self):
        self._current_value = 0
        self._bar.set_value(0)

    def set_label(self, label: str):
        self._label.set_text(label)

    def init(self, total: int):
        self._current_value = 0
        self._bar.set_value(0)
        self._bar.set_max(total)

    def progress(self, value: float):
        self._current_value = self._current_value + value
        self._bar.set_value(self._current_value)


class MainForm(VBox):
    settings: Settings

    def __init__(self, calculate: Callable[[Callable[[CalculationUtils], List[Result]]], None], settings: Settings):
        """
        Initialize a main form.

        The given callable will be called when the `Calculate` button is clicked with a CalculationInput created from
        the values of this form's fields
        :param calculate: the function to call on `Calculate` click
        """
        super().__init__()
        self.settings = settings

        self.set_style("align-items: flex-end; flex-wrap: wrap")

        self._warning_box = VBox(style="align-self: flex-start; min-height: 24px")
        self.append(self._warning_box)

        self._init_elements()

        self._calculate_button = gui.Button("Calculate", style="margin-bottom: 20px")
        self._calculate_button.set_enabled(False)

        self._calculate_button.onclick.do(lambda w: calculate(self.start_calculation))

        self.append(self._calculate_button)

    def start_calculation(self, calculation_utils: CalculationUtils) -> List[Result]:
        pass

    def update_settings(self, settings: Settings) -> None:
        """
        Update the inner representation of the settings.

        This is supposed to be called from outside when the settings are changed.
        :param settings: the new settings values
        """

        self.settings = settings
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

    def show_warning(self, text: str):
        warning_label = IconLabel(text, "warning")
        warning_label.attributes["class"] = "warning"
        self._warning_box.append(warning_label)

    def clean_warnings(self):
        self._warning_box.empty()


class PathMainForm(MainForm):
    _calculation_input: Optional[CalculationInput] = None
    _uv_file: Optional[str] = None
    _calibration_file: Optional[str] = None
    _b_file: Optional[str] = None
    _arf_file: Optional[str] = None

    def _init_elements(self):

        file_form = gui.HBox(style="margin-bottom: 20px; flex-wrap: wrap")
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
        if file_name is not None:
            self._uv_file = path.join(TMP_FILE_DIR, file_name)
        else:
            self._uv_file = None
        self.check_fields()

    def _on_calibration_file_change(self, file_uploader: gui.Widget, file_data: bytes, file_name):
        """
        Calibration (UVR) file upload handler
        """
        del file_uploader, file_data  # remove unused parameters
        if file_name is not None:
            self._calibration_file = path.join(TMP_FILE_DIR, file_name)
        else:
            self._calibration_file = None
        self.check_fields()

    def _on_b_file_change(self, file_uploader: gui.Widget, file_data: bytes, file_name):
        """
        B file upload handler
        """
        del file_uploader, file_data  # remove unused parameters
        if file_name is not None:
            self._b_file = path.join(TMP_FILE_DIR, file_name)
        else:
            self._b_file = None
        self.check_fields()

    def _on_arf_file_change(self, file_uploader: gui.Widget, file_data: bytes, file_name):
        """
        ARF file upload handler
        """
        del file_uploader, file_data  # remove unused parameters
        if file_name is not None:
            self._arf_file = path.join(TMP_FILE_DIR, file_name)
        else:
            self._arf_file = None
        self.check_fields()

    def check_fields(self):
        self.clean_warnings()
        if self._uv_file is not None and self._calibration_file is not None:

            d, brewer_id = name_to_date_and_brewer_id(self._uv_file)
            brewer_type = BFileOzoneProvider(File(self._b_file) if self._b_file is not None else None).get_brewer_type()
            if brewer_type is None:
                self.show_warning(
                    f"Straylight correction cannot be determined. Using default:" f"{self.settings.default_straylight_correction.value}"
                )
            # If all fields are valid, we initialize a CalculationInput and enable the button
            self._calculation_input = CalculationInput(
                brewer_id,
                d,
                self.settings,
                File(self._uv_file),
                File(self._b_file) if self._b_file is not None else None,
                File(self._calibration_file),
                File(self._arf_file) if self._arf_file is not None else None,
                brewer_type,
            )
            self._calculate_button.set_enabled(True)
        else:
            self._calculate_button.set_enabled(False)
            self._calculation_input = None

    def start_calculation(self, calculation_utils: CalculationUtils) -> List[Result]:
        if self._calculation_input is None:
            raise Exception("It should not be possible to start calculation with a calculation_input which is None")
        return calculation_utils.calculate_for_input(self._calculation_input)


class SimpleMainForm(MainForm):
    _file_utils: FileUtils
    _brewer_id: Optional[str] = None
    _date_start: Optional[date] = None
    _date_end: Optional[date] = None
    _uvr_file: Optional[str] = None

    def __init__(self, calculate: Callable[[Callable[[CalculationUtils], List[Result]]], None], file_utils: FileUtils, settings: Settings):
        self._file_utils = file_utils
        super().__init__(calculate, settings)
        self.check_fields()

    def _init_elements(self):
        self._date_end = date.today()
        self._date_start = self._date_end - timedelta(days=3)

        file_form = gui.HBox(style="margin-bottom: 20px; flex-wrap: wrap")

        self._brewer_dd = gui.DropDown()
        self._update_brewer_ids()
        self._brewer_dd.onchange.do(self._on_bid_change)
        self._brewer_input = Input("Brewer id", self._brewer_dd, style="margin-right: 20px")

        self._uvr_dd = gui.DropDown()
        self._update_uvr_files()
        self._uvr_dd.onchange.do(self._on_uvr_change)
        self._uvr_input = Input("UVR file", self._uvr_dd, style="margin-right: 20px")

        self._date_start_selector = gui.Date(default_value="2019-06-24")
        self._date_start_selector.onchange.do(self._on_date_start_change)
        self._date_start_input = Input("Start date", self._date_start_selector, style="margin-right: 20px")

        self._date_end_selector = gui.Date(default_value="2019-06-27")
        self._date_end_selector.onchange.do(self._on_date_end_change)
        self._date_end_input = Input("End date", self._date_end_selector, style="margin-right: 20px")

        file_form.append(self._brewer_input)
        file_form.append(self._uvr_input)
        file_form.append(self._date_start_input)
        file_form.append(self._date_end_input)

        self.append(file_form)

        self._refresh_button = gui.Button("Refresh", style="margin-bottom: 10px")
        self._refresh_button.onclick.do(self._refresh)

        self.append(self._refresh_button)

    def _update_brewer_ids(self):
        if self.settings.uv_data_source == DataSource.FILES or self.settings.uvr_data_source == DataSource.FILES:
            brewer_ids = self._file_utils.get_brewer_ids()
        else:
            brewer_ids = eubrewnet_available_brewer_ids
        self._brewer_dd.empty()
        for bid in brewer_ids:
            item = gui.DropDownItem(bid)
            self._brewer_dd.append(item)

        if self._brewer_id not in brewer_ids and len(brewer_ids) > 0:
            self._brewer_id = brewer_ids[0]
        if self._brewer_id not in brewer_ids:
            self._brewer_id = None
        self._brewer_dd.set_value(self._brewer_id)

    def _update_uvr_files(self):
        if self.settings.uvr_data_source == DataSource.EUBREWNET:
            return
        uvr_files = self._file_utils.get_uvr_files(self._brewer_id)

        self._uvr_dd.empty()
        for uvr_file in uvr_files:
            item = gui.DropDownItem(uvr_file.file_name)
            self._uvr_dd.append(item)

        if self._uvr_file not in [u.file_name for u in uvr_files] and len(uvr_files) > 0:
            self._uvr_file = uvr_files[0].file_name
        elif self._uvr_file not in [u.file_name for u in uvr_files]:
            self._uvr_file = None
        self._uvr_dd.set_value(self._uvr_file)

    def _update_date_range(self):
        if self.settings.uv_data_source == DataSource.FILES:
            date_range = self._file_utils.get_date_range(self._brewer_id)
        else:
            date_range = (date(2000, 1, 1), date.today())

        if self._date_start < date_range[0] or self._date_start > date_range[1]:
            self._date_start = date_range[0]
        if self._date_end > date_range[1] or self._date_start < date_range[0]:
            self._date_end = date_range[1]

        self._date_start_selector.set_value(self._date_start)
        self._date_end_selector.set_value(self._date_end)

        self._date_start_selector.attributes["min"] = date_range[0].isoformat()
        self._date_start_selector.attributes["max"] = date_range[1].isoformat()

        self._date_end_selector.attributes["min"] = date_range[0].isoformat()
        self._date_end_selector.attributes["max"] = date_range[1].isoformat()

    def _refresh(self, widget: gui.Widget):
        del widget  # remove unused parameter
        self._file_utils.refresh()
        self.check_fields()

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
        self._update_uvr_files()
        self.check_fields()

    def _on_uvr_change(self, widget: gui.Widget, value: str):
        del widget  # remove unused parameter
        self._uvr_file = value
        self.check_fields()

    def _on_date_start_change(self, widget: gui.Widget, value: str):
        del widget  # remove unused parameter
        if value != "" and value is not None:
            self._date_start = date.fromisoformat(value)
        else:
            self._date_start = None
        self.check_fields()

    def _on_date_end_change(self, widget: gui.Widget, value: str):
        del widget  # remove unused parameter
        if value != "" and value is not None:
            self._date_end = date.fromisoformat(value)
        else:
            self._date_end = None
        self.check_fields()

    def check_fields(self):
        self._update_brewer_ids()
        self._update_uvr_files()
        self._update_date_range()

        self.clean_warnings()
        if self._brewer_id is not None and self._date_start is not None and self._date_end is not None:

            # If all fields are valid, we enable the button
            self._calculate_button.set_enabled(True)
        else:
            self._calculate_button.set_enabled(False)

        if self._brewer_id is not None:
            arf = self._file_utils.get_arf_file(self._brewer_id)
            if arf is None:
                self.show_warning("No arf file exists for this brewer id. Cos correction will not be applied")

        if self._brewer_id is not None:
            brewer_type = self._file_utils.get_brewer_type(self._brewer_id)
            if brewer_type is None:
                straylight_correction = self.settings.default_straylight_correction
                self.show_warning(f"Straylight correction cannot be determined. Using default: {straylight_correction.value}")

        if self.settings.uvr_data_source == DataSource.EUBREWNET:
            hide(self._uvr_input)
        else:
            show(self._uvr_input)

    def start_calculation(self, calculation_utils: CalculationUtils) -> List[Result]:
        if self._brewer_id is None or self._date_start is None or self._date_end is None:
            raise Exception("Calculation should not be available with None values")
        calculation_inputs = self._file_utils.get_calculation_inputs_between(
            self._date_start, self._date_end, self._brewer_id, self.settings, self._uvr_file
        )
        return calculation_utils.calculate_for_inputs(calculation_inputs)


class Input(VBox):
    """
    An input with a label above an input widget
    """

    def __init__(self, label: str, input_widget: gui.Widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lw = gui.Label(label + ":")
        self.append(lw)
        self.append(input_widget)
        input_widget.set_style("width: 260px; height: 25px")


class ResultWidget(VBox):
    """
    A result widget containing a title, a list of generated files and other infos
    """

    def __init__(self):
        super().__init__(style="margin-bottom: 20px; width: 100%")
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
            date_iso = result.calculation_input.date.isoformat()
            if date_iso not in files:
                files[date_iso] = []

            files[date_iso].append(result)

        self.append(self._create_result_overview(files, duration))

        for file in files:
            file_gui = self._create_result_gui(files[file])
            self.append(file_gui)

    @staticmethod
    def _create_result_overview(files: Dict[str, List[Result]], duration: float) -> VBox:
        vbox = VBox(style="margin-bottom: 20px")

        # Convert the duration into something human readable
        td = timedelta(seconds=duration)
        hours, rem = divmod(td.seconds, 3600)
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
    def _create_result_gui(results: List[Result]) -> VBox:
        """
        Create a section's GUI with a title and a list of files
        :param results: the results for the given file
        :return: the GUI's widget
        """
        vbox = VBox(style="margin-bottom: 20px")

        result_title = Title(
            Level.H3, f"{results[0].calculation_input.date.isoformat()} ({date_to_days(results[0].calculation_input.date)})"
        )
        vbox.append(result_title)

        if len(results) > 0 and len(results[0].calculation_input.warnings) > 0:
            warning_box = VBox(style="margin-bottom: 15px")
            for warning in results[0].calculation_input.warnings:
                warning_label = IconLabel(warning, "warning", style="margin-bottom: 5px")
                warning_label.attributes["class"] = "warning"
                warning_box.append(warning_label)

            vbox.append(warning_box)

        info = ResultInfo("Sections", len(results))
        vbox.append(info)

        info_label = gui.Label("Output files:", style="font-weight: bold")
        vbox.append(info_label)

        # TODO: show WOUDC download button
        # download_button = gui.FileDownloader(results[0].get_woudc_name(), path.join(OUTPUT_DIR, results[0].get_woudc_name()), width=330,
        #                                      style="margin-top: 5px; margin-bottom: 5px")
        # vbox.append(download_button)

        # UVER file download button
        download_button = gui.FileDownloader(
            results[0].get_uver_name(),
            path.join(OUTPUT_DIR, results[0].get_uver_name()),
            width=330,
            style="margin-top: 5px; margin-bottom: 5px",
        )
        vbox.append(download_button)

        # qasume files download buttons
        for result in results:
            download_button = gui.FileDownloader(
                result.get_qasume_name(), path.join(OUTPUT_DIR, result.get_qasume_name()), width=330, style="margin-top: 5px"
            )
            vbox.append(download_button)

        return vbox


class Icon(gui.Label):
    def __init__(self, icon_name, *args, **kwargs):
        """
        Args:
            icon_name (str): The string content that have to be displayed in the Label.
            kwargs: See Container.__init__()
        """
        super(Icon, self).__init__(icon_name, *args, **kwargs)
        self.type = "i"
        self.attributes["class"] = "material-icons"
        self.set_text(icon_name)


class IconLabel(gui.Label):
    def __init__(self, text, icon_name, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.set_style("display: flex; align-items: center")
        icon = Icon(icon_name, style="margin-right: 5px; order: -1")
        self.append(icon)


class IconButton(gui.Button):
    def __init__(self, text, icon_name, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.set_style("display: flex; align-items: center")
        icon = Icon(icon_name, style="margin-right: 5px; order: -1")
        self.add_child("icon", icon)


class Backdrop(gui.Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_class("backdrop")


class Modal(Backdrop):
    _extra_buttons: Dict[str, gui.Button]
    _is_closed: bool = False

    def __init__(
        self, title: str, content: gui.Widget, extra_buttons: List[Tuple[str, Callable[[gui.Widget], None]]] = [], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        modal = VBox()
        modal.add_class("modal")
        title = Title(Level.H2, title, style="padding-left: 30px; padding-right: 30px")
        modal.append(title)
        wrapper = VBox(style="")
        wrapper.add_class("modal_content_wrapper")
        wrapper.append(content)
        modal.append(wrapper)

        buttons = gui.HBox()
        buttons.add_class("buttons")

        self._extra_buttons = {}
        for button_text, button_action in extra_buttons:
            b = gui.Button(button_text)
            b.onclick.do(button_action)
            buttons.append(b)
            self._extra_buttons[button_text] = b

        close_button = gui.Button("Close")
        close_button.onclick.do(lambda w: self.close())
        buttons.append(close_button)

        modal.append(buttons)
        self.add_child("modal", modal)
        self.onclick.do(lambda w: self.close())
        
        # Add dummy onclick to stop click event propagation which would close the modal
        modal.onclick.do(lambda w: True)

    def close(self):
        parent: gui.Container = self.get_parent()
        parent.remove_child(self)
        self._is_closed = True

    def get_extra_buttons(self) -> Dict[str, gui.Button]:
        return self._extra_buttons

    def is_closed(self):
        return self._is_closed


class SettingsWidget(VBox):
    _save_button: gui.Button = None

    def __init__(self, settings: Settings):
        super().__init__()

        form_title = Title(Level.H4, "ARF File column")
        self.append(form_title)

        self._arf_selection = gui.DropDown()
        self._arf_selection.append(gui.DropDownItem("1"))
        self._arf_selection.append(gui.DropDownItem("2"))
        self._arf_selection.append(gui.DropDownItem("3"))
        self._arf_selection.append(gui.DropDownItem("4"))
        self._arf_selection.set_value(str(settings.arf_column))
        arf_input = Input(
            "Column of the ARF file to use for the cos correction (column 0 is sza)", self._arf_selection, style="margin-bottom: 10px"
        )
        self.append(arf_input)

        form_title = Title(Level.H4, "Daily file settings")
        self.append(form_title)

        self._weighted_irradiance_type_selection = gui.DropDown()
        for t in WeightedIrradianceType:
            self._weighted_irradiance_type_selection.append(gui.DropDownItem(t))
        self._weighted_irradiance_type_selection.set_value(settings.weighted_irradiance_type)
        weighted_irradiance_type_input = Input(
            "Type of weight function to use for the weighted irradiance",
            self._weighted_irradiance_type_selection,
            style="margin-bottom: 10px",
        )
        self.append(weighted_irradiance_type_input)

        coscor_title = Title(Level.H4, "Cos correction")
        coscor_title.set_style("margin-top: 14px")
        self.append(coscor_title)

        self._no_coscor_checkbox = gui.CheckBoxLabel("Skip cos correction", style="height: 30px; width: 260px; padding-right: 20px")
        self._no_coscor_checkbox.set_value(settings.no_coscor)
        # Click didn't work correctly for checkboxes due to a bug with onclick.
        self._no_coscor_checkbox.onclick.do(lambda w: self._no_coscor_checkbox.set_value(not self._no_coscor_checkbox.get_value()))
        self.append(self._no_coscor_checkbox)

        coscor_title = Title(Level.H4, "Temperature correction")
        coscor_title.set_style("margin-top: 14px")
        self.append(coscor_title)
        temperature_explanation = IconLabel(
            "Each value of the spectrum F for a temperature T (°C) will be corrected with a correction "
            "factor C and a reference temperature Tref (°C) with the formula: F * [1 + C * (T - Tref)]",
            "info_outline",
            style="margin-bottom: 10px",
        )
        self.append(temperature_explanation)

        # Temperature correction dual field
        temp_correction = gui.HBox(style="justify-content: stretch; width: 260px")
        self._temp_factor_spin = gui.SpinBox(settings.temperature_correction_factor, -4, 4, 0.01, style="width: 100px; height: 25px")
        self._temp_ref_spin = gui.SpinBox(settings.temperature_correction_ref, -50, 50, 0.5, style="width: 100px; height: 25px")
        temp_factor_label = gui.Label("C:", style="flex-grow: 1")
        temp_correction.append(temp_factor_label)
        temp_correction.append(self._temp_factor_spin)
        temp_ref_label = gui.Label("Tref:", style="margin-left: 8px; flex-grow: 1")
        temp_correction.append(temp_ref_label)
        temp_correction.append(self._temp_ref_spin)
        self.append(temp_correction)

        default_title = Title(Level.H4, "Default values")
        default_title.set_style("margin-top: 14px")
        self.append(default_title)
        default_explanation = IconLabel(
            "Will be used if no value is found in the files or via api", "info_outline", style="margin-bottom: 10px"
        )
        self.append(default_explanation)

        # Albedo field
        self._albedo_spin = gui.SpinBox(settings.default_albedo, 0, 1, 0.01)
        albedo_input = Input("Albedo", self._albedo_spin, style="margin-bottom: 10px")
        self.append(albedo_input)

        # Aerosol dual field
        aerosol = gui.HBox(style="justify-content: stretch; width: 100%")
        self._alpha_spin = gui.SpinBox(settings.default_aerosol.alpha, 0, 2, 0.01, style="width: 110px; height: 25px")
        self._beta_spin = gui.SpinBox(settings.default_aerosol.beta, 0, 1.5, 0.01, style="width: 110px; height: 25px")
        alpha_label = gui.Label("α:", style="flex-grow: 1")
        aerosol.append(alpha_label)
        aerosol.append(self._alpha_spin)
        beta_label = gui.Label("β:", style="margin-left: 8px; flex-grow: 1")
        aerosol.append(beta_label)
        aerosol.append(self._beta_spin)
        aerosol_input = Input("Aerosol", aerosol, style="margin-bottom: 10px")
        self.append(aerosol_input)

        # Ozone field
        self._ozone_spin = gui.SpinBox(settings.default_ozone, 200, 600, 0.5)
        ozone_input = Input("Ozone", self._ozone_spin, style="margin-bottom: 10px")
        self.append(ozone_input)

        self._straylight_checkbox = gui.CheckBoxLabel(
            "Apply straylight correction", style="height: 30px; width: 260px; padding-right: 20px"
        )
        self._straylight_checkbox.set_value(settings.default_straylight_correction == StraylightCorrection.APPLIED)
        # Click didn't work correctly for checkboxes due to a bug with onclick.
        self._straylight_checkbox.onclick.do(lambda w: self._straylight_checkbox.set_value(not self._straylight_checkbox.get_value()))
        self.append(self._straylight_checkbox)

        source_title = Title(Level.H4, "Data source")
        source_title.set_style("margin-top: 14px")
        self.append(source_title)
        source_explanation = IconLabel(
            "Data can either come from files on disk or from the online database eubrewnet.",
            "info_outline",
            style="margin-bottom: 10px; line-height: 14pt",
        )
        self.append(source_explanation)

        self._form_selection_checkbox = gui.CheckBoxLabel(
            "Specify files manually instead of giving a date and a brewer id", style="min-height: 30px; margin-bottom: 6px"
        )
        self._form_selection_checkbox.set_value(settings.manual_mode)
        # Click didn't work correctly for checkboxes due to a bug with onclick.
        self._form_selection_checkbox.onclick.do(lambda w: self._form_selection_checkbox_change())
        self.append(self._form_selection_checkbox)

        self._source_container = VBox()

        self._uv_source_selection = gui.DropDown()
        for source in DataSource:
            self._uv_source_selection.append(gui.DropDownItem(source))
        self._uv_source_selection.set_value(settings.uv_data_source)
        uv_source_input = Input("UV data source", self._uv_source_selection, style="margin-bottom: 10px")
        self._source_container.append(uv_source_input)

        self._ozone_source_selection = gui.DropDown()
        for source in DataSource:
            self._ozone_source_selection.append(gui.DropDownItem(source))
        self._ozone_source_selection.set_value(settings.ozone_data_source)
        ozone_source_input = Input("Ozone data source", self._ozone_source_selection, style="margin-bottom: 10px")
        self._source_container.append(ozone_source_input)

        self._uvr_source_selection = gui.DropDown()
        for source in DataSource:
            self._uvr_source_selection.append(gui.DropDownItem(source))
        self._uvr_source_selection.set_value(settings.uvr_data_source)
        uvr_source_input = Input("UVR data source", self._uvr_source_selection, style="margin-bottom: 10px")
        self._source_container.append(uvr_source_input)

        self.append(self._source_container)
        self._update_manual_mode()

    def save(self) -> Settings:
        manual_mode = self._form_selection_checkbox.get_value()

        arf_column = int(self._arf_selection.get_value())

        weighted_irradiance_type = self._weighted_irradiance_type_selection.get_value()

        no_coscor = self._no_coscor_checkbox.get_value()

        temperature_correction_factor = float(self._temp_factor_spin.get_value())
        temperature_correction_ref = float(self._temp_ref_spin.get_value())

        albedo = float(self._albedo_spin.get_value())

        alpha = float(self._alpha_spin.get_value())
        beta = float(self._beta_spin.get_value())

        ozone = float(self._ozone_spin.get_value())

        if self._straylight_checkbox.get_value():
            straylight_correction = StraylightCorrection.APPLIED
        else:
            straylight_correction = StraylightCorrection.NOT_APPLIED

        uv_data_source = self._uv_source_selection.get_value()
        ozone_data_source = self._ozone_source_selection.get_value()
        uvr_data_source = self._uvr_source_selection.get_value()

        settings = Settings(
            manual_mode,
            arf_column,
            WeightedIrradianceType(weighted_irradiance_type),
            no_coscor,
            temperature_correction_factor,
            temperature_correction_ref,
            albedo,
            Angstrom(alpha, beta),
            ozone,
            straylight_correction,
            DataSource(uv_data_source),
            DataSource(ozone_data_source),
            DataSource(uvr_data_source),
        )
        settings.write()
        self._show_success()
        return settings

    def set_save_button(self, button: gui.Button) -> None:
        self._save_button = button

    def _show_success(self):
        self.empty()
        success_label = IconLabel("Saved successfully!", "done")
        success_label.add_class("success")
        self.append(success_label)

        if self._save_button is not None:
            self._save_button.set_enabled(False)

    def _form_selection_checkbox_change(self):
        self._form_selection_checkbox.set_value(not self._form_selection_checkbox.get_value())
        self._update_manual_mode()

    def _update_manual_mode(self):
        if self._form_selection_checkbox.get_value():
            hide(self._source_container)
        else:
            show(self._source_container)
