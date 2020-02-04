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
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import List, Callable, Optional

import remi.gui as gui
from remi import App, Label
from remi.gui import VBox

from buvic.logic.calculation_utils import CalculationUtils
from buvic.logic.file_utils import FileUtils
from buvic.logic.result import Result
from buvic.logic.settings import Settings
from buvic.const import OUTPUT_DIR, DATA_DIR, APP_VERSION, ASSETS_DIR
from buvic.gui.utils import show, hide
from buvic.gui.widgets import Title, Level, Loader, PathMainForm, SimpleMainForm, ResultWidget, Modal, IconButton, SettingsWidget

LOG = getLogger(__name__)


class BUVIC(App):
    _file_utils: FileUtils
    _main_container: VBox
    _forms: VBox
    _setting_widget: SettingsWidget
    _main_form: SimpleMainForm
    _secondary_form: PathMainForm
    _loader: Loader
    _result_container: ResultWidget
    _error_label: Label
    _modal: Optional[Modal] = None

    _executor: ThreadPoolExecutor
    _duration: float

    def __init__(self, *args):
        self._settings = Settings.load()
        super(BUVIC, self).__init__(*args, static_file_path={"plots": OUTPUT_DIR, "res": ASSETS_DIR})

    def main(self):

        self._executor = ThreadPoolExecutor(1)
        self._duration = 0

        head: gui.HEAD = self.page.get_child("head")
        head.add_child("google_icons", '<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">')
        self._file_utils = FileUtils(DATA_DIR)

        self._main_container = gui.VBox()

        logo_container = gui.HBox()
        logo_container.set_style("width: 100%; justify-content: space-between; margin-bottom: 20px")
        logo = gui.Image("/res:logo_buvic.png", width=300, style="align-self: flex-start")
        header_picture = gui.Image("/res:pmodwrc_logo.png", width=200, style="align-self: flex-start")
        logo_container.append(logo)
        logo_container.append(header_picture)
        self._main_container.append(logo_container)

        title = Title(Level.H1, "Brewer UV Irradiance Calculator")

        self._forms = VBox()

        settings_button = IconButton("Settings", "settings", style="align-self: flex-start; margin-bottom: 10px")
        settings_button.onclick.do(self._open_settings)
        self._forms.append(settings_button)

        self._main_form = SimpleMainForm(self._calculate, self._file_utils, self._settings, self._handle_error)
        self._secondary_form = PathMainForm(self._calculate, self._settings)
        hide(self._secondary_form)
        self._forms.append(self._main_form)
        self._forms.append(self._secondary_form)

        self._loader = Loader()

        self._result_container = ResultWidget()

        self._main_container.append(title)
        self._main_container.append(self._loader)
        self._main_container.append(self._forms)

        self._error_label = gui.Label("", style="color: #E00; font-size: 12pt; font-weight: bold")
        hide(self._error_label)
        self._main_container.append(self._error_label)

        self._main_container.append(self._result_container)

        version = gui.Link(
            "https://github.com/pec0ra/buvic", f"BUVIC {APP_VERSION}", style="color: #999; align-self: flex-end; margin-top: 30px"
        )
        self._main_container.append(version)

        self._on_settings_changed()

        self._main_form.refresh()

        # returning the root widget
        return self._main_container

    def _calculate(self, calculation: Callable[[CalculationUtils], List[Result]]) -> None:
        """
        Start the calculation in a background thread for a given input
        :param calculation: the calculation to execute
        """

        self._reset_errors()
        self._loader.reset()
        self._loader.set_label("Loading")
        self._loader.reset()
        show(self._loader)
        hide(self._forms)
        hide(self._result_container)
        self.do_gui_update()

        self._executor.submit(self._start_calculation, calculation)

    def _start_calculation(self, calculation: Callable[[CalculationUtils], List[Result]]):
        """
        The calculation task to execute on the background thread.

        This creates a `CalculationUtils` and execute the given calculation on it
        :param calculation: the calculation to execute
        """
        try:
            job_utils = CalculationUtils(DATA_DIR, OUTPUT_DIR, progress_handler=self._loader,)
            results = calculation(job_utils)
            self._show_result(results)
        except Exception as e:
            self._handle_error(e)

    def _reset_errors(self):
        hide(self._error_label)
        self._error_label.set_text("")

    def _show_result(self, results: List[Result]):
        self._result_container.display(results, self._duration)

        if len(results) == 0:
            self._show_error("No result produced for the given parameters")

        self._main_form.check_fields()
        self._secondary_form.check_fields()
        hide(self._loader)
        show(self._forms)
        show(self._result_container)
        self.do_gui_update()

    def _handle_error(self, e: Exception):
        LOG.error("An error occurred during calculation: ", exc_info=True)
        self._show_error(str(e))

    def _show_error(self, error: str):
        self._main_form.check_fields()
        self._secondary_form.check_fields()
        hide(self._result_container)
        hide(self._loader)
        show(self._forms)
        show(self._error_label)
        if error is not None:
            self._error_label.set_text(error)
        else:
            LOG.warning("Trying to show an error with no message")

    def _on_settings_changed(self) -> None:
        """Called when the settings have been changed"""
        self._main_form.update_settings(self._settings)
        self._secondary_form.update_settings(self._settings)
        if self._settings.manual_mode:
            hide(self._main_form)
            show(self._secondary_form)
        else:
            show(self._main_form)
            hide(self._secondary_form)

    def _open_settings(self, widget: gui.Widget):
        del widget

        save_button_text = "Save"
        self._setting_widget = SettingsWidget(self._settings)
        if self._modal is not None and not self._modal.is_closed():
            self._modal.close()
        self._modal = Modal("Settings", self._setting_widget, [(save_button_text, self._save_settings)])
        self._main_container.append(self._modal)
        self._setting_widget.set_save_button(self._modal.get_extra_buttons()[save_button_text])

    def _save_settings(self, widget: gui.Widget):
        del widget
        self._settings = self._setting_widget.save()
        self._on_settings_changed()
