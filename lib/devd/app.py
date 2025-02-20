"""
devd.app - implement App.run()
"""

from typing import Any, Tuple
import logging
from .util import Args, Opts

Result = Any
Error = Any
ExitCode = int | None
AppResponse = Tuple[Result, Error, ExitCode]


class App:
    def __init__(self, args: Args, opts: Opts, main_opts: dict):
        self.args = args
        self.opts = opts
        self.main_opts = main_opts

    def run(self) -> AppResponse:
        """
        - response can be any value
        - error can be any value or None.
        - uncaught exceptions are to be handled by the caller.
        - exit_code defaults to the error and exception handling of the caller.
        """
        return self.run_demo()

    def __call__(self):
        return self.run()

    ###############################################################

    def run_demo(self) -> AppResponse:
        logging.info("%s", f"App.run_demo: {self.args=}")
        arg0 = self.args and self.args[0]
        if arg0 == "EXCEPTION":
            raise ValueError("App.run_demo: EXCEPTION")
        if arg0 == "FAIL":
            return "App.run: FAIL", arg0, None
        if arg0 == "EXIT-2":
            return "App.run: EXIT-2", None, 2
        # raise NotImplemented("App.run")
        return "App.run_demo: OK", None, None
