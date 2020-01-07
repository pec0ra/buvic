import logging
import os

from remi import start

from buvic.app import BUVIC
from buvic.const import TMP_FILE_DIR, OUTPUT_DIR
from buvic.logutils import init_logging

if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

port = 80
if "PORT" in os.environ:
    port = int(os.environ['PORT'])

init_logging(logging.DEBUG)

# starts the web server
start(BUVIC, address='0.0.0.0', port=port, start_browser=False, multiple_instance=True)
