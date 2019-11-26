import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List

import remi.gui as gui
from remi import App

from uv.logic.calculation_input import CalculationInput
from .const import PLOT_DIR
from .gui.utils import show, hide
from .gui.widgets import Title, Level, Loader, SimpleMainForm, ResultWidget
from .logic.irradiance_evaluation import IrradianceEvaluation, Result


class UVApp(App):
    def __init__(self, *args):
        super(UVApp, self).__init__(*args, static_file_path={'plots': PLOT_DIR})
        self._executor = ThreadPoolExecutor(1)
        self.uv_file = None
        self.calibration_file = None
        self.arf_file = None
        self.b_file = None

    def main(self):
        self.main_container = gui.VBox(width="80%")
        self.main_container.set_style("margin: 30px auto; padding: 20px")

        self.title = Title(Level.H1, "Irradiance calculation")

        self.main_form = SimpleMainForm(self.calculate)

        self.loader = Loader()

        self.result_container = ResultWidget()

        self.main_container.append(self.title)
        self.main_container.append(self.loader)
        self.main_container.append(self.main_form)
        self.main_container.append(self.result_container)

        self.error_label = gui.Label("")
        self.error_label.set_style("color: #E00; font-size: 12pt; font-weight: bold")
        hide(self.error_label)
        self.main_container.append(self.error_label)

        # returning the root widget
        return self.main_container

    def calculate(self, calculation_input: CalculationInput):
        self.reset_errors()
        self.loader.set_progress(0)
        self.loader.set_label("Calculating...")
        show(self.loader)
        hide(self.main_form)
        hide(self.result_container)

        ie = IrradianceEvaluation(calculation_input,
                                  progress_handler=self.progress_handler)
        self._executor.submit(self.start_calculation, ie)

    def start_calculation(self, ie: IrradianceEvaluation):
        try:
            result = ie.calculate()
            self.show_result(result)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            self.show_error(str(e))
            raise e

    def reset_errors(self):
        hide(self.error_label)
        self.error_label.set_text("")

    def progress_handler(self, current_progress: int, total_progress: int):
        if total_progress == 0:
            self.loader.set_progress(0)
        else:
            value = int(current_progress * 50 / total_progress)
            self.loader.set_progress(value)

    def show_result(self, results: List[Result]):
        self.loader.set_label("Generating result files...")
        self.loader.set_progress(50)

        self.result_container.display(results, self.progress_handler)

        self.main_form.check_files()
        hide(self.loader)
        show(self.main_form)
        show(self.result_container)

    def show_error(self, error: str):
        self.main_form.check_files()
        hide(self.result_container)
        hide(self.loader)
        show(self.main_form)
        show(self.error_label)
        if error is not None:
            self.error_label.set_text(error)
        else:
            print("Error is None")
