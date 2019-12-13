# Brewer UV Irradiance Calculation

Brewer UV Irradiance Calculation (BUVIC) is a tool to calculate the cosine corrected irradiance from brewer raw UV measurements.

## Requirements

Docker needs to be installed in order to run this tool


### Directory structure

BUVIC needs access to two main directories:
1. An input directory (e.g. `input_dir`)
2. An output directory (e.g. `output_dir`)

The input directory is where you put your instrument files and your measurement files. It must have the following structure:
```
instr/
    arf_033.dat
    arf_070.dat
    ...
    UVR17319.070
    UVR17319.117
    UVR17419.033
    ...
    19.par
uvdata/
    B17019.033
    B17019.070
    B17119.033
    B17119.070
    ...
    UV17019.033
    UV17019.070
    UV17119.033
    UV17119.070
    ...
```

In the `instr` directory:
* ARF files with the name pattern `arf_<brewer_id>.dat`
* Calibration files with the name pattern `UVRXXXXX.<brewer_id>`
* Parameter files with the name patter `<year>.par` where *year* is the last two digits of the year (e.g. 19)

In the `uvdata` directory:
* B files with the name pattern `B<days><year>.<brewer_id>` where *days* is the number of days since new year and *year* is the last two
digits of the year (e.g. 19)
* UV files with the name pattern `UV<days><year>.<brewer_id>` where *days* is the number of days since new year and *year* is the last two
digits of the year (e.g. 19)

The output directory is the place where BUVIC will write its output files. BUVIC will automatically create a structure to group files by year.


### File formats

#### Parameter files

The parameter files are composed of multiple rows, where each row is composed of five values separated by a semicolon (`;`).

The first value of each row is the day since new year, the second value is the albedo, the third and fourth values are the angstrom's
alpha and beta of the aerosol and the fifth value is the cloud coverage (0 for no cloud and 1 for cloudy).

In the first line of the file, only the cloud coverage is optional. The other values cannot be empty.
For the following lines, the albedo, alpha and beta values can be omitted. If this is the case, the value of the last line with non empty value
is used.
If the cloud coverage is omitted in any line, the value will be retrieved from the [darksky](https://darksky.net/dev) api.

Here is an example of a parameter file content `19.par`:
```
10;0.1;1;0.1;
11;;1.2;0.2;1
12;0.3;;;0
14;0.5;1.5;0.5;
```


#### Output files

The output files are in the qasume format.
Their names have the following pattern: `<days><hour><minute>.<brewer_id>` and are placed in a subdirectory with the year of the measurement
as name. In the name pattern, *days* is the number of days since new year and *hour* and *minute* is the time of the measurement.

Each qasume file begins with four header lines, each beginning with `% `.
The first header line contains information about this software
The second header line contains the place of the measurement with its name, latitude and longitude.
The third line gives information about the parameter used for calculation. Each info has the format `<name>=<value>` and infos are
separated by a tabulation.
The value for `coscor` is followed by the cloud coverage in parenthesis if this value was taken from [darksky](https://darksky.net/dev).
The fourth line contains the headers for the three columns of data.

After the header, the following rows contain the data. Each row contains three values separated by white spaces: the wavelength, the spectral
irradiance and the time of the measurement (see the third line of the header for more details).

Here is an example of a (truncated) qasume file `1751130G.117`:
```
% Generated with Brewer UV Irradiance Calculation v2.1
% El Arenosillo 37.1N 6.73W
% type=ua	coscor=clear_sky(0.67)	tempcor=false	straylightcor=false	o3=312.1DU	albedo=0.04	alpha=1.3	beta=0.1
% wavelength(nm)	spectral_irradiance(W m-2 nm-1)	time_hour_UTC
290.0	 0.000001157	   11.50033
290.5	 0.000000000	   11.50133
291.0	 0.000000000	   11.50217
291.5	 0.000001131	   11.50300
292.0	 0.000008208	   11.50383
292.5	 0.000051625	   11.50467
293.0	 0.000050769	   11.50550
293.5	 0.000090523	   11.50633
294.0	 0.000153403	   11.50717
294.5	 0.000206659	   11.50800
295.0	 0.000307826	   11.50883
...
```



## Instructions


The simplest way to start a docker container with buvic is to run:
```
docker run -d -p <PORT>:80 --name buvic pmodwrc/buvic
```
Where `<PORT>` is the port on which the web app will listen (e.g. 8080).

The flag `-d` tells docker to run this container as a daemon (in the background). It may be omitted if you want to run it in your current terminal.

After running this command, you can access the web app in your browser at `http://localhost:<PORT>`.
This instance of BUVIC however only uses some demo measurement files as input.

To use BUVIC correctly, you will need to map an input directory and an output directory to your docker container.
In the docker image, the input directory is at `/data` and the output directory is at `/out`.
We need to map these two directories to two directories on your computer.
We use docker volumes (the option `-v`) to map a host directory to a docker directory (it works similarly to links).
```
docker run -d -p <PORT>:80 -v <INPUT_DIRECTORY>:/data -v <OUTPUT_DIRECTORY>:/out --user $(id -u):$(id -g) --name buvic pmodwrc/buvic
```
where `<INPUT_DIRECTORY>` is the *absolute* path to your input directory (e.g. `D:\buvic\input_dir` on Windows or `/home/user/buvic/input_dir`
on Linux) and `<OUTPUT_DIRECTORY>` is the *absolute* path to the directory you want to save the outputs in.

The `--user $(id -u):$(id -g)` option tells docker to run the container as the current user.
This prevents permissions issues at the moment of writing files to the output directory.
It is optional and you might need to skip it on Windows.


If you want [darksky](https://darksky.net/dev) to be used, you will need to create an account and give your api key as environment variable.
Using this functionality is not required and the cloud coverage values can be manually entered in the parameter file instead.

You can pass your darksky api token to BUVIC by adding the parameter `-e DARKSKY_TOKEN=your_darksky_token`.
Example:
```
docker run -d -p <PORT>:80 -e DARKSKY_TOKEN=your_darksky_token --name buvic pmodwrc/buvic
```
