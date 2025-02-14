from typing import Any, List, Tuple, Callable
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone


lib_dir: Path = Path(".")


def pairs(items: list, offset: int = 1) -> List[Tuple[Any, Any]]:
    return [
        (items[i], items[j])
        for i in range(len(items))
        for j in range(i + offset, len(items))
    ]


def setup_logging(**kwargs):
    kwargs = {
        "stream": sys.stderr,
        "level": logging.INFO,
        "format": "%(asctime)s %(levelname)-8s %(message)s",
        "datefmt": "%Y-%m-%dT%H:%M:%S%z",
    } | kwargs
    logging.basicConfig(**kwargs)


WithTimingResult = Tuple[Any, Exception | None, datetime, datetime, float]


def with_timing(
    fun: Callable[[], Any],
    tz: timezone | None = None,
) -> WithTimingResult:
    tz = tz or timezone.utc
    t0 = datetime.now(tz)
    result = exc = None
    try:
        result = fun()
    # pylint: disable-next=broad-exception-caught
    except Exception as e:
        exc = e
    t1 = datetime.now(tz)
    return result, exc, t0, t1, (t1 - t0).total_seconds()


Backtrace = List[Tuple[str, int]]


def backtrace_list(exc: BaseException) -> Backtrace:
    trb = exc.__traceback__
    trb_extracted = traceback.extract_tb(trb)
    return [
        (
            str(frame.filename).removeprefix(str(lib_dir) + "/"),
            frame.lineno or 0,
        )
        for frame in trb_extracted
    ]
