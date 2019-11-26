import os
import sys
from datetime import date
from shutil import rmtree

from matplotlib import rcParams

from uv.logic.irradiance_evaluation import IrradianceEvaluation
from uv.logic.calculation_input import CalculationInput
from uv.logic.utils import create_sza_plot, create_spectrum_plots

DATA_DIR = "../Misc/data/"

rcParams.update({'figure.autolayout': True})
rcParams['figure.figsize'] = 10, 7

plot_output_dir = "plots/"
if len(sys.argv) <= 4:
    days = int(sys.argv[1])
    brewer_id = sys.argv[2]
    calculation_input = CalculationInput.from_days_and_bid(DATA_DIR, brewer_id, days)

    if len(sys.argv) > 3:
        plot_output_dir = sys.argv[3]
else:
    calculation_input = CalculationInput(
        date.today(),
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4]
    )

    if len(sys.argv) > 4:
        plot_output_dir = sys.argv[4]

ie = IrradianceEvaluation(calculation_input)
results = ie.calculate()

if os.path.exists(plot_output_dir):
    print('Overwriting last output')
    rmtree(plot_output_dir)

os.makedirs(plot_output_dir)

for result in results:
    create_spectrum_plots(plot_output_dir, results)

create_sza_plot(plot_output_dir, results, "eps")

