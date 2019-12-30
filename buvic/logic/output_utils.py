from os import path, makedirs
from pathlib import Path
from threading import Lock

from buvic.logic.result import Result

lock = Lock()


def create_csv(saving_dir: str, result: Result) -> str:
    file_name = result.get_name()

    full_path = Path(path.join(saving_dir, file_name))

    with lock:
        if not path.exists(full_path.parent):
            makedirs(full_path.parent)

    with open(full_path, "w") as csv_file:
        result.to_qasume(csv_file)
    return file_name
