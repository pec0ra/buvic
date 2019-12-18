import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import List, Callable

import remi.gui as gui
from remi import App, Label
from remi.gui import VBox

from buvic.logic.calculation_utils import CalculationUtils
from buvic.logic.file_utils import FileUtils
from buvic.logic.result import Result
from .const import OUTPUT_DIR, DATA_DIR, APP_VERSION, ASSETS_DIR
from .gui.utils import show, hide
from .gui.widgets import Title, Level, Loader, PathMainForm, SimpleMainForm, ResultWidget, ExtraParamForm

LOG = getLogger(__name__)


class UVApp(App):
    _file_utils: FileUtils
    _main_container: VBox
    _forms: VBox
    _extra_param_form: ExtraParamForm
    _main_form: SimpleMainForm
    _secondary_form: PathMainForm
    _loader: Loader
    _result_container: ResultWidget
    _error_label: Label
    _lock = multiprocessing.Manager().Lock()

    def __init__(self, *args):
        super(UVApp, self).__init__(*args, static_file_path={'plots': OUTPUT_DIR, 'res': ASSETS_DIR})

        self._executor = ThreadPoolExecutor(1)
        self._duration = 0

    def main(self):
        self._file_utils = FileUtils(DATA_DIR)

        self._main_container = gui.VBox(width="80%", style="margin: 30px auto; padding: 20px 40px 10px 40px")

        header_picture = gui.Image("/res:pmodwrc_logo.png", width=200, style="align-self: flex-start")
        title = Title(Level.H1, "Brewer UV Irradiance Calculator")

        self._forms = VBox()

        form_selection_checkbox = gui.CheckBoxLabel("Manual mode", style="align-self: flex-start; margin-bottom: 20px;"
                                                                         "height: 30px")
        form_selection_checkbox.onchange.do(self._on_form_selection_change)
        self._forms.append(form_selection_checkbox)

        self._extra_param_form = ExtraParamForm()
        self._forms.append(self._extra_param_form)

        self._main_form = SimpleMainForm(self._calculate, self._file_utils)
        self._secondary_form = PathMainForm(self._calculate)
        hide(self._secondary_form)
        self._forms.append(self._main_form)
        self._forms.append(self._secondary_form)

        self._extra_param_form.register_handler(self._main_form.extra_param_change_callback)

        self._loader = Loader()

        self._result_container = ResultWidget()

        self._main_container.append(header_picture)
        self._main_container.append(title)
        self._main_container.append(self._loader)
        self._main_container.append(self._forms)

        self._error_label = gui.Label("", style="color: #E00; font-size: 12pt; font-weight: bold")
        hide(self._error_label)
        self._main_container.append(self._error_label)

        self._main_container.append(self._result_container)

        version = gui.Link("https://hub.docker.com/r/pmodwrc/buvic", f"BUVIC {APP_VERSION}",
                           style="color: #999; align-self: flex-end; margin-top: 30px")
        self._main_container.append(version)

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
            job_utils = CalculationUtils(DATA_DIR, OUTPUT_DIR, init_progress=self._init_progress, progress_handler=self._make_progress,
                                         finish_progress=self._finish_progress)
            results = calculation(job_utils)
            self._show_result(results)
        except Exception as e:
            self._handle_error(e)

    def _reset_errors(self):
        hide(self._error_label)
        self._error_label.set_text("")

    def _init_progress(self, total: int, text: str = "Calculating..."):
        self._loader.set_label(text)
        self._loader.init(total)

    def _finish_progress(self, duration: float):
        self._duration = duration

    def _make_progress(self, value: float):
        with self._lock:
            self._loader.progress(value)

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

    def _on_form_selection_change(self, widget: gui.Widget, value: bool) -> None:
        """
        Called when the `Manual mode` checkbox is toggled
        """
        del widget  # remove unused parameter
        if value:
            hide(self._main_form)
            show(self._secondary_form)
            self._extra_param_form.register_handler(self._secondary_form.extra_param_change_callback)
        else:
            show(self._main_form)
            hide(self._secondary_form)
            self._extra_param_form.register_handler(self._main_form.extra_param_change_callback)
