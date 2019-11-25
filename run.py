import os

from remi import start

from uv.app import UVApp
from uv.const import TMP_FILE_DIR, PLOT_DIR

if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)


# starts the web server
start(UVApp)
