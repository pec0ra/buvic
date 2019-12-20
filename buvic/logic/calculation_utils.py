from __future__ import annotations

import concurrent
import os
import threading
import time
import warnings
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass
from logging import getLogger
from os import path
from typing import Callable, List, Any, TypeVar, Generic, Optional, Tuple
from warnings import warn

from watchdog.observers import Observer

from buvic.const import ARF_FILES_SUBDIR, UV_FILES_SUBDIR, B_FILES_SUBDIR, PARAMETER_FILES_SUBDIR
from buvic.logic.calculation_event_handler import CalculationEventHandler
from buvic.logic.file import File
from buvic.logic.output_utils import create_csv
from buvic.logic.result import Result
from buvic.logic.settings import Settings
from buvic.logic.utils import days_to_date
from .calculation_input import CalculationInput
from .irradiance_calculation import IrradianceCalculation

LOG = getLogger(__name__)


class CalculationUtils:
    """
    A utility to create and schedule calculation jobs.
    """

    warnings_lock = threading.RLock()

    def __init__(
            self,
            input_dir: str,
            output_dir: str,
            init_progress: Callable[[int, str], None] = None,
            finish_progress: Callable[[float], None] = None,
            progress_handler: Callable[[float], None] = None,
    ):
        """
        Create an instance of JobUtils with the given parameters
        :param input_dir: the directory to get the files from
        :param output_dir: the directory to save the csv in
        :param init_progress: will be called at the beginning of the calculation with the total number of calculations
                              as parameter
        :param finish_progress: will be called at the end of the calculation
        :param progress_handler: will be called every time progress is made with the amount of progress given as
                                 parameter
        """

        self._input_dir = input_dir
        self._output_dir = output_dir
        self._init_progress = init_progress
        self._finish_progress = finish_progress
        self._progress_handler = progress_handler

    def calculate_for_input(self, calculation_input: CalculationInput) -> List[Result]:
        """
        Calculate irradiance and create csv for a given calculation input

        :param calculation_input: the input for the calculation
        :return: the results of the calculation
        """
        start = time.time()
        LOG.info("Starting calculation for '%s', '%s', '%s' and '%s'", calculation_input.uv_file_name,
                 calculation_input.b_file_name, calculation_input.calibration_file_name,
                 calculation_input.arf_file_name)

        # We collect all warnings and add them to the calculation input
        with self.warnings_lock, warnings.catch_warnings(record=True) as w:
            calculation_input.init_properties()
            calculation_input.add_warnings(w)

        # Create `IrradianceCalculation` Jobs
        calculation_jobs = self._create_jobs(calculation_input)

        LOG.debug("Scheduling %d jobs for file '%s'", len(calculation_jobs), calculation_input.uv_file_name)

        # Initialize the progress bar
        if self._init_progress is not None:
            self._init_progress(len(calculation_jobs), "Calculating...")

        # Execute the jobs
        result_list = self._execute_jobs(calculation_jobs)

        duration = time.time() - start
        if self._finish_progress is not None:
            self._finish_progress(duration)
        LOG.info("Finished calculations for '%s', '%s', '%s' and '%s' in %ds", calculation_input.uv_file_name,
                 calculation_input.b_file_name, calculation_input.calibration_file_name,
                 calculation_input.arf_file_name, duration)
        return result_list

    def watch(self, settings: Settings) -> None:
        """
        TODO: fix me
        Watch a directory for new UV or B files.

        This will create a watchdog on the input directory. Every time a UV file or a B file (recognized by their names) is modified, it
        will calculate the irradiance and generate the corresponding output (csv).

        This method will run until interrupted by the user

        :param settings: the settings to use for calculation
        """
        self._init_progress = None
        self._progress_handler = None
        event_handler = CalculationEventHandler(self._on_new_file, settings)
        observer = Observer()
        observer.schedule(event_handler, self._input_dir)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def calculate_for_inputs(self, calculation_inputs: List[CalculationInput]) -> List[Result]:
        """
        Calculate irradiance and create csv for a given list of calculation inputs

        :param calculation_inputs: the inputs for the calculation
        :return: the results of the calculation
        """
        start = time.time()

        if len(calculation_inputs) == 0:
            return self._handle_empty_input()

        # Initialize the progress bar
        if self._init_progress is not None:
            self._init_progress(len(calculation_inputs), f"Reading {len(calculation_inputs)} "
                                                         f"file{'s' if len(calculation_inputs) > 1 else ''}...")
        job_list = []
        for calculation_input in calculation_inputs:
            # We collect all warnings and add them to the calculation input
            with self.warnings_lock, warnings.catch_warnings(record=True) as w:
                calculation_input.init_properties()
                calculation_input.add_warnings(w)

            # Create `IrradianceCalculation` Jobs
            calculation_jobs = self._create_jobs(calculation_input)
            job_list.extend(calculation_jobs)
            self._make_progress()

        LOG.info("Starting calculation of %d file sections in %d files", len(job_list), len(calculation_inputs))
        # Init progress bar
        if self._init_progress is not None:
            self._init_progress(len(job_list), f"Calculating irradiance for {len(job_list)} "
                                               f"section{'s' if len(job_list) > 1 else ''} in {len(calculation_inputs)} "
                                               f"file{'s' if len(calculation_inputs) > 1 else ''}...")

        # Execute the jobs
        ret = self._execute_jobs(job_list)

        duration = time.time() - start
        if self._finish_progress is not None:
            self._finish_progress(duration)
        LOG.info("Finished calculation batch in %ds", duration)
        return ret

    def _on_new_file(self, file_type: str, days: str, year: str, brewer_id: str, settings: Settings) -> None:
        """
        TODO: fix me
        """
        if file_type == "UV":
            calculation_input = self._input_from_files(days, year, brewer_id, settings, File("TODO", "TODO"))
            if calculation_input is not None:
                self.calculate_for_input(calculation_input)
        if file_type == "B":
            calculation_input = self._input_from_files(days, year, brewer_id, settings, File("TODO", "TODO"))
            if calculation_input is not None:
                self.calculate_for_input(calculation_input)

    def _input_from_files(self, days: str, year: str, brewer_id: str, settings: Settings, uvr_file: File):
        """
        TODO: deprecated

        use FileUtils._input_from_files instead
        """
        uv_file_name = "UV" + days + year + "." + brewer_id
        b_file_name = "B" + days + year + "." + brewer_id
        arf_file_name = "arf_" + brewer_id + ".dat"
        parameter_file_name = year + ".par"

        uv_file: File = File(path.join(self._input_dir, UV_FILES_SUBDIR, uv_file_name),
                             path.join(self._input_dir, UV_FILES_SUBDIR))
        if not path.exists(uv_file.full_path):
            LOG.info("UV file '" + str(uv_file) + "' not found, skipping")
            return None

        b_file: Optional[File] = File(path.join(self._input_dir, B_FILES_SUBDIR, b_file_name),
                                      path.join(self._input_dir, B_FILES_SUBDIR))
        if b_file is not None and not path.exists(b_file.full_path):
            LOG.warning(f"Corresponding B file '{b_file}' not found for UV file '{uv_file}', will use default ozone "
                        "values and straylight correction will be applied as default")
            warn(f"Corresponding B file '{b_file}' not found for UV file '{uv_file}', default ozone value is used"
                 f"and straylight correction is applied")
            b_file = None

        arf_file: Optional[File] = File(path.join(self._input_dir, ARF_FILES_SUBDIR, arf_file_name),
                                        path.join(self._input_dir, ARF_FILES_SUBDIR))
        if arf_file is not None and not path.exists(arf_file.full_path):
            LOG.warning("ARF file was not found for UV file '" + uv_file.file_name + "', cos correction will not be applied")
            warn(f"ARF file was not found for UV file '{uv_file.file_name}', cos correction has not been applied")
            arf_file = None

        parameter_file: Optional[File] = File(path.join(self._input_dir, PARAMETER_FILES_SUBDIR, parameter_file_name),
                                              path.join(self._input_dir, PARAMETER_FILES_SUBDIR))
        if parameter_file is not None and not path.exists(parameter_file.full_path):
            parameter_file = None

        # If everything is ok, return a calculation input
        return CalculationInput(
            brewer_id,
            days_to_date(int(days), int(year)),
            settings,
            uv_file,
            b_file,
            uvr_file,
            arf_file,
            parameter_file_name=parameter_file
        )

    def _execute_jobs(self, jobs: List[Job[Any, Result]]) -> List[Result]:
        """
        Execute given jobs and create output qasume files for them.

        For each one of the given jobs, two things are done:
            1. The irradiance is calculated
            2. Qasume files are created and written to the output directory

        We use a ThreadPoolExecutor to schedule the jobs since calling LibRadtran already creates a new process.

        :param jobs: The job to execute
        :return: the results of the jobs.
        """

        result_list: List[Result] = []
        future_result = []

        cpu_count = os.cpu_count() if os.cpu_count() is not None else 2
        # Create the thread pool and the process pool
        with ThreadPoolExecutor(min(20, (cpu_count if cpu_count is not None else 2) + 4)) as thread_pool:

            try:
                # Submit the jobs to the thread pool
                for job in jobs:
                    future_result.append(thread_pool.submit(job.run))

                try:
                    for future in future_result:
                        # Wait for each job to finish and produce a result
                        result: Result = future.result(timeout=40)

                        # Notify the progress bar
                        self._make_progress()

                        # Add the result to the return list
                        result_list.append(result)

                except concurrent.futures.TimeoutError as e:
                    raise ExecutionError("One of the threads took too long to do its calculations.") from e

                # At this point, we have finished waiting for all future_results (irradiance calculation)
                LOG.debug("Finished irradiance calculation for '%s'", result_list[0].calculation_input.uv_file_name)

                return result_list
            except Exception as e:
                LOG.info("Exception caught in child thread, cancelling all remaining tasks")
                for future in future_result:
                    future.cancel()
                raise e

    def _create_jobs(self, calculation_input: CalculationInput) -> List[Job[Tuple[IrradianceCalculation, int], Result]]:
        """
        Create a list of irradiance calculation `Job` that can be scheduled on a thread pool or process pool.
        Each of the job of the list will do the calculation for one of the section of the UV File.

        :param calculation_input: the calculation input for which to create the jobs
        :return: a list of calculation job.
        """

        LOG.debug("Calculating irradiance for '%s', '%s', '%s' and '%s'", calculation_input.uv_file_name,
                  calculation_input.b_file_name, calculation_input.calibration_file_name,
                  calculation_input.arf_file_name)

        ie = IrradianceCalculation(calculation_input)

        job_list = []
        for entry_index in range(len(calculation_input.uv_file_entries)):
            job_list.append(
                Job(self._job_task, (ie, entry_index))
            )

        return job_list

    def _job_task(self, args: Tuple[IrradianceCalculation, int]) -> Result:
        ie = args[0]
        entry_index = args[1]
        result = ie.calculate(entry_index)
        self._create_output(result, self._output_dir)
        return result

    @staticmethod
    def _create_output(result: Result, output_dir: str) -> None:
        """
        Create the csv for a given result.
        The created csv will be saved as file.
        :param result: the result for which to create the output
        """

        LOG.debug("Starting creating output for section %d of '%s'", result.index,
                  result.calculation_input.uv_file_name)

        create_csv(output_dir, result)

    def _make_progress(self) -> None:
        """
        Notify the progressbar of progress.
        """
        if self._progress_handler is not None:
            self._progress_handler(1)

    def _handle_empty_input(self) -> List[Result]:
        # Init progress bar
        if self._init_progress is not None:
            self._init_progress(0, "Calculating...")

        if self._finish_progress is not None:
            self._finish_progress(0)

        LOG.warning("No input file found for the given parameters")

        return []


INPUT = TypeVar('INPUT')
RETURN = TypeVar('RETURN')


@dataclass
class Job(Generic[INPUT, RETURN]):
    _fn: Callable[[INPUT], RETURN]
    _args: INPUT

    def run(self) -> RETURN:
        """
        Execute the job
        :return: the job's return value
        """
        return self._fn(self._args)


class ExecutionError(Exception):
    pass
