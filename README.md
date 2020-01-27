![BUVIC](assets/logo_github_header.png)

[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![GitHub top language](https://img.shields.io/github/languages/top/pec0ra/buvic)](https://github.com/pec0ra/buvic/search?l=Python)
[![GitHub](https://img.shields.io/github/license/pec0ra/buvic)](https://www.gnu.org/licenses/gpl-3.0) 
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/pec0ra/buvic)](https://github.com/pec0ra/buvic/releases/)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/pec0ra/buvic/Python%20checks)](https://github.com/pec0ra/buvic/actions)
[![Docker Cloud Automated build](https://img.shields.io/docker/cloud/automated/pmodwrc/buvic)](https://hub.docker.com/r/pmodwrc/buvic/builds)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Brewer UV Irradiance Calculation

BUVIC is a small application running in the browser that executes calculations of cosine corrected irradiance from brewer raw UV measurements.

It can execute these calculations for chosen dates and brewer id and the corresponding measurement can either be read from the file system
or retrieved from eubrewnet.

![GUI](assets/gui.png)

![GUI](assets/gui2.png)

## Usage

To install BUVIC, run the [`installer.py`](installer.py) and follow the instructions. This requires python 3+.
```
python installer.py
```

More information about how to use BUVIC can be found in the [wiki](https://github.com/pec0ra/buvic/wiki/Usage)

## Documentation

Information about BUVIC's usage and implementation can be found in the [wiki](https://github.com/pec0ra/buvic/wiki)

*   [Home](https://github.com/pec0ra/buvic/wiki)
*   [About](https://github.com/pec0ra/buvic/wiki/About)
*   [Usage](https://github.com/pec0ra/buvic/wiki/Usage)
    *   [Requirements](https://github.com/pec0ra/buvic/wiki/Usage%3A-Requirements)
    *   [Docker](https://github.com/pec0ra/buvic/wiki/Usage%3A-Docker)
    *   [Python App](https://github.com/pec0ra/buvic/wiki/Usage%3A-Python-App)
    *   [Settings](https://github.com/pec0ra/buvic/wiki/Usage%3A-Settings)
*   [Contributing](https://github.com/pec0ra/buvic/wiki/Contributing)
    *   [License](https://github.com/pec0ra/buvic/wiki/Contributing%3A-License)
    *   [Code Style](https://github.com/pec0ra/buvic/wiki/Contributing%3A-Code-Style)
    *   [Releases](https://github.com/pec0ra/buvic/wiki/Contributing%3A-Releases)
    *   [Implementation Details](https://github.com/pec0ra/buvic/wiki/Contributing%3A-Implementation-Details)
    *   [Adding Data Sources](https://github.com/pec0ra/buvic/wiki/Contributing%3A-Adding-Data-Sources)
    *   [Adding Output Formats](https://github.com/pec0ra/buvic/wiki/Contributing%3A-Adding-Output-Formats)

## License

BUVIC is published under the `GNU General Public License version 3` (GPL v3). See [LICENSE.md](LICENSE.md) for more details.
