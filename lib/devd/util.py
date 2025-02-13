from typing import Any, Tuple, Callable
import logging
import sys
from datetime import datetime, timezone


def setup_logging(**kwargs):
    kwargs = {
        "stream": sys.stderr,
        "level": logging.INFO,
        "format": "%(asctime)s %(message)s",
        "datefmt": "%Y-%m-%dT%H:%M:%S%z",
    } | kwargs
    logging.basicConfig(**kwargs)


def with_timing(
    fun: Callable[[], Any],
    tz: timezone | None = None,
) -> Tuple[Any, Exception | None, datetime, datetime, float]:
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
