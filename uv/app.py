import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List

import remi.gui as gui
from remi import App, Label
from remi.gui import VBox

from uv.logic.calculation_input import CalculationInput
from .const import PLOT_DIR
from .gui.utils import show, hide
from .gui.widgets import Title, Level, Loader, ExpertMainForm, SimpleMainForm, ResultWidget
from .logic.irradiance_evaluation import IrradianceEvaluation, Result


class UVApp(App):
    _main_container: VBox
    _main_form: SimpleMainForm
    _secondary_form: ExpertMainForm
    _loader: Loader
    _result_container: ResultWidget
    _error_label: Label

    def __init__(self, *args):
        super(UVApp, self).__init__(*args, static_file_path={'plots': PLOT_DIR})

        self._executor = ThreadPoolExecutor(1)
        self.uv_file = None
        self.calibration_file = None
        self.arf_file = None
        self.b_file = None

    def main(self):
        self._main_container = gui.VBox(width="80%")
        self._main_container.set_style("margin: 30px auto; padding: 20px")

        title = Title(Level.H1, "Irradiance calculation")

        self._forms = VBox()
        self._forms.set_style("width: 100%")

        form_selection_checkbox = gui.CheckBoxLabel("Manual mode")
        form_selection_checkbox.set_style("align-self: flex-start")
        form_selection_checkbox.onchange.do(self._form_selection_change)
        self._forms.append(form_selection_checkbox)

        self._main_form = SimpleMainForm(self.calculate)
        self._secondary_form = ExpertMainForm(self.calculate)
        hide(self._secondary_form)
        self._forms.append(self._main_form)
        self._forms.append(self._secondary_form)

        self._loader = Loader()

        self._result_container = ResultWidget()

        self._main_container.append(title)
        self._main_container.append(self._loader)
        self._main_container.append(self._forms)
        self._main_container.append(self._result_container)

        self._error_label = gui.Label("")
        self._error_label.set_style("color: #E00; font-size: 12pt; font-weight: bold")
        hide(self._error_label)
        self._main_container.append(self._error_label)

        # returning the root widget
        return self._main_container

    def calculate(self, calculation_input: CalculationInput):
        self.reset_errors()
        self._loader.set_progress(0)
        self._loader.set_label("Calculating...")
        show(self._loader)
        hide(self._forms)
        hide(self._result_container)

        try:

            self._check_input(calculation_input)

            ie = IrradianceEvaluation(calculation_input,
                                      progress_handler=self.progress_handler)
            self._executor.submit(self.start_calculation, ie)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            self.show_error(str(e))

    def start_calculation(self, ie: IrradianceEvaluation):
        try:
            result = ie.calculate()
            self.show_result(result)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            self.show_error(str(e))
            raise e

    def reset_errors(self):
        hide(self._error_label)
        self._error_label.set_text("")

    def progress_handler(self, current_progress: int, total_progress: int):
        if total_progress == 0:
            self._loader.set_progress(0)
        else:
            value = int(current_progress * 50 / total_progress)
            self._loader.set_progress(value)

    def show_result(self, results: List[Result]):
        self._loader.set_label("Generating result files...")
        self._loader.set_progress(50)

        self._result_container.display(results, self.progress_handler)

        self._main_form.check_files()
        self._secondary_form.check_files()
        hide(self._loader)
        show(self._forms)
        show(self._result_container)

    def show_error(self, error: str):
        self._main_form.check_files()
        self._secondary_form.check_files()
        hide(self._result_container)
        hide(self._loader)
        show(self._forms)
        show(self._error_label)
        if error is not None:
            self._error_label.set_text(error)
        else:
            print("Error is None")

    def _form_selection_change(self, widget, value: bool):
        if value:
            hide(self._main_form)
            show(self._secondary_form)
        else:
            show(self._main_form)
            hide(self._secondary_form)

    @staticmethod
    def _check_input(calculation_input: CalculationInput):
        if calculation_input is None:
            raise ValueError("Unexpected error: form data could not be read correctly. Please try again")
        if calculation_input.measurement_date is None:
            raise ValueError("Unexpected error: Measurement date has not been correctly set")

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
