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
from __future__ import annotations

import concurrent
import itertools
import os
import time
from concurrent.futures.thread import ThreadPoolExecutor
from logging import getLogger
from os import path
from typing import Callable, List, Any, Tuple

from watchdog.observers import Observer

from buvic.logic.calculation_event_handler import CalculationEventHandler
from buvic.logic.result import Result
from buvic.logic.settings import Settings
from .calculation_input import CalculationInput
from .irradiance_calculation import IrradianceCalculation
from .job import Job
from .output import QasumeOutput, UverOutput, WoudcOutput
from .warnings import get_warnings, clear_warnings

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
        LOG.info(
            "Starting calculation for '%s', '%s', '%s' and '%s'",
            calculation_input.uv_file_name,
            calculation_input.b_file_name,
            calculation_input.calibration_file_name,
            calculation_input.arf_file_name,
        )

        # We collect all warnings and add them to the calculation input
        clear_warnings()
        calculation_input.init_properties()
        calculation_input.add_warnings(get_warnings())

        # Create `IrradianceCalculation` Jobs
        calculation_jobs = self._create_jobs(calculation_input)

        LOG.debug("Scheduling %d jobs for file '%s'", len(calculation_jobs), calculation_input.uv_file_name)

        # Initialize the progress bar
        if self._init_progress is not None:
            self._init_progress(len(calculation_jobs), "Calculating...")

        # Execute the jobs
        result_list = self._execute_jobs(calculation_jobs)

        # Generate the output
        self._generate_output(result_list)

        duration = time.time() - start
        if self._finish_progress is not None:
            self._finish_progress(duration)
        LOG.info(
            "Finished calculations for '%s', '%s', '%s' and '%s' in %ds",
            calculation_input.uv_file_name,
            calculation_input.b_file_name,
            calculation_input.calibration_file_name,
            calculation_input.arf_file_name,
            duration,
        )
        return result_list

    def watch(self, settings: Settings) -> None:
        """
        Watch a directory for new files.

        This will create a watchdog on the input directory. Every time a UV file or a B file (recognized by their names) is modified, it
        will calculate the irradiance and generate the corresponding output (csv).

        This method will run until interrupted by the user

        :param settings: the settings to use for calculation
        """
        self._init_progress = None
        self._progress_handler = None
        event_handler = CalculationEventHandler(self._input_dir, self.calculate_for_input, settings)
        observer = Observer()
        observer.schedule(event_handler, path.join(self._input_dir, "instr"), True)
        observer.schedule(event_handler, path.join(self._input_dir, "uvdata"), True)
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
            self._init_progress(
                len(calculation_inputs),
                f"Collecting data for {len(calculation_inputs)} " f"day{'s' if len(calculation_inputs) > 1 else ''}...",
            )

        # We initialize the data (reading files / querying eubrewnet) and create the jobs on multiple threads for improved performance
        with ThreadPoolExecutor(max_workers=self._get_thread_count()) as thread_pool:
            job_list_list = thread_pool.map(self._init_and_create_jobs, calculation_inputs, timeout=30)

        LOG.debug("Finished initializing inputs and creating jobs")

        # Flatten the list of lists of jobs into a list of jobs
        job_list = list(itertools.chain(*list(job_list_list)))

        if len(job_list) == 0:
            return self._handle_empty_input()

        # Get the number of files for which we do calculations (only used as user information)
        valid_input_count = len(
            [calculation_input for calculation_input in calculation_inputs if len(calculation_input.uv_file_entries) > 0]
        )
        LOG.info("Starting calculation of %d file sections in %d files", len(job_list), valid_input_count)

        # Init progress bar
        if self._init_progress is not None:
            self._init_progress(
                len(job_list),
                f"Calculating irradiance for {len(job_list)} "
                f"section{'s' if len(job_list) > 1 else ''} in {valid_input_count} "
                f"file{'s' if valid_input_count > 1 else ''}...",
            )

        # Execute the jobs
        ret = self._execute_jobs(job_list)

        # Generate the output files
        self._generate_output(ret)

        duration = time.time() - start
        if self._finish_progress is not None:
            self._finish_progress(duration)
        LOG.info("Finished calculation batch in %ds", duration)
        return ret

    def _init_and_create_jobs(self, calculation_input: CalculationInput) -> List[Job]:
        """
        Initialize the properties of a given calculation input and create calculation jobs for it.

        :param calculation_input: the calculation input to initialize and for which to creat the jobs
        :return: the created jobs
        """
        # We collect all warnings and add them to the calculation input
        clear_warnings()
        calculation_input.init_properties()
        calculation_input.add_warnings(get_warnings())
        LOG.debug("Finished initializing properties for %s", calculation_input.date.isoformat())

        if len(calculation_input.uv_file_entries) > 0:
            # Create `IrradianceCalculation` Jobs
            calculation_jobs = self._create_jobs(calculation_input)
        else:
            calculation_jobs = []

        # Report progress to the progress bar
        self._make_progress()

        LOG.debug("Finished creating jobs for %s", calculation_input.date.isoformat())
        return calculation_jobs

    def _execute_jobs(self, jobs: List[Job[Any, Result]]) -> List[Result]:
        """
        Execute given jobs.

        We use a ThreadPoolExecutor to schedule the jobs to improve performance.

        :param jobs: The job to execute
        :return: the results of the jobs.
        """

        result_list: List[Result] = []
        future_result = []

        # Create the thread pool
        with ThreadPoolExecutor(self._get_thread_count()) as thread_pool:

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

            except Exception as e:
                LOG.info("Exception caught in child thread, cancelling all remaining tasks")
                for future in future_result:
                    future.cancel()
                raise e

        # At this point, we have finished calculating the irradiance and writing the results
        LOG.debug("Finished irradiance calculation for '%s'", result_list[0].calculation_input.uv_file_name)
        return result_list

    def _create_jobs(self, calculation_input: CalculationInput) -> List[Job[Tuple[IrradianceCalculation, int], Result]]:
        """
        Create a list of irradiance calculation `Job` that can be scheduled on a thread pool or process pool.
        Each of the job of the list will do the calculation for one of the section of the UV File.

        :param calculation_input: the calculation input for which to create the jobs
        :return: a list of calculation job.
        """

        LOG.debug(
            "Calculating irradiance for '%s', '%s', '%s' and '%s'",
            calculation_input.uv_file_name,
            calculation_input.b_file_name,
            calculation_input.calibration_file_name,
            calculation_input.arf_file_name,
        )

        ie = IrradianceCalculation(calculation_input)

        job_list = []
        for entry_index in range(len(calculation_input.uv_file_entries)):
            job_list.append(Job(self._job_task, (ie, entry_index)))

        return job_list

    @staticmethod
    def _job_task(args: Tuple[IrradianceCalculation, int]) -> Result:
        ie = args[0]
        entry_index = args[1]
        result = ie.calculate(entry_index)
        return result

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

    def _generate_output(self, results: List[Result]):
        start = time.time()
        output_jobs = []
        sorted_results = sorted(results, key=lambda r: r.uv_file_entry.header.date)

        for date, result_iter in itertools.groupby(sorted_results, key=lambda r: r.uv_file_entry.header.date):
            results = sorted(result_iter, key=lambda r: r.spectrum.measurement_times[0])
            if len(results) != 0:
                qasume_jobs = QasumeOutput(self._output_dir, results).get_jobs()
                output_jobs.extend(qasume_jobs)

                uver_jobs = UverOutput(self._output_dir, results).get_jobs()
                output_jobs.extend(uver_jobs)

                if results[0].calculation_input.settings.activate_woudc:
                    woudc_jobs = WoudcOutput(self._output_dir, results).get_jobs()
                    output_jobs.extend(woudc_jobs)

        # Initialize the progress bar
        if self._init_progress is not None:
            self._init_progress(
                len(output_jobs), f"Generating output files",
            )

        # Create the thread pool
        with ThreadPoolExecutor(self._get_thread_count()) as thread_pool:

            future_result = []
            try:
                # Submit the jobs to the thread pool
                for job in output_jobs:
                    future_result.append(thread_pool.submit(job.run))

                try:
                    for future in future_result:
                        # Wait for each job to finish
                        future.result(timeout=40)

                        # Notify the progress bar
                        self._make_progress()

                except concurrent.futures.TimeoutError as e:
                    raise ExecutionError("One of the threads took too long to do its calculations.") from e

            except Exception as e:
                LOG.info("Exception caught in child thread, cancelling all remaining tasks")
                for future in future_result:
                    future.cancel()
                raise e
        LOG.debug(f"File output creation in : {time.time() - start}s")

    @staticmethod
    def _get_thread_count() -> int:
        cpu_count = os.cpu_count() if os.cpu_count() is not None else 2
        return min(20, (cpu_count if cpu_count is not None else 2) + 4)


class ExecutionError(Exception):
    pass
