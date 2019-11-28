import logging
import os

from remi import start

from uv.app import UVApp
from uv.const import TMP_FILE_DIR, OUTPUT_DIR
from uv.logutils import init_logging

if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

init_logging(logging.INFO)

# starts the web server
start(UVApp, multiple_instance=True)
