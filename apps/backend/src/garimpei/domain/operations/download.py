from collections.abc import Callable
from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True)
class ArchiveDownload:
    stream: BinaryIO
    size: int
    sha256: str
    close: Callable[[], None]
