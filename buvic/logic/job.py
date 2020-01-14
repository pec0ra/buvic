from dataclasses import dataclass
from typing import Generic, Callable, TypeVar

INPUT = TypeVar("INPUT")
RETURN = TypeVar("RETURN")


@dataclass
class Job(Generic[INPUT, RETURN]):
    _fn: Callable[[INPUT], RETURN]
    _args: INPUT

    def run(self) -> RETURN:
        """
        Execute the job
        :return: the job's return value
        """
        return self._fn(self._args)  # type: ignore
