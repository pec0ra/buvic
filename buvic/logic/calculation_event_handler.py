import re
from logging import getLogger
from typing import Callable

from watchdog.events import FileSystemEventHandler, FileSystemMovedEvent, FileSystemEvent

from buvic.logic.settings import Settings

LOG = getLogger(__name__)


class CalculationEventHandler(FileSystemEventHandler):
    ACCEPTED_FILE_REGEX = re.compile(r".*(?P<file_type>B|UV)(?P<days>\d{3})(?P<year>\d{2})\.(?P<brewer_id>\d{3})$")

    def __init__(self, on_new_file: Callable[[str, str, str, str, Settings], None], settings: Settings):
        self._on_new_file = on_new_file
        self._parameters = settings

    def on_modified(self, event):
        self._on_created_or_modified(event)

    def on_moved(self, event: FileSystemMovedEvent):
        self._on_created_or_modified(event)

    def _on_created_or_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return

        if isinstance(event, FileSystemMovedEvent):
            file_path = event.dest_path
        else:
            file_path = event.src_path

        res = self.ACCEPTED_FILE_REGEX.match(file_path)
        if res:
            LOG.info("File matched for event " + type(event).__name__)
            file_type = res.group("file_type")
            days = res.group("days")
            year = res.group("year")
            brewer_id = res.group("brewer_id")
            try:
                self._on_new_file(file_type, days, year, brewer_id, self._parameters)
            except Exception:
                LOG.error("An error occurred while handling file", exc_info=True)
