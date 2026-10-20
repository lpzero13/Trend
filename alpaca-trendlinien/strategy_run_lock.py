"""One OS-owned writer per study directory; release survives worker termination."""
from contextlib import contextmanager
import os
from pathlib import Path

from models import DataError


@contextmanager
def study_lock(output):
    root = Path(output).expanduser().resolve()
    root.parent.mkdir(parents=True, exist_ok=True)
    path = root.parent/("."+root.name+".safety.lock")
    with path.open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise DataError("Ein anderer Prozess bearbeitet diesen Strategieauftrag.", 409) from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
