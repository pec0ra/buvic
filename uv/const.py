TMP_FILE_DIR = "tmp/"
OUTPUT_DIR = "out/"
DATA_DIR = "data/"

UV_FILES_SUBDIR = "uvdata/"
B_FILES_SUBDIR = "uvdata/"
CALIBRATION_FILES_SUBDIR = "instr/"
ARF_FILES_SUBDIR = "instr/"
PARAMETER_FILES_SUBDIR = "instr/"

DEFAULT_ALBEDO_VALUE = 0.04
DEFAULT_ALPHA_VALUE = 1.3
DEFAULT_BETA_VALUE = 0.1
DEFAULT_OZONE_VALUE = 300

with open("version") as version_file:
    APP_VERSION = version_file.readline().strip()
