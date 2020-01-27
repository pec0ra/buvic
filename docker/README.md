<img src="https://raw.githubusercontent.com/pec0ra/buvic/master/assets/logo_github_header.png" width="100%" >

# Brewer UV Irradiance Calculation

Brewer UV Irradiance Calculation (BUVIC) is a tool to calculate the cosine corrected irradiance from brewer raw UV measurements.

A more complete documentation can be found on [BUVIC's wiki](https://github.com/pec0ra/buvic/wiki)

## Requirements

Docker needs to be installed in order to run this tool

### Directory structure

BUVIC needs access to three main directories:
1. An instrument directory (e.g. `instr`)
2. A uv data directory (e.g. `uvdata`)
3. An output directory (e.g. `output_dir`)

The instrument directory is where you put your instrument files. 
```
instr/
    arf_033.dat
    arf_070.dat
    ...
    UVR17319.070
    UVR17319.117
    UVR17419.033
    ...
    par_18.033
    par_18.070
    par_19.033
    par_19.070
    ...
```
It contains:
*   ARF files with the name pattern `arf_<brewer_id>.dat`
*   Calibration files with the name pattern `UVRXXXXX.<brewer_id>`
*   Parameter files with the name pattern `par_<year>.<brewer_id>` where *year* is the last two digits of the year (e.g. 19)

The uv data directory is where you put your measurement files.
```
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
It contains:
*   B files with the name pattern `B<days><year>.<brewer_id>` where *days* is the number of days since new year and *year* is the last two
digits of the year (e.g. 19)
*   UV files with the name pattern `UV<days><year>.<brewer_id>` where *days* is the number of days since new year and *year* is the last two
digits of the year (e.g. 19)

Inside the instrument and uv data directories, you may use any directory structure that you want.
The files will be searched recursively into this structure.

Example of more complex structure:
```
instr/
    033/
        arf_033.dat
        UVR17419.033
        par_18.033
        par_19.033
    070/
        arf_070.dat
        UVR17019.070
        UVR17319.070
        par_18.070
        par_19.070
    ...

uvdata/
    033/
        2018/
            B17018.033
            UV17018.033
            ...
        2019/
            B17019.033
            B17119.033
            UV17019.033
            UV17119.033
            ...
    070/
        2018/
            B17018.070
            UV17018.070
            ...
        2019/
            B17019.070
            B17119.070
            UV17019.070
            UV17119.070
            ...
    ...
```

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

Here is an example of a parameter file content `par_19.033`:
```
10;0.1;1;0.1;
11;;1.2;0.2;1
12;0.3;;;0
14;0.5;1.5;0.5;
```

#### Output files

The output files are in the qasume format.
Their names have the following pattern: `<days><hour><minute>.<brewer_id>` and are placed in subdirectories with instrument id and year as
names. In the file name pattern, *days* is the number of days since new year and *hour* and *minute* is the time of the measurement.

Each qasume file begins with four header lines, each beginning with `% `.
The first header line contains information about the file generation.
The second header line contains the place of the measurement with its name, latitude and longitude.
The third line gives information about the parameter used for calculation. Each info has the format `<name>=<value>` and infos are
separated by a tabulation.
The value for `coscor` is followed by the cloud coverage in parenthesis if this value was taken from [darksky](https://darksky.net/dev).
The fourth line contains the headers for the three columns of data.

After the header, the following rows contain the data. Each row contains three values separated by white spaces: the wavelength, the spectral
irradiance and the time of the measurement (see the third line of the header for more details).

Here is an example of a (truncated) qasume file `1751130G.117`:
```
% Generated with Brewer UV Irradiance Calculation v2.1 at 2019-12-13 12:48:17
% El Arenosillo 37.1N 6.73W
% type=ua	coscor=clear_sky(darksky:0.67)	tempcor=false	straylightcor=false	o3=312.1DU	albedo=0.04	alpha=1.3	beta=0.1
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

The best way to run this image is with the [installer](#installer) or with [docker-compose](#docker-compose)

### Installer

[`installer.py`](https://github.com/pec0ra/buvic/blob/master/installer.py) is a small script to help deploy the docker UV Server image.

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

**Upgrading BUVIC**

To upgrade, just run the installer again and choose the version you want.

### Docker Compose

It is possible to use [Docker Compose](https://docs.docker.com/compose/) to easily configure and start BUVIC's docker image.

**Instructions:**

Docker Compose needs to be installed first.
If you use Windows or Mac, you are lucky because Docker Compose comes preinstalled with docker.
If you use another OS, see the [install instructions](https://docs.docker.com/compose/install/).

Clone [BUVIC's repository](https://github.com/pec0ra/buvic) or download the
[`docker-compose.yml`](https://github.com/pec0ra/buvic/blob/master/docker/docker-compose.yml) file:

```yaml
version: '3.7'

volumes:
  buvic-settings:

services:
  app:
    image: pmodwrc/buvic:latest
    container_name: buvic
    ports:
      # Change the port you want BUVIC to listen to (default: 80). Value must be <LISTENING_PORT>:4444
      - 80:4444
    volumes:
      - buvic-settings:/settings

      # Adapt the path to your instrument files
      - ../data/instr:/instr

      # Adapt the path to your uv files
      - ../data/uvdata/:/uvdata

      # Adapt the path for your output files
      - ../out:/out
    environment:
      # Uncomment next line if you want to use darksky
      #- DARKSKY_TOKEN=yourdarkskytoken

      - PORT=4444

    # Uncomment next line to allow giving the user to run the image in environment variable `CURRENT_UID` (value must be `<user_id>:<group_id>'
    #user: ${CURRENT_UID}

    # Uncomment next line to run the image with given another user id and group id
    #user: 1000:1000

    # Uncomment this line if you want the image to start at boot
    #restart: always

    init: true
```

Open a terminal and navigate to the directory where the `docker-compose.yml` file is (it's in `docker/` if you cloned the repository)
and make the needed changes (see comments).

Then run
```
docker-compose up -d
```
The option `-d` tells docker-compose to run as a daemon (in the background). If you want the image to run in the terminal, skip this option.

**Upgrading BUVIC**

To upgrade BUVIC, run the following commands in the same directory as the `docker-compose.yml` file:
```shell script
docker-compose down
docker pull pmodwrc/buvic
docker-compose up
```

#### Demo command

The simplest way to start a docker container with buvic is to run:
```
docker run -d -p <HOST_PORT>:80 --name buvic pmodwrc/buvic
```
Where `<HOST_PORT>` is the port on which the web app will listen (e.g. 8080).

The flag `-d` tells docker to run this container as a daemon (in the background). It may be omitted if you want to run it in your current terminal.

After running this command, you can access the web app in your browser at `http://localhost:<HOST_PORT>`.
This instance of BUVIC however only uses some demo measurement files as input.

#### Mapping directories

To use BUVIC correctly, you will need to map input and output directories of your host machine to your docker container.

There are three relevant directories that need to be mapped (see [Directory structure](#directory-structure) for more details):
1. `/instr`
2. `/uvdata`
3. `/out`

Each of these directories needs to be mapped to a directory on your host computer.
We use docker volumes (the option `-v`) to map a host directory to a docker directory.
When mapping a host directory (e.g. `/home/user/buvic_data`) to a docker directory (e.g. `/path/in/docker/buvic_data`), the directory inside
the docker container will share the contents of the host directory.

Here is an example of command which maps host directories to `/instr`, `/uvdata` and `/out`:
```
docker run -d -p <HOST_PORT>:80 -v <INSTR_DIRECTORY>:/instr -v <UVDATA_DIRECTORY>:/uvdata -v <OUTPUT_DIRECTORY>:/out --name buvic pmodwrc/buvic
```
where `<INSTR_DIRECTORY>` is the *absolute* path to the instrument directory on the host (e.g. `D:\buvic\instr` on Windows or
`/home/user/buvic/instr` on Linux), `<UVDATA_DIRECTORY>` is the *absolute* path to the uv data directory on the host and `<OUTPUT_DIRECTORY>`
is the *absolute* path to the directory you want to save the outputs in.

#### Permissions

On linux machines, you may want to specify which user/group runs the docker container to avoid permission issues when writing to the output
directory.
This can be done with the parameter `--user <user_id>:<group_id>` or simply `--user $(id -u):$(id -g)` to use the current user and group.

Note that if you use another user than root, you will not get permission to listen to port 80 (the default port for buvic inside the
container).
A workaround for this is to specify on which port buvic will listen with the environment variable `PORT`. This is done by adding the
following parameter to your docker run command 
```-e PORT=<PORT_NUMBER>```
where `<PORT_NUMBER>` is the port number to use (must be greater than 1024 for non root users).

Example:
```
docker run -d -p <HOST_PORT>:4444 --user 1000:1000 -e PORT=4444 --name buvic pmodwrc/buvic
```
Notice that for the `-p` option, we don't use 80 anymore but the port specified with the `PORT` environment variable (4444 in this example).

#### Darksky

If you want [darksky](https://darksky.net/dev) to be used, you will need to create an account and give your api key as environment variable.
Using this functionality is not required and the cloud coverage values can be manually entered in the parameter file instead.

You can pass your darksky api token to BUVIC by adding the parameter `-e DARKSKY_TOKEN=your_darksky_token`.
Example:
```
docker run -d -p <HOST_PORT>:80 -e DARKSKY_TOKEN=your_darksky_token --name buvic pmodwrc/buvic
```
