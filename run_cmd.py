from __future__ import annotations

import logging
import multiprocessing
import os
from argparse import ArgumentParser
from datetime import date
from pprint import PrettyPrinter

import progressbar
from matplotlib import rcParams

from buvic.const import TMP_FILE_DIR
from buvic.logic.calculation_input import CalculationInput
from buvic.logic.calculation_utils import CalculationUtils
from buvic.logic.file import File
from buvic.logic.file_utils import FileUtils
from buvic.logic.parameter_file import Angstrom
from buvic.logic.settings import Settings
from buvic.logutils import init_logging

rcParams.update({'figure.autolayout': True})
rcParams['figure.figsize'] = 10, 7

pp = PrettyPrinter(indent=2)

DEFAULT_DATA_DIR = "data/"
DEFAULT_OUTPUT = "out/"

settings = Settings()

parser = ArgumentParser(description="Calculate irradiance spectra")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--dates-and-brewer-id", "-d", nargs=3, metavar=("DATE_START", "DATE_END", "BREWER_ID"),
                   help="The dates, in iso format (e.g. 2019-03-24, and the id of the brewer to get the data from")

group.add_argument("--paths", "-p", nargs=4, metavar=("UV_FILE", "B_FILE", "UVR_FILE", "ARF_FILE"),
                   help="The paths to the files. UV_FILE: The file containing the raw uv measurements. B_FILE: The "
                        "file containing the ozone measurements. UVR_FILE: The UVR file containing calibration "
                        "data. ARF_FILE: The file containing the arf data")

group.add_argument("--all", action="store_true", help="Finds and converts all UV files in the input directory")

group.add_argument("--watch", "-w", action="store_true",
                   help="Watches the input directory for file changes and automatically converts changed UV files")

parser.add_argument("--input-dir", "-i", help="The directory to get the files from")
parser.add_argument("--output-dir", "-o", help="The directory to save the results in", default=DEFAULT_OUTPUT)
parser.add_argument("--albedo", "-a", type=float, help="The albedo value to use for the calculations",
                    default=settings.default_albedo)
parser.add_argument("--aerosol", "-e", type=float, nargs=2, metavar=("ALPHA", "BETA"),
                    default=settings.default_aerosol,
                    help="The aerosol angstrom's alpha and beta values to use for the calculations.")
parser.add_argument("--ozone", "-z", type=float, help="The ozone value in DU to use for the calculations if no value is found in a B file",
                    default=settings.default_ozone)
parser.add_argument("--no-coscor", "-c", help="Don't apply cos correction", action="store_true")

args = parser.parse_args()
pp.pprint(vars(args))

dates_and_brewer_id = args.dates_and_brewer_id
paths = args.paths
do_all = args.all
watch = args.watch
albedo = args.albedo
aerosol = Angstrom(args.aerosol[0], args.aerosol[1])
ozone = args.ozone
output_dir = args.output_dir
input_dir = args.input_dir
no_coscor = args.no_coscor

settings.default_albedo = albedo
settings.default_aerosol = aerosol
settings.default_ozone = ozone

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


def init_progress(total: int, text: str):
    del text  # Remove unused variable
    progress.start(total)
    progress.update(0)


def finish_progress(duration: float):
    del duration  # Remove unused variable
    progress.finish()


def show_progress(value: float):
    if progress is not None:
        with lock:
            progress.update(progress.value + value)


if input_dir is None:
    input_dir = DEFAULT_DATA_DIR
cmd = CalculationUtils(input_dir, output_dir, init_progress=init_progress, progress_handler=show_progress,
                       finish_progress=finish_progress)

file_utils = FileUtils(input_dir)

if dates_and_brewer_id is not None:
    init_logging(logging.INFO)

    date_start = date.fromisoformat(dates_and_brewer_id[0])
    date_end = date.fromisoformat(dates_and_brewer_id[1])
    brewer_id = dates_and_brewer_id[2]

    inputs = file_utils.get_calculation_inputs_between(date_start, date_end, brewer_id, settings)
    cmd.calculate_for_inputs(inputs)

elif paths is not None:
    init_logging(logging.WARN)
    if input_dir is None:
        input_dir = ""

    calculation_input = CalculationInput(
        settings,
        File(input_dir + paths[0], input_dir),
        File(input_dir + paths[1], input_dir),
        File(input_dir + paths[2], input_dir),
        File(input_dir + paths[3], input_dir),
    )

    cmd.calculate_for_input(calculation_input)

elif do_all:
    init_logging(logging.WARN)

    inputs = file_utils.get_calculation_inputs(settings)
    cmd.calculate_for_inputs(inputs)

elif watch:
    init_logging(logging.INFO)

    cmd.watch(settings)
