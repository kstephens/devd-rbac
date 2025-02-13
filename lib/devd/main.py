"""
devd.main - basic command line interface
"""

from typing import List  # ,Any, Self, Callable, Literal, Tuple, cast

# from dataclasses import dataclass, field
# from pathlib import Path
import sys

# import os
# import copy
import json

# import yaml
import logging

# from icecream import ic
from .app import App
from .util import setup_logging, with_timing


def main(argv: List[str], **kwargs):
    progname, *args = argv

    def run_app():
        setup_logging()
        return App(args=args, **kwargs).run()

    result, exc, t0, t1, elasped_sec = with_timing(run_app)
    if result is not None:
        result, error, exit_code = result
    else:
        result = error = exit_code = None
    if exc is not None and error is None:
        if exit_code is None:
            exit_code = 1
        error = {
            "class": error.__class__.__name__,
            "message": str(exc),
            "backtrace": [],
        }
    elif error is not None:
        error = {
            "class": error.__class__.__name__,
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
    if exc is not None:
        logging.error("%s", f"{progname}: EXCEPTION")
    json.dump(response, fp=sys.stdout, indent=2)
    print("", file=sys.stdout)
    return exit_code
