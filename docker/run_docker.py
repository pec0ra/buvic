import os
import sys

from remi import start

from uv.app import UVApp
from uv.const import TMP_FILE_DIR, PLOT_DIR

if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

port = 80
if len(sys.argv) > 1:
    port = int(sys.argv[1])

# starts the web server
start(UVApp, address='0.0.0.0', port=port, start_browser=False, multiple_instance=True)
