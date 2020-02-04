import multiprocessing

import progressbar

from buvic.logic.progress_handler import ProgressHandler


class CMDProgressHandler(ProgressHandler):
    widgets = [
        " ",
        progressbar.RotatingMarker(),
        " ",
        progressbar.Percentage(),
        " ",
        progressbar.Bar("#", "[", "]"),
        " | ",
        progressbar.Timer(),
        " | ",
        progressbar.ETA(),
    ]
    progress_bar = progressbar.ProgressBar(initial_value=0, min_value=0, max_value=0, widgets=widgets)
    lock = multiprocessing.Manager().Lock()

    def init_progress(self, total: int, legend: str = "Calculating..."):
        del legend  # Remove unused variable
        self.progress_bar.start(total)
        self.progress_bar.update(0)

    def finish_progress(self, duration: float):
        del duration  # Remove unused variable
        self.progress_bar.finish()

    def progress(self):
        if self.progress_bar is not None:
            with self.lock:
                self.progress_bar.update(self.progress_bar.value + 1)
