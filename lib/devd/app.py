"""
devd.app - implement App.run()
"""

from typing import (
    Any,
    List,
    Tuple,
    Dict,
)  #  , Self, Any,Callable, Literal, Tuple, cast


Result = Any
Error = Any
ExitCode = int | None
AppResponse = Tuple[Result, Error, ExitCode]


class App:
    def __init__(self, args: List[str], opts: Dict[str, Any], main_opts: dict):
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
        arg0 = self.args and self.args[0]
        if arg0 == "EXCEPTION":
            raise ValueError("App.run: EXCEPTION")
        if arg0 == "FAIL":
            return "App.run: FAIL", arg0, None
        if arg0 == "EXIT-2":
            return "App.run: EXIT-2", None, 2
        # raise NotImplemented("App.run")
        return "App.run: OK", None, None

    def __call__(self):
        return self.run()
