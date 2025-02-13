"""
devd.app - implement run()
"""

from typing import (
    Any,
    List,
    Tuple,
)  #  , Self, Any, Dict  # , Callable, Literal, Tuple, cast


# (result, error, exit_code)
AppResponse = Tuple[Any, Any | None, int | None]


class App:
    def __init__(self, args: List[str]):
        self.args = args

    def run(self) -> AppResponse:
        """
        - response can be any value
        - error can be any value or None.
        - uncaught exceptions are to be handled by the caller.
        - exit_code defaults to the error and exception handling of the caller.
        """
        arg0 = self.args and self.args[0]
        if arg0 == "EXCEPTION":
            raise ValueError("EXCEPTION")
        if arg0 == "FAIL":
            return "App.run", arg0, None
        if arg0 == "EXIT":
            return "App.run", None, 2
        # raise NotImplemented("App.run")
        return "App.run", None, None

    def __call__(self):
        return self.run()
