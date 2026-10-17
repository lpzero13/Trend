"""Provider-independent data contracts shared by chart and headless research."""
from dataclasses import dataclass
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


class DataError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class Bar:
    time: int
    end: int
    open: float
    high: float
    low: float
    close: float
    volume: float
