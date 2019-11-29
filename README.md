# UV irradiance calculations

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
