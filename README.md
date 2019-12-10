# UV irradiance calculations


This repository contains a set of tools to calculate the cosine corrected irradiance from raw UV measurements.

## Table of content
<!--ts-->
   * [UV irradiance calculations](#uv-irradiance-calculations)
      * [Table of content](#table-of-content)
      * [Requirements](#requirements)
      * [UV Web Application](#uv-web-application)
      * [Command Line App](#command-line-app)
         * [1. Calculate dates and brewer id](#1-calculate-dates-and-brewer-id)
         * [2. Calculate for given files](#2-calculate-for-given-files)
         * [3. Calculate for all files of a given directory](#3-calculate-for-all-files-of-a-given-directory)
         * [4. Watchdog](#4-watchdog)
      * [Installer](#installer)
      * [Releases](#releases)
      * [Docker](#docker)
         * [1. UV Server](#1-uv-server)
         * [2. UV Watch](#2-uv-watch)
      * [Implementation](#implementation)
         * [1. User Interface](#1-user-interface)
         * [2. Job creation / handling](#2-job-creation--handling)
         * [3. Calculations](#3-calculations)

<!-- Added by: basile, at: Di Dez 10 10:26:23 CET 2019 -->

<!--te-->

## Requirements

All python commands required python >= 3.7 and the libraries listed in [requirements.txt](requirements.txt).
These libraries can be installed with the pip command:
```
pip install -r requirements.txt
```

The Docker images require docker


## UV Web Application

UV Web Application is a small application running in the browser to facilitate the execution of irradiance calculation.

It offers the possibility to choose dates and a brewer id to automatically find the measurement files from a predefined set or to manually upload measurement files (manual mode).

![GUI](assets/gui.png)

**Instructions:**

Run:
```
python run.py
```
The application should automatically open in the browser.

## Command Line App

The command line offers 4 different possibilities to perform irradiance calculations.

1. Calculate for dates and brewer id
2. Calculate for given files
3. Calculate for all files of a given directory
4. Monitor a directory for changes and execute the calculation every time new measurement files are added

**Instructions:**
Help about the command line can be shown with:
```
python run_cmd.py -h
```
or
```
python run_cmd.py --help
```
which yields the result:
```
usage: run_cmd.py [-h]
                  (--dates-and-brewer-id DATE_START DATE_END BREWER_ID | --paths UV_FILE B_FILE UVR_FILE ARF_FILE | --all | --watch)
                  [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]
                  [--albedo ALBEDO] [--aerosol ALPHA BETA] [--ozone OZONE]
                  [--no-coscor] [--no-plots]

Calculate irradiance spectra

optional arguments:
  -h, --help            show this help message and exit
  --dates-and-brewer-id DATE_START DATE_END BREWER_ID, -d DATE_START DATE_END BREWER_ID
                        The dates, in iso format (e.g. 2019-03-24, and the id
                        of the brewer to get the data from
  --paths UV_FILE B_FILE UVR_FILE ARF_FILE, -p UV_FILE B_FILE UVR_FILE ARF_FILE
                        The paths to the files. UV_FILE: The file containing
                        the raw uv measurements. B_FILE: The file containing
                        the ozone measurements. UVR_FILE: The UVR file
                        containing calibration data. ARF_FILE: The file
                        containing the arf data
  --all                 Finds and converts all UV files in the input directory
  --watch, -w           Watches the input directory for file changes and
                        automatically converts changed UV files
  --input-dir INPUT_DIR, -i INPUT_DIR
                        The directory to get the files from
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        The directory to save the results in
  --albedo ALBEDO, -a ALBEDO
                        The albedo value to use for the calculations
  --aerosol ALPHA BETA, -e ALPHA BETA
                        The aerosol angstrom's alpha and beta values to use
                        for the calculations.
  --ozone OZONE, -z OZONE
                        The ozone value in DU to use for the calculations if
                        no value is found in a B file
  --no-coscor, -c       Don't apply cos correction
  --no-plots, -q        Don't generate plots but only qasume files
```
The options `--days-and-brewer-id`, `--paths`, `--all` and `--watch` correspond to the 4 different ways to run the tool and only one can be used at a time.

The options `--input-dir`, `--output-dir`, `--albedo`, `--aerosol` , `--ozone`, `--no-coscor` and `--no-plots` are optional parameters and can be used with any of the 4 options cited above. If not specified, default values will be used.

### 1. Calculate dates and brewer id

This command search for measurements between two dates for a brewer id from a preset of files.
The dates are given in iso format `yyyy-mm-dd`

**Examples:**

Run the calculation for brewer `070` on June 24th, 25th and 26th and write the output in the `brewer117` directory:
```
python run_cmd.py --days-and-brewer-id 2019-06-24 2019-06-26 070 --output-dir brewer177/
```

Run the calculation for brewer `186` on June 25th and 26th with an albedo of 0.1 and angström's alpha of 1.3 and beta of 0.1 as aerosol (using shortcuts flags `-d`, `-a` and `-e` instead of their full versions). The `-c` parameter (or `--only-csv`) tells that we don't want to generate plots but only csv files
```
python run_cmd.py -d 2019-06-25 2019-06-26 186 -a 0.1 -e 1.3 0.1 -c
```
Note that if `--input-dir` is not specified, the measurement files will be taken from `data/`.

### 2. Calculate for given files

This command executes the calculation for four given measurement files:
1. UV File: Raw uv measurements
2. B File: For ozone measurements
3. UVR File: The instrument calibration data
4. ARF File: TODO

**Examples:**

Run the calculation for the four files in the directory `my_measurement_files`:
```
python run_cmd.py --input-dir my_measurement_files/ --paths UV17519.070 B17519.070 UVR17319.070 arf_070.dat
```
Note that if `--input-dir` is not specified, the file paths are relative to the working directory.

Run the calculation for the four files with an albedo of 0.1 and angström's alpha of 1.3 and beta of 0.1 as aerosol (using shortcuts flags `-p`, `-a` and `-e` instead of their full versions). The `-c` parameter (or `--only-csv`) tells that we don't want to generate plots but only csv files
```
python run_cmd.py -p data/UV17519.070 data/B17519.070 data/UVR17319.070 data/arf_070.dat -a 0.1 -e 1.3 0.1 -c
```

### 3. Calculate for all files of a given directory

Find all pair of UV and B files in a directory and run calculations for each them.
Calculations will be skipped if UVR and ARF files are not available.

**Examples:**

Run the calculations for all the files found in the `data` directory and write the output to the `output` directory:
```
python run_cmd.py --all data/ -o output/
```
Note that `--input-dir` has no effect for this command.

### 4. Watchdog

Monitor a directory for new files and run the calculation for every new/modified pair of UV and B files.
Calculations will be skipped if UVR and ARF files are not available.

```
python run_cmd.py --watch --input-dir measurements/
```
Note that if `--input-dir` is not specified, the measurement files will be taken from `data/`.

## Installer

`installer.py` is a small script to help deploy the docker UV Server image.

**Instructions:**

`installer.py` requires python 3+.
To run the script:
```
python installer.py
```
or on linux simply:
```
./installer.py
```
Then follow the instructions on terminal


## Releases

Releases have a version in the form `vMAJOR.MINOR` (e.g `v1.2`).

To create a new release, change the version in the [version file](version).
Then, create a new tag with the version as a name:
```
git tag v1.2 -a -m "UV Server v1.2"
```
and push it to github:
```
git push --tags
```
Docker hub will automatically build the corresponding docker image (Note: it can take a few hours until the images are built).

Alternatively, you can run the script `release.py` which will do these steps automatically.

## Docker

Two docker images are available for calculations:
1. `pec0ra/uv-server`: A small web app to help launching calculations
2. `pec0ra/uv-watch`: A watchdog to automatically execute the calculations when files are changed in a directory

### 1. UV Server

This docker image contains the UV Web Application (See section above)

**Instructions:**

See the [Installer section](#installer) for an easier way to run this docker image.

To build this image, run:
```
docker build -f Dockerfile.server . -t pec0ra/uv-server
```
Note that the tag `pec0ra/uv-server` can be replaced with another custom tag


To start a docker container, run:
```
docker run -d -p <PORT>:80 --name uv-server pec0ra/uv-server
```
Where `<PORT>` is the port on which the web app will listen (e.g. 8080).

The flag `-d` tells docker to run this container as a daemon (in the background). It may be omitted if you want to run it in your current terminal.

After running this command, you can access the web app in your browser at `http://localhost:<PORT>`

If you want [darksky](https://darksky.net/dev) to be used, you will need to create an account and give your api key as environment variable.
This can be done by adding the parameter `-e DARKSKY_TOKEN=your_darksky_token`.
Example:
```
docker run -d -p <PORT>:80 -e DARKSKY_TOKEN=your_darksky_token --name uv-server pec0ra/uv-server
```

If you want to use a custom directory as a source for measurement files and/or for output files, you can mount the container's `/data` and `/out` as volumes:
```
docker run -d -p <PORT>:80 <MEASUREMENT_PATH>:/data -v <OUT_PATH>:/out --user $(id -u):$(id -g) --name uv-server pec0ra/uv-server
```
where `<MEASUREMENT_PATH>` is the *absolute* path to your measurement and `<OUT_PATH>` is the *absolute* path to the directory you want to save the outputs in.

The `--user $(id -u):$(id -g)` option tells docker to run the container as the current user.
This prevents permissions issues at the moment of writing files to the output directory.
You might need to skip this option on Windows.


### 2. UV Watch

This docker image contains the UV Watchdog

**Instructions:**

To build this image, run:
```
docker build -f Dockerfile.watch . -t pec0ra/uv-watch
```
Note that the tag `pec0ra/uv-watch` can be replaced with another custom tag


To start a docker container, run:
```
docker run --d -v <WATCH_PATH>:/in -v <OUT_PATH>:/out --user $(id -u):$(id -g) --name uv-watch pec0ra/uv-watch
```
Where:

`<WATCH_PATH>` is the *absolute* path to the directory you want to monitor

`<OUT_PATH>` is the directory in which to save the generated csv files

The flag `-d` tells docker to run this container as a daemon (in the background).
It may be ommited if you want to run it in your current terminal.

The `--user $(id -u):$(id -g)` option tells docker to run the container as the current user.
This prevents permissions issues at the moment of writing files to the output directory.
You might need to skip this option on Windows.

After running this command, any new pair of UV and B files added/modified in `<WATCH_PATH>` will automatically be converted an irradiance spectrum saved in `<OUT_PATH>`


## Implementation

For this implementation section, we will split the functionality of the application in the following parts:

1. User Interface
2. Job creation / handling
3. Calculations


![Technical details](assets/technical_detail_1.png)

### 1. User Interface

Two user interfaces are available:
1. Command line interface (CLI)
2. Graphical User Interface (GUI)

Both interfaces are responsible for getting the necessary parameters from the user.
The parameters include dates and brewer id to find the required files for the calculations as well as some default values for ozone, abledo
and aerosol for the case where these cannot be found in the files.


The first interface's implementation is written in [`run_cmd.py`](run_cmd.py) and mostly consists of command line argument parsing.
Once the arguments are parsed, their values are passed to the `CalculationUtils` (See [next section](#2-job-creation--handling)).

The second interface's implementation is more complex and consists of the following three files:
1. [`run.py`](run.py) (or [`docker/run_docker.py`](docker/run_docker.py) for the docker image) which serves as an entry point to start the UVApp.
2. [`uv/app.py`](uv/app.py) which contains the UVApp class.
3. [`uv/gui/widgets.py`](uv/gui/widgets.py) which contains the implementation of some of the more complex interface's widgets.

The UVApp class is the core of the GUI and uses the [remi library](https://github.com/dddomodossola/remi).
The class initializes the widgets in its `main` method and adds them to its main container.

The most important of the interface's widgets are the `MainForm`s (`PathMainForm` to give files as input and `SimpleMainForm` to give dates
and brewer id as input). They keep track of the values of their fields and of the extra parameters and call the `CalculationUtils` (See
[next section](#2-job-creation--handling)) with these values when the *Calculate* button is clicked.


### 2. Job creation / handling

Job creation and handling is done in the class [`CalculationUtils`](uv/logic/calculation_utils.py).

Before creating the jobs, all the information required for the Jobs is written in a `CalculationInput` object.
Each `CalculationInput` corresponds to one UV file (measurements for one day). Since multiple measurements are done each day (in each UV
file), the UV file is divided into sections, each represented as a `UVFileEntry` object.
In the end, one Job will be created for each `UVFileEntry`. Each Job needs therefore to get a `CalculationInput` as parameter as well as the
index of the section it does the calculation for.

Jobs can be created in four different ways:
1. `calculate_for_input`: Create jobs for a given `CalculationInput`. Used when file paths are already known.
2. `calculate_for_all_between`: Finds all the files for measurements between two days and create the jobs for them.
3. `calculate_for_all`: Finds all files in a directory and create the jobs for them
4. `watch`: Monitors a directory and each time a file is found, calls `calculate_for_input`.

The difference between way 1. (and 4.) and ways 2. and 3. is that way 1 only create Jobs for one `CalculationInput`.
Ways 2. and 3. make calculation for multiple days and therefore create Jobs for multiple `CalculationInput` objects.

All the Jobs are then scheduled on a `ThreadPoolExecutor` and will run in parallel.
Their results will then be scheduled on a `ProcessPoolExecutor` for the generation of qasume and plot files.


### 3. Calculations

The calculations executed in each Job from the [previous section](#2-job-creation--handling) are mostly implemented in
[`IrradianceCalculation`](uv/logic/irradiance_calculation.py).
The entry point in this class for the calculations is the method `calculate` as explained in the [previous section](#2-job-creation--handling),
this method has access to a `CalculationInput` object for infos about the measurement files and extra parameters as well as the index of the
section to do the calculations for.

![Calculation workflow](assets/technical_detail_2.png)

The first part of the calculations is to parse the measurement files to get the data from. Each file type has its own file parser. Their
implementations can be found in the files [`uv/logic/uv_file.py`](uv/logic/uv_file.py), [`uv/logic/b_file.py`](uv/logic/b_file.py),
[`uv/logic/arf_file.py`](uv/logic/arf_file.py), [`uv/logic/calibration_file.py`](uv/logic/calibration_file.py) and
[`uv/logic/parameter_file.py`](uv/logic/parameter_file.py).

Note that the file parsing is triggered automatically (and cached) when calling one of the following property on the `CalculationInput`:
* `uv_file_entries`: parses the uv file
* `ozone`: parses the b file
* `calibration`: parses the calibration file
* `arf`: parses the arf file
* `parameters`: parses the parameter file

In addition to parsing the files, an api call is made to [darksky.net](https://darksky.net/dev) to get the cloud cover for the day of the
measurements. This information is used to choose between a clear sky or a diffuse cos correction.

In the next step, the raw measurements and the calibration data is used to convert the raw UV measurements to a calibrated spectrum.
A call to LibRadtran is also made with the infos from the measurement and parameter files to get `Fdiff`, `Fdir` and `Fglo`.

Finally, the results from LibRadtran and from the darksky.net api call are used to apply the cos correction to the calibrated
spectrum.
This information as well as the input parameters used is returned from the `calculate` method as a `Result` object.
