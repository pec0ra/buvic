# Python code

This directory contains most of the python code of BUVIC.

The code is separated in two directories:
1. [`gui`](gui): The code related to the user interface
2. [`logic`](logic): The backend code doing all the data collecting and calculations

In addition, the following files are present in this directory:
* [`const.py`](const.py): Some constants and global variables
* [`libradtran_command.py`](libradtran_command.py): Contains only the command used to call libradtran.
  In the docker version of BUVIC, this file is overwritten by [`../docker/libradtran_command.py`](../docker/libradtran_command.py)
* [`logutils.py`](logutils.py): A small utility to initialize logging