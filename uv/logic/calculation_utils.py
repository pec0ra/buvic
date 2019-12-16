from __future__ import annotations

import concurrent
import os
import re
import time
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from logging import getLogger
from os import path, listdir
from typing import Callable, List, Any, TypeVar, Generic

from watchdog.observers import Observer

from uv.const import CALIBRATION_FILES_SUBDIR, ARF_FILES_SUBDIR, UV_FILES_SUBDIR, B_FILES_SUBDIR, PARAMETER_FILES_SUBDIR
from uv.logic.calculation_event_handler import CalculationEventHandler
from uv.logic.output_utils import create_csv
from uv.logic.result import Result
from uv.logic.utils import date_range, date_to_days
from .calculation_input import CalculationInput, InputParameters
from .irradiance_calculation import IrradianceCalculation
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

        calculation_input.init_properties()

        # Create `IrradianceCalculation` Jobs
        calculation_jobs = self._create_jobs(calculation_input)

        LOG.debug("Scheduling %d jobs for file '%s'", len(calculation_jobs), calculation_input.uv_file_name)

        # Initialize the progress bar
        if self._init_progress is not None:
            self._init_progress(len(calculation_jobs))

        # Execute the jobs
        result_list = self._execute_jobs(calculation_jobs)

        duration = time.time() - start
        if self._finish_progress is not None:
            self._finish_progress(duration)
        LOG.info("Finished calculations for '%s', '%s', '%s' and '%s' in %ds", calculation_input.uv_file_name,
                 calculation_input.b_file_name, calculation_input.calibration_file_name,
                 calculation_input.arf_file_name, duration)
        return result_list

    def calculate_for_all_between(self, start_date: date, end_date: date, brewer_id, parameters: InputParameters,
                                  uvr_file: str or None = None) -> List[Result]:
        """
        Calculate irradiance and create csv for all UV Files found for between a start date and an end date for a given brewer id.

        :param start_date: the dates' lower bound (inclusive) for the measurements
        :param end_date: the dates' upper bound (inclusive) for the measurements
        :param brewer_id: the id of the brewer instrument
        :param parameters: the parameters to use for the calculation
        :param uvr_file: the uvr file to use for the calculation or None to use the default
        :return: the calculation results
        """

        input_list = []
        for d in date_range(start_date, end_date):
            year = d.year - 2000
            days = date_to_days(d)

            LOG.debug("Creating input for date %s as days %d and year %d", d.isoformat(), days, year)
            calculation_input = self._input_from_files(f"{days:03}", f"{year:02}", brewer_id, parameters, uvr_file)
            if calculation_input is not None:
                input_list.append(calculation_input)

        return self._calculate_for_inputs(input_list)

    def calculate_for_all(self, parameters: InputParameters) -> None:
        """
        Calculate irradiance and create csv for all UV Files in a the input directory.

        This will loop through all files of `input_dir` and find all UV files. For each UV file, it will look if
        corresponding B file, UVR file and ARF file exist.
        If they exist, it will call IrradianceCalculation to create a result and it will then create csv from
        this result

        :param parameters: the parameters to use for calculation
        """

        input_list = []
        for file_name in listdir(self._input_dir):
            # UV file names are like `UV12319.070`
            res = re.match(r'UV(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d+)', file_name)

            # If `file_name` is a UV file
            if res is not None:
                days = res.group("days")
                year = res.group("year")
                brewer_id = res.group("brewer_id")

                calculation_input = self._input_from_files(days, year, brewer_id, parameters)
                if calculation_input is not None:
                    input_list.append(calculation_input)

        self._calculate_for_inputs(input_list)

    def watch(self, parameters: InputParameters) -> None:
        """
        Watch a directory for new UV or B files.

        This will create a watchdog on the input directory. Every time a UV file or a B file (recognized by their names) is modified, it
        will calculate the irradiance and generate the corresponding output (csv).

        This method will run until interrupted by the user

        :param parameters: the parameters to use for calculation
        """
        self._init_progress = None
        self._progress_handler = None
        event_handler = CalculationEventHandler(self._on_new_file, parameters)
        observer = Observer()
        observer.schedule(event_handler, self._input_dir)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def _calculate_for_inputs(self, calculation_inputs: List[CalculationInput]) -> List[Result]:
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
            calculation_input.init_properties()

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

    def _on_new_file(self, file_type: str, days: str, year: str, brewer_id: str, parameters: InputParameters) -> None:
        if file_type == "UV":
            calculation_input = self._input_from_files(days, year, brewer_id, parameters)
            if calculation_input is not None:
                self.calculate_for_input(calculation_input)
        if file_type == "B":
            calculation_input = self._input_from_files(days, year, brewer_id, parameters)
            if calculation_input is not None:
                self.calculate_for_input(calculation_input)

    def _input_from_files(self, days: str, year: str, brewer_id: str, parameters: InputParameters, uvr_file: str or None = None):
        uv_file = "UV" + days + year + "." + brewer_id
        b_file = "B" + days + year + "." + brewer_id
        arf_file = "arf_" + brewer_id + ".dat"
        if uvr_file is not None:
            calibration_file = uvr_file
        else:
            info = get_brewer_info(brewer_id)
            calibration_file = info.uvr_file_name
        parameter_file = year + ".par"

        uv_file_path = path.join(self._input_dir, UV_FILES_SUBDIR, uv_file)
        if not path.exists(uv_file_path) and not path.exists(path.join(self._input_dir, UV_FILES_SUBDIR, brewer_id, uv_file)):
            LOG.info("UV file '" + str(uv_file_path) + "' not found, skipping")
            return None
        elif not path.exists(uv_file_path):
            # If the file is not at the root, then it is in a subdirectory
            uv_file_path = path.join(self._input_dir, UV_FILES_SUBDIR, brewer_id, uv_file)

        b_file_path = path.join(self._input_dir, B_FILES_SUBDIR, b_file)
        if not path.exists(b_file_path) and not path.exists(path.join(self._input_dir, B_FILES_SUBDIR, brewer_id, b_file)):
            LOG.warning(f"Corresponding B file '{b_file_path}' not found for UV file '{uv_file}', will use default ozone "
                        "values and straylight correction will be applied as default")
        elif not path.exists(b_file_path):
            # If the file is not at the root, then it is in a subdirectory
            b_file_path = path.join(self._input_dir, B_FILES_SUBDIR, brewer_id, b_file)

        calibration_file_path = path.join(self._input_dir, CALIBRATION_FILES_SUBDIR, calibration_file)
        if not path.exists(calibration_file_path):
            LOG.warning("Corresponding UVR file '" + str(calibration_file_path) + "' not found for UV file '" + uv_file + "', skipping")
            return None

        arf_file_path = path.join(self._input_dir, ARF_FILES_SUBDIR, arf_file)
        if not path.exists(arf_file_path):
            LOG.warning("ARF file was not found for UV file '" + uv_file + "', cos correction will not be applied")
            arf_file_path = None

        parameter_file_path = path.join(self._input_dir, PARAMETER_FILES_SUBDIR, parameter_file)
        if not path.exists(parameter_file_path):
            parameter_file_path = None

        # If everything is ok, return a calculation input
        return CalculationInput(
            parameters,
            uv_file_path,
            b_file_path,
            calibration_file_path,
            arf_file_path,
            parameter_file_name=parameter_file_path
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

        # Create the thread pool and the process pool
        with ThreadPoolExecutor(min(20, os.cpu_count() + 4)) as thread_pool:

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

    def _create_jobs(self, calculation_input: CalculationInput) -> List[Job[int, Result]]:
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

    def _job_task(self, ie: IrradianceCalculation, entry_index: int) -> Result:
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
            self._init_progress(0)

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
        return self._fn(*self._args)


class ExecutionError(Exception):
    pass
