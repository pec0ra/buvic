class ProgressHandler:

    duration: float = 0

    def init_progress(self, total: int, legend: str = "Calculating..."):
        raise NotImplementedError("Method must be implemented in sub class")

    def progress(self):
        raise NotImplementedError("Method must be implemented in sub class")

    def finish_progress(self, duration: float):
        self.duration = duration
