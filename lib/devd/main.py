"""
devd.main - basic command line interface
"""

from typing import Any, List, Dict  # ,Any, Self, Callable, Literal, Tuple, cast
import sys
import re
import json
import logging
from pathlib import Path
from . import app
from . import util
from .util import setup_logging, with_timing, WithTimingResult, backtrace_list

# from dataclasses import dataclass, field
# from pathlib import Path
# import os
# import copy
# import yaml
# from icecream import ic


main_opts: Dict[str, Any] = {}


def main(argv: List[str], opts: Dict[str, Any]) -> int:
    _progname, *args = argv
    util.lib_dir = Path(main_opts.get("lib_dir") or ".").absolute()

    # Parse arg
    while args:
        arg = args[0]
        if arg == "--":
            args.pop(0)
            break
        if m := re.search(r"^--([a-z][-a-z]+)=(.*)", arg):
            opts[m[1].replace("-", "_")] = m[2]
            args.pop(0)
        else:
            break

    def run_app():
        setup_logging()
        return app.App(args=args, opts=opts, main_opts=main_opts).run()

    response = process_result(with_timing(run_app))
    json.dump(response, fp=sys.stdout, indent=2)
    print("", file=sys.stdout)
    return response["exit_code"]


def process_result(with_timing_result: WithTimingResult):
    result, exc, t0, t1, elasped_sec = with_timing_result
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
            "backtrace": backtrace_list(exc),
        }
    elif error is not None:
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
        "elapsed_ms": round(elasped_sec * 1000, 2),
    }
    if error:
        logging.error("%s", f"{error['class']} {error['message']}")
    return response
