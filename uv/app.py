import multiprocessing
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable

import remi.gui as gui
from matplotlib import rcParams
from remi import App, Label
from remi.gui import VBox

from uv.logic.calculation_input import CalculationInput
from uv.logic.job_utils import CalculationUtils
from uv.logic.result import Result
from .const import OUTPUT_DIR, DATA_DIR
from .gui.utils import show, hide
from .gui.widgets import Title, Level, Loader, PathMainForm, SimpleMainForm, ResultWidget, ExtraParamForm


class UVApp(App):
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
        super(UVApp, self).__init__(*args, static_file_path={'plots': OUTPUT_DIR})

        # Some tweaking for matplotlib
        rcParams.update({'figure.autolayout': True})
        rcParams['figure.figsize'] = 9, 6

        self._executor = ThreadPoolExecutor(1)
        self._duration = 0

    def main(self):
        self._main_container = gui.VBox(width="80%")
        self._main_container.set_style("margin: 30px auto; padding: 40px")

        title = Title(Level.H1, "Irradiance calculation")

        self._forms = VBox()
        self._forms.set_style("width: 100%")

        form_selection_checkbox = gui.CheckBoxLabel("Manual mode")
        form_selection_checkbox.set_style("align-self: flex-start; margin-bottom: 20px")
        form_selection_checkbox.onchange.do(self._on_form_selection_change)
        self._forms.append(form_selection_checkbox)

        self._extra_param_form = ExtraParamForm()
        self._forms.append(self._extra_param_form)

        self._main_form = SimpleMainForm(self._calculate)
        self._secondary_form = PathMainForm(self._calculate)
        hide(self._secondary_form)
        self._forms.append(self._main_form)
        self._forms.append(self._secondary_form)

        self._extra_param_form.register_handler(self._main_form.extra_param_change_callback)

        self._loader = Loader()

        self._result_container = ResultWidget()

        self._main_container.append(title)
        self._main_container.append(self._loader)
        self._main_container.append(self._forms)

        self._error_label = gui.Label("")
        self._error_label.set_style("color: #E00; font-size: 12pt; font-weight: bold")
        hide(self._error_label)
        self._main_container.append(self._error_label)
        
        self._main_container.append(self._result_container)

        # returning the root widget
        return self._main_container

    def _calculate(self, calculation: Callable[[CalculationUtils], List[Result]]) -> None:
        """
        Start the calculation in a background thread for a given input
        :param calculation: the calculation to execute
        """

        self._reset_errors()
        self._loader.reset()
        show(self._loader)
        hide(self._forms)
        hide(self._result_container)

        self._executor.submit(self._start_calculation, calculation)

    def _start_calculation(self, calculation: Callable[[CalculationUtils], List[Result]]):
        """
        The calculation task to execute on the background thread.

        This creates a `CalculationUtils` and execute the given calculation on it
        :param calculation: the calculation to execute
        """
        try:
            job_utils = CalculationUtils(DATA_DIR, OUTPUT_DIR, init_progress=self._init_progress, progress_handler=self._make_progress,
                                         finish_progress=self._finish_progress, only_csv=True)
            results = calculation(job_utils)
            self._show_result(results)
        except Exception as e:
            self._handle_error(e)

    def _reset_errors(self):
        hide(self._error_label)
        self._error_label.set_text("")

    def _init_progress(self, total: int):
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

    def _handle_error(self, e: Exception):
        traceback.print_tb(e.__traceback__)
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
            print("Error is None")

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

    @staticmethod
    def _check_input(calculation_input: CalculationInput) -> None:
        """
        Check a given calculation input for consistency and throw a `ValueError` if any problem is found.
        :param calculation_input: the calculation input to check
        """

        if calculation_input is None:
            raise ValueError("Unexpected error: form data could not be read correctly. Please try again")
        if calculation_input.albedo is None:
            raise ValueError("Unexpected error: Albedo has not been correctly set")
        if calculation_input.aerosol is None:
            raise ValueError("Unexpected error: Aerosol has not been correctly set")

        if calculation_input.uv_file_name is None:
            raise ValueError("Unexpected error: UV File name could not be set correctly")
        if calculation_input.calibration_file_name is None:
            raise ValueError("Unexpected error: UVR File name could not be set correctly")
        if calculation_input.b_file_name is None:
            raise ValueError("Unexpected error: B File name could not be set correctly")
        if calculation_input.arf_file_name is None:
            raise ValueError("Unexpected error: ARF File name could not be set correctly")

        if not os.path.exists(calculation_input.uv_file_name):
            raise ValueError("UV File name could not be find for the given brewer id and date")
        if not os.path.exists(calculation_input.calibration_file_name):
            raise ValueError("UVR File name could not be find for the given brewer id")
        if not os.path.exists(calculation_input.b_file_name):
            raise ValueError("B File name could not be find for the given brewer id and date")
        if not os.path.exists(calculation_input.arf_file_name):
            raise ValueError("ARF File name could not be find for the given brewer id")
