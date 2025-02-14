from typing import Any, List, Tuple, Callable, Iterable, Generator
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone


lib_dir: Path = Path(".")


# Generator[yield_type, send_type, return_type]
PairsGenerator = Generator[Tuple[Any, Any], None, None]


def pairs_generator(items: Iterable, inclusive: bool = False) -> PairsGenerator:
    """
    Generates unique 2-tuples pairing each item with another.
    This is effectively the triangular matrix of the cross product.
    When inclusive is true, identity elements are present: e.g. ("a", "a").
    """
    offset = 0 if inclusive else -1
    i = 0
    for a in items:
        j = 0
        for b in items:
            if j + offset >= i:
                yield a, b
            j += 1
        i += 1


def pairs(items: Iterable, inclusive: bool = False) -> Iterable[Tuple[Any, Any]]:
    """See pairs_generator."""
    return list(pairs_generator(items, inclusive))


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
