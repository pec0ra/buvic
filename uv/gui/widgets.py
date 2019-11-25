from enum import Enum
from typing import Any, Callable

import remi.gui as gui

from .utils import show, hide
from ..const import TMP_FILE_DIR


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
            self.set_style("font-size: 15pt; margin-top: 10px; margin-bottom: 20px")
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
        info_label.set_style("font-weight: bold; width: 90px")
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


class MainForm(VBox):
    def __init__(self, calculate: Callable[[str, str, str, str], None]):
        super().__init__()
        self.uv_file = None
        self.calibration_file = None
        self.b_file = None
        self.arf_file = None

        file_form = gui.HBox()
        file_form.set_style("margin-bottom: 20px")
        self._uv_file_selector = FileSelector("UV File:", handler=self.handle_uv_file)
        self._calibration_file_selector = FileSelector("Calibration File:", handler=self.handle_calibration_file)
        self._b_file_selector = FileSelector("B File:", handler=self.handle_b_file)
        self._arf_file_selector = FileSelector("ARF File:", handler=self.handle_arf_file)

        self._calculate_button = Button("Calculate")
        self._calculate_button.set_enabled(False)
        self._calculate_button.set_style("align-self: end; margin-bottom: 20px")
        self._calculate_button.onclick.do(lambda w: calculate(self.uv_file, self.calibration_file, self.b_file, self.arf_file))

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
            self._calculate_button.set_enabled(True)
        else:
            self._calculate_button.set_enabled(False)

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
