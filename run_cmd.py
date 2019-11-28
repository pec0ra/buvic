from __future__ import annotations

import multiprocessing
import os, logging
from argparse import ArgumentParser
from pprint import PrettyPrinter

import progressbar
from matplotlib import rcParams

from uv.const import DEFAULT_ALBEDO_VALUE, DEFAULT_ALPHA_VALUE, DEFAULT_BETA_VALUE, TMP_FILE_DIR
from uv.logic.calculation_input import CalculationInput
from uv.logic.job_utils import JobUtils
from uv.logutils import init_logging

init_logging(logging.WARN)

rcParams.update({'figure.autolayout': True})
rcParams['figure.figsize'] = 10, 7

pp = PrettyPrinter(indent=2)

DEFAULT_DATA_DIR = "data/"
DEFAULT_OUTPUT = "out/"

parser = ArgumentParser(description="Calculate irradiance spectra")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--days-and-brewer-id", "-d", nargs=2, metavar=("DAYS", "BREWER_ID"),
                   help="The date, represented as the days since new year, and the id of the brewer to get the data from")

group.add_argument("--paths", "-p", nargs=4, metavar=("UV_FILE", "B_FILE", "UVR_FILE", "ARF_FILE"),
                   help="The paths to the files. UV_FILE: The file containing the raw uv measurements. B_FILE: The "
                        "file containing the ozone measurements. UVR_FILE: The UVR file containing calibration "
                        "data. ARF_FILE: The file containing the arf data")

group.add_argument("--all", metavar="PATH", help="Finds and converts all UV files in the given PATH")

parser.add_argument("--input-dir", "-i", help="The directory get the files from")
parser.add_argument("--output-dir", "-o", help="The directory to save the results in", default=DEFAULT_OUTPUT)
parser.add_argument("--albedo", "-a", type=float, help="The albedo value to use for the calculations",
                    default=DEFAULT_ALBEDO_VALUE)
parser.add_argument("--aerosol", "-e", type=float, nargs=2, metavar=("ALPHA", "BETA"),
                    default=(DEFAULT_ALPHA_VALUE, DEFAULT_BETA_VALUE),
                    help="The aerosol angstrom's alhpa and beta values to use for the calculations.")
parser.add_argument("--only-csv", "-c", help="Don't generate plots but only csv files", action="store_true")

args = parser.parse_args()
pp.pprint(vars(args))

days_and_brewer_id = args.days_and_brewer_id
paths = args.paths
do_all = args.all
albedo = args.albedo
aerosol = args.aerosol
output_dir = args.output_dir
input_dir = args.input_dir
only_csv = args.only_csv

if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)

widgets = [
    " ", progressbar.RotatingMarker(),
    " ", progressbar.Percentage(), " ",
    progressbar.Bar("#", "[", "]"),
    " | ", progressbar.Timer(),
    " | ", progressbar.ETA(),
]
progress = progressbar.ProgressBar(initial_value=0, min_value=0, max_value=0,
                                   widgets=widgets)
m = multiprocessing.Manager()
lock = m.Lock()


def init_progress(total: int):
    progress.start(total)
    progress.update(0)


def show_progress(value: float):
    if progress is not None:
        with lock:
            progress.update(progress.value + value)


cmd = JobUtils(output_dir, only_csv, init_progress=init_progress, progress_handler=show_progress)
if days_and_brewer_id is not None:
    if input_dir is None:
        input_dir = DEFAULT_DATA_DIR
    days = int(days_and_brewer_id[0])
    brewer_id = days_and_brewer_id[1]
    calculation_input = CalculationInput.from_days_and_bid(
        albedo,
        aerosol,
        input_dir,
        brewer_id,
        days
    )

    progress.start(1)
    cmd.calculate_and_output(calculation_input)

elif paths is not None:
    if input_dir is None:
        input_dir = ""
    calculation_input = CalculationInput(
        albedo,
        aerosol,
        input_dir + paths[0],
        input_dir + paths[1],
        input_dir + paths[2],
        input_dir + paths[3]
    )

    cmd.calculate_and_output(calculation_input)

elif do_all is not None:
    if input_dir is None:
        input_dir = DEFAULT_DATA_DIR

    cmd.calculate_for_all(input_dir, albedo, aerosol)
