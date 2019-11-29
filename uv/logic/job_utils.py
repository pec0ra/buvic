from __future__ import annotations

import re
import time
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass
from logging import getLogger
from os import path, makedirs, listdir
from typing import Tuple, Callable, List, Any, TypeVar, Generic

from watchdog.observers import Observer

from uv.const import DEFAULT_ALBEDO_VALUE, DEFAULT_BETA_VALUE, DEFAULT_ALPHA_VALUE
from uv.logic.calculation_event_handler import CalculationEventHandler
from uv.logic.result import Result
from .calculation_input import CalculationInput
from .irradiance_calculation import IrradianceCalculation
from .utils import create_csv, create_spectrum_plots, create_sza_plot
from ..brewer_infos import get_brewer_info

LOG = getLogger(__name__)


class CalculationUtils:
    """
    A utility to create and schedule calculation jobs.
    """

    def __init__(
            self,
            input_dir: str,
            output_dir: str,
            only_csv: bool = False,
            init_progress: Callable[[int], None] = None,
            progress_handler: Callable[[float], None] = None,
            file_type: str = "png",
            albedo: float = DEFAULT_ALBEDO_VALUE,
            aerosol: Tuple[float, float] = (DEFAULT_ALPHA_VALUE, DEFAULT_BETA_VALUE)
    ):
        """
        Create an instance of JobUtils with the given parameters
        :param input_dir: the directory to get the files from
        :param output_dir: the directory to save the plots and csv in
        :param only_csv: whether to only create csv files (no plots)
        :param init_progress: will be called at the beginning of the calculation with the total number of calculations
                              as parameter
        :param progress_handler: will be called every time progress is made with the amount of progress given as
                                 parameter
        :param file_type: the file extension of the plots
        :param albedo: the albedo to set for the calculations
        :param aerosol: the aerosol values to set for the calculations
        """

        self._input_dir = input_dir
        self._output_dir = output_dir
        self._only_csv = only_csv
        self._init_progress = init_progress
        self._progress_handler = progress_handler
        self._file_type = file_type
        self._albedo = albedo
        self._aerosol = aerosol

    def calculate_and_output(self, calculation_input: CalculationInput) -> List[Result]:
        """
        Calculate irradiance, and create plots and csv for a given calculation input

        :param calculation_input: the input for the calculation
        :return: the results of the calculation
        """
        start = time.time()
        LOG.info("Starting calculation for '%s', '%s', '%s' and '%s'", calculation_input.uv_file_name,
                 calculation_input.b_file_name, calculation_input.calibration_file_name,
                 calculation_input.arf_file_name)

        # Create output directory if needed
        if not path.exists(self._output_dir):
            makedirs(self._output_dir)

        # Create `IrradianceCalculation` Jobs
        calculation_jobs = self._create_jobs(calculation_input)

        LOG.debug("Scheduling %d jobs for file '%s'", len(calculation_jobs), calculation_input.uv_file_name)

        # Initialize the progress bar
        if self._init_progress is not None:
            self._init_progress(len(calculation_jobs))

        # Execute the jobs
        result_list = self._execute_jobs(calculation_jobs)

        # Create an extra plot of the correction factor against the szas
        if not self._only_csv:
            create_sza_plot(self._output_dir, result_list, self._file_type)

        LOG.info("Finished calculations for '%s', '%s', '%s' and '%s' in %ds", calculation_input.uv_file_name,
                 calculation_input.b_file_name, calculation_input.calibration_file_name,
                 calculation_input.arf_file_name, time.time() - start)
        return result_list

    def calculate_for_all(self) -> None:
        """
        Create plots and csv for all UV Files in a the input directory.

        This will loop through all files of `input_dir` and find all UV files. For each UV file, it will look if
        corresponding B file, UVR file and ARF file exist.
        If they exist, it will call IrradianceCalculation to create a result and it will then create plots and csv from
        this result
        """

        if not path.exists(self._output_dir):
            makedirs(self._output_dir)

        input_list = []
        for file_name in listdir(self._input_dir):
            # UV file names are like `UV12319.070`
            res = re.match(r'UV(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)', file_name)

            # If `file_name` is a UV file
            if res is not None:
                days = res.group("days")
                year = res.group("year")
                brewer_id = res.group("brewer_id")

                calculation_input = self.input_from_files(days, year, brewer_id)
                if calculation_input is not None:
                    input_list.append(calculation_input)

        job_list = []
        for calculation_input in input_list:
            # Create `IrradianceCalculation` Jobs
            calculation_jobs = self._create_jobs(calculation_input)
            job_list.extend(calculation_jobs)

        print("Starting calculation of ", len(job_list), " file sections in ", len(input_list), " files")
        # Init progress bar
        if self._init_progress is not None:
            self._init_progress(len(job_list))

        # Execute the jobs
        self._execute_jobs(job_list)

    def watch(self) -> None:
        """
        Watch a directory for new UV or B files.

        This will create a watchdog on the input directory. Every time a UV file or a B file (recognized by their names) is modified, it
        will calculate the irradiance and generate the corresponding output (plots/csv).

        This method will run until interrupted by the user
        """
        self._init_progress = None
        self._progress_handler = None
        event_handler = CalculationEventHandler(self._on_new_file)
        observer = Observer()
        observer.schedule(event_handler, self._input_dir)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def _on_new_file(self, file_type: str, days: str, year: str, brewer_id: str) -> None:
        if file_type == "UV":
            calculation_input = self.input_from_files(days, year, brewer_id)
            if calculation_input is not None:
                self.calculate_and_output(calculation_input)
        if file_type == "B":
            calculation_input = self.input_from_files(days, year, brewer_id)
            if calculation_input is not None:
                self.calculate_and_output(calculation_input)

    def input_from_files(self, days: str, year: str, brewer_id: str):
        uv_file = "UV" + days + year + "." + brewer_id
        b_file = "B" + days + year + "." + brewer_id
        info = get_brewer_info(brewer_id)
        calibration_file = info.uvr_file_name
        arf_file = info.arf_file_name

        if not path.exists(path.join(self._input_dir, uv_file)):
            print("Corresponding UV file '" + uv_file + "' not found for B file '" + b_file + "', skipping")
            return None

        if not path.exists(path.join(self._input_dir, b_file)):
            print("Corresponding B file '" + b_file + "' not found for UV file '" + uv_file + "', skipping")
            return None

        if not path.exists(path.join(self._input_dir, calibration_file)):
            print("Corresponding UVR file '" + calibration_file + "' not found for UV file '" + uv_file + "', skipping")
            return None

        if not path.exists(path.join(self._input_dir, arf_file)):
            print("Corresponding ARF file '" + arf_file + "' not found for UV file '" + uv_file + "', skipping")
            return None

        # If everything is ok, return a calculation input
        return CalculationInput(
            self._albedo,
            self._aerosol,
            path.join(self._input_dir, uv_file),
            path.join(self._input_dir, b_file),
            path.join(self._input_dir, calibration_file),
            path.join(self._input_dir, arf_file)
        )

    def _execute_jobs(self, jobs: List[Job[Any, Result]]) -> List[Result]:
        """
        Execute given jobs and create output plots and csv for them.

        For each one of the given jobs, two things are done:
            1. The job is scheduled on a thread pool to asynchronously produce a Result
            2. For the result of step 1, the generation of plots and csv is scheduled on a process pool

        We use a ThreadPoolExecutor to schedule the jobs since it is lighter and faster than a ProcessPoolExecutor.
        For the generation of plots, we have to use a ProcessPoolExecutor since matplotlib can't run in parallel threads
        but only in different processes.

        :param jobs: The job to execute
        :return: the results of the jobs.
        """

        result_list: List[Result] = []
        future_result = []

        # Create the thread pool and the process pool
        with ThreadPoolExecutor() as thread_pool, ProcessPoolExecutor() as process_pool:

            # Submit the jobs to the thread pool
            for job in jobs:
                future_result.append(thread_pool.submit(job.call))

            future_output = []

            for future in future_result:
                # Wait for each job to finish and produce a result
                result = future.result()

                # Notify the progress bar
                self._make_progress()

                # Schedule the creation of plots and csv
                future_output.append(
                    process_pool.submit(self._create_output, result, self._output_dir, self._only_csv, self._file_type))

                # Add the result to the return list
                result_list.append(result)

            # At this point, we have finished waiting for all future_results (irradiance calculation)
            LOG.debug("Finished irradiance calculation for '%s'", result_list[0].calculation_input.uv_file_name)

            for future in future_output:
                # Wait for each plots/csv creation to finish
                future.result()

                # Notify the progress bar
                self._make_progress()

            # At this point, we have finished waiting for all future_outputs (plot/csv creations)
            LOG.debug("Finished creating output for '%s'", result_list[0].calculation_input.uv_file_name)

            return result_list

    @staticmethod
    def _create_jobs(calculation_input: CalculationInput) -> List[Job[int, Result]]:
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
                Job(ie.calculate, entry_index)
            )

        return job_list

    @staticmethod
    def _create_output(result: Result, output_dir: str, only_csv: bool, file_type: str) -> None:
        """
        Create the plots and csv for a given result.
        The created plots and csv will be saved as files.
        :param result: the result for which to create the output
        """

        LOG.debug("Starting creating output for section %d of '%s'", result.index,
                  result.calculation_input.uv_file_name)

        create_csv(output_dir, result)
        if not only_csv:
            create_spectrum_plots(output_dir, result, file_type)

    def _make_progress(self) -> None:
        """
        Notify the progressbar of progress.

        Since we perform two steps for each of the jobs, we increment the progress by 0.5 for each step.
        """
        if self._progress_handler is not None:
            self._progress_handler(0.5)


INPUT = TypeVar('INPUT')
RETURN = TypeVar('RETURN')


@dataclass
class Job(Generic[INPUT, RETURN]):
    _fn: Callable[[INPUT], RETURN]
    _args: INPUT

    def call(self) -> RETURN:
        """
        Execute the job
        :return: the job's return value
        """
        return self._fn(self._args)

