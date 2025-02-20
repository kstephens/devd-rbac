from typing import Any, List, Dict, Tuple, Callable, Iterable, Generator
import logging
import sys
import re
import traceback
from pathlib import Path
from datetime import datetime, timezone
import json
import yaml
from pythonjsonlogger.json import JsonFormatter


lib_dir: Path = Path(".")


Args = List[str]
Opts = Dict[str, Any]


def parse_args(args: Args, opts: Opts) -> Tuple[Args, Opts]:
    """Dead simple --option=value parser."""
    args, opts = args.copy(), opts.copy()
    while args:
        arg = args.pop(0)
        if arg == "--":
            break
        if m := re.search(r"^--([a-z][-a-z]+)=(.*)", arg):
            opts[m[1].replace("-", "_")] = m[2]
        else:
            args.append(arg)
            break
    return args, opts


def output_response(response: Any, fmt: str, stream=None):
    if stream is None:
        stream = sys.stdout
    if fmt == "json":
        json.dump(response, fp=stream, indent=2)
        print("", file=sys.stdout)
    elif fmt == "yaml":
        yaml.dump(response, stream=stream)
    elif fmt != "none":
        print(repr(response), file=stream)


#############################################


def setup_logging(**kwargs):
    kwargs = {
        "stream": sys.stderr,
        "level": logging.INFO,
        "format": "%(asctime)s %(levelname)-8s %(message)s",
        "datefmt": "%Y-%m-%dT%H:%M:%S%z",
    } | kwargs
    formatter = kwargs.pop("formatter", None)
    logging.basicConfig(**kwargs)
    if formatter:
        if formatter == "json":
            formatter = JsonFormatter(
                "{created}{asctime}{process}{name}{levelname}{message}",
                style="{",
            )
        set_logger_formatter(logging.getLogger(), formatter)
        for log in all_loggers():
            set_logger_formatter(log, formatter)


def set_logger_formatter(logger, formatter):
    for handler in logger.handlers:
        handler.setFormatter(formatter)


def all_loggers():
    # E1101: Instance of 'RootLogger' has no 'loggerDict' member (no-member)
    # pylint: disable-next=no-member
    return [logging.getLogger(name) for name in logging.root.manager.loggerDict]


#############################################

LoggingCallback = Callable[[logging.LogRecord], None]


class LoggingCallbackHandler(logging.Handler):
    def __init__(self, callback: LoggingCallback, level: int = logging.INFO):
        super().__init__()
        self.callback = callback
        self.level = level
        self.filters = []
        self.lock = None

    def emit(self, record):
        try:
            basic = [
                record.asctime,
                # record.created,
                record.levelname,
                record.name,
                record.message,
            ]
            self.callback(basic)
        except (KeyboardInterrupt, SystemExit):
            raise
        # pylint: disable-next=bare-except
        except:
            self.handleError(record)


def with_log_collection(callback: LoggingCallback, proc: Callable) -> Any:
    logger = logging.getLogger()
    handler = LoggingCallbackHandler(callback)
    try:
        logger.addHandler(handler)
        return proc()
    finally:
        logger.removeHandler(handler)


#############################################

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


def process_result(with_timing_result: WithTimingResult) -> dict:
    result, exc, t0, t1, elapsed_sec = with_timing_result
    # app.AppResponse
    if result is None:
        result = error = exit_code = None
    else:
        result, error, exit_code = result
    if exc is not None and error is None:
        if exit_code is None:
            exit_code = 1
        error = {
            "class": exc.__class__.__name__,
            "message": str(exc),
            "backtrace": [f"{file}:{line}" for file, line in backtrace_list(exc)],
        }
    elif error is not None:
        if exit_code is None:
            exit_code = 1
        error = {
            "class": None,  # error.__class__.__name__,
            "message": str(error),
            "backtrace": [],
        }
    if exit_code is None:
        exit_code = 0
    response = {
        "result": result,
        "error": error,
        "exit_code": exit_code,
        "started_at": t0.isoformat(),
        "stopped_at": t1.isoformat(),
        "elapsed_ms": round(elapsed_sec * 1000, 2),
    }
    if error:
        logging.error("%s", f"{error['class']} : {error['message']}")
    return response


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


#############################################

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
