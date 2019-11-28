import os
import re
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Tuple, Callable, List, Any

from uv.logic.result import Result
from .calculation_input import CalculationInput
from .irradiance_calculation import IrradianceCalculation, Job
from .utils import create_csv, create_spectrum_plots, create_sza_plot
from ..brewer_infos import get_brewer_info


class JobUtils:

    def __init__(self, output_dir: str, only_csv: bool = False, init_progress: Callable[[int], None] = None,
                 progress_handler: Callable[[float], None] = None, file_type: str = "png"):
        self._output_dir = output_dir
        self._only_csv = only_csv
        self._init_progress = init_progress
        self._progress_handler = progress_handler
        self._file_type = file_type

    def calculate_and_output(self, calculation_input: CalculationInput) -> List[Result]:
        """
        Calculate irradiance, and create plots and csv for a given calculation input

        :param calculation_input: the input for the calculation
        """
        ie = IrradianceCalculation(calculation_input)
        calculation_jobs = ie.calculate()

        if self._init_progress is not None:
            self._init_progress(len(calculation_jobs))

        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)

        result_list = self._execute_jobs(calculation_jobs)

        if not self._only_csv:
            create_sza_plot(self._output_dir, result_list, self._file_type)

        return result_list

    def _execute_jobs(self, jobs: List[Job[Any, Result]]) -> List[Result]:

        thread_pool = ThreadPoolExecutor()
        result_list = []
        future_result = []
        for job in jobs:
            future_result.append(thread_pool.submit(job.call))

        process_pool = ProcessPoolExecutor()
        future_output = []
        for future in future_result:
            result = future.result()
            self._make_progress()
            future_output.append(
                process_pool.submit(self._create_output, result, self._output_dir, self._only_csv, self._file_type))
            result_list.append(result)

        for future in future_output:
            future.result()
            self._make_progress()

        return result_list

    @staticmethod
    def _create_output(result: Result, output_dir: str, only_csv: bool, file_type: str):
        create_csv(output_dir, result)
        if not only_csv:
            create_spectrum_plots(output_dir, result, file_type)
        return result

    def _make_progress(self):
        if self._progress_handler is not None:
            self._progress_handler(0.5)

    def calculate_for_all(self, input_dir: str, albedo: float, aerosol: Tuple[float, float]) -> None:

        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)

        input_list = []
        for file_name in os.listdir(input_dir):
            res = re.match(r'UV(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)', file_name)
            if res is not None:
                days = res.group("days")
                year = res.group("year")
                brewer_id = res.group("brewer_id")

                uv_file = file_name
                b_file = "B" + days + year + "." + brewer_id
                info = get_brewer_info(brewer_id)
                calibration_file = info.uvr_file_name
                arf_file = info.arf_file_name

                if not os.path.exists(input_dir + b_file):
                    print("Corresponding B file '" + b_file + "' not found for UV file '" + uv_file + "', skipping")
                    continue

                if not os.path.exists(input_dir + calibration_file):
                    print(
                        "Corresponding UVR file '" + calibration_file + "' not found for UV file '" + uv_file + "', skipping")
                    continue

                if not os.path.exists(input_dir + arf_file):
                    print("Corresponding ARF file '" + arf_file + "' not found for UV file '" + uv_file + "', skipping")
                    continue

                input_list.append(CalculationInput(
                    albedo,
                    aerosol,
                    input_dir + uv_file,
                    input_dir + b_file,
                    input_dir + calibration_file,
                    input_dir + arf_file
                ))
        job_list = []
        for calculation_input in input_list:
            ie = IrradianceCalculation(calculation_input)
            calculation_jobs = ie.calculate()
            job_list.extend(calculation_jobs)

        if self._init_progress is not None:
            self._init_progress(len(job_list))

        self._execute_jobs(job_list)

    def _handle_input(self, calculation_input: CalculationInput) -> None:
        self.calculate_and_output(calculation_input)
