import logging
import os
import sys

from remi import start

from uv.app import UVApp
from uv.const import TMP_FILE_DIR, OUTPUT_DIR
from uv.logutils import init_logging

if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

port = 80
if len(sys.argv) > 1:
    port = int(sys.argv[1])

init_logging(logging.DEBUG)

# starts the web server
start(UVApp, address='0.0.0.0', port=port, start_browser=False, multiple_instance=True)
