import os
from argparse import ArgumentParser
from pprint import PrettyPrinter

from matplotlib import rcParams

from uv.const import DEFAULT_ALBEDO_VALUE, DEFAULT_ALPHA_VALUE, DEFAULT_BETA_VALUE
from uv.logic.calculation_input import CalculationInput
from uv.logic.irradiance_calculation import IrradianceCalculation
from uv.logic.utils import create_sza_plot, create_spectrum_plots, create_csv

rcParams.update({'figure.autolayout': True})
rcParams['figure.figsize'] = 10, 7

pp = PrettyPrinter(indent=2)

DEFAULT_DATA_DIR = "data/"
DEFAULT_OUTPUT = "out/"

parser = ArgumentParser(description="Calculate irradiance spectra")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--days_and_brewer_id", "-d", nargs=2, metavar=("DAYS", "BREWER_ID"),
                   help="The date, represented as the days since new year, and the id of the brewer to get the data from")

group.add_argument("--paths", "-p", nargs=4, metavar=("UV_FILE", "B_FILE", "UVR_FILE", "ARF_FILE"),
                   help="The paths to the files. UV_FILE: The file containing the raw uv measurements. B_FILE: The "
                        "file containing the ozone measurements. UVR_FILE: The UVR file containing calibration "
                        "data. ARF_FILE: The file containing the arf data")

parser.add_argument("--input_dir", "-i", help="The directory get the files from")
parser.add_argument("--output_dir", "-o", help="The directory to save the results in", default=DEFAULT_OUTPUT)
parser.add_argument("--albedo", "-a", type=float, help="The albedo value to use for the calculations",
                    default=DEFAULT_ALBEDO_VALUE)
parser.add_argument("--aerosol", "-e", type=float, nargs=2, metavar=("ALPHA", "BETA"),
                    default=(DEFAULT_ALPHA_VALUE, DEFAULT_BETA_VALUE),
                    help="The aerosol angstrom's alhpa and beta values to use for the calculations.")

args = parser.parse_args()
pp.pprint(vars(args))

days_and_brewer_id = args.days_and_brewer_id
albedo = args.albedo
aerosol = args.aerosol
output_dir = args.output_dir
input_dir = args.input_dir
if days_and_brewer_id:
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

else:
    if input_dir is None:
        input_dir = ""
    paths = args.paths
    calculation_input = CalculationInput(
        albedo,
        aerosol,
        input_dir + paths[0],
        input_dir + paths[1],
        input_dir + paths[2],
        input_dir + paths[3]
    )

ie = IrradianceCalculation(calculation_input)
results = ie.calculate()

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for result in results:
    create_csv(output_dir, result)
    create_spectrum_plots(output_dir, result, "svg")

create_sza_plot(output_dir, results, "svg")
