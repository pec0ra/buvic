# UV irradiance calculations


This repository contains a set of tools to calculate the cosine corrected irradiance from raw UV measurements.


## Requirements

All python commands required python >= 3.7 and the libraries listed in [requirements.txt](requirements.txt).
These libraries can be installed with the pip command:
```
pip install -r requirements.txt
```

The Docker images require docker


## UV Web Application

UV Web Application is a small application running in the browser to facilitate the execution of irradiance calculation.

It offers the possibility to choose a date and a brewer id to automatically find the measurement files from a predefined set or to manually upload measurement files (manual mode).

**Instructions:**

Run:
```
python run.py
```
The application should automatically open in the browser.

## Command line app

The command line offers 4 different possibilities to perform irradiance calculations.

1. Calculate for a date and brewer id
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
                  (--days-and-brewer-id DAYS BREWER_ID | --paths UV_FILE B_FILE UVR_FILE ARF_FILE | --all | --watch)
                  [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]
                  [--albedo ALBEDO] [--aerosol ALPHA BETA] [--only-csv]

Calculate irradiance spectra

optional arguments:
  -h, --help            show this help message and exit
  --days-and-brewer-id DAYS BREWER_ID, -d DAYS BREWER_ID
                        The date, represented as the days since new year, and
                        the id of the brewer to get the data from
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
                        The directory get the files from
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        The directory to save the results in
  --albedo ALBEDO, -a ALBEDO
                        The albedo value to use for the calculations
  --aerosol ALPHA BETA, -e ALPHA BETA
                        The aerosol angstrom's alhpa and beta values to use
                        for the calculations.
  --only-csv, -c        Don't generate plots but only csv files
```
The options `--days-and-brewer-id`, `--paths`, `--all` and `--watch` correspond to the 4 different ways to run the tool and only one can be used at a time.

The options `--input-dir`, `--output-dir`, `--albedo`, `--aerosol` and `--only-csv` are optional parameters and can be used with any of the 4 options cited above. If not specified, default values will be used.

### 1. Calculate for a date and brewer id

This command search for measurements matching a date and a brewer id from a preset of files.
The date is given as the number of days since new year (January 1st is 1)

**Examples:**

Run the calculation for brewer `070` on June 26th and write the output in the `brewer117` directory:
```
python run_cmd.py --days-and-brewer-id 177 070 --output-dir brewer177/
```

Run the calculation for brewer `186` on June 25th with an albedo of 0.1 and angström's alpha of 1.3 and beta of 0.1 as aerosol (using shortcuts flags `-d`, `-a` and `-e` instead of their full versions). The `-c` parameter (or `--only-csv`) tells that we don't want to generate plots but only csv files
```
python run_cmd.py -d 175 186 -a 0.1 -e 1.3 0.1 -c
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



## Docker

Two docker images are available for calculations:
1. `pec0ra/uv-server`: A small web app to help launching calculations
2. `pec0ra/uv-watch`: A watchdog to automatically execute the calculations when files are changed in a directory

### 1. UV Server

This docker image contains the UV Web Application (See section above)

**Instructions:**

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

The flag `-d` tells docker to run this container as a daemon (in the background). It may be ommited if you want to run it in your current terminal.

After running this command, you can access the web app in your browser at `http://localhost:<PORT>`




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
