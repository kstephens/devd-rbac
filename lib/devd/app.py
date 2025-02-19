"""
devd.app - implement App.run()
"""

from typing import (
    Any,
    List,
    Tuple,
    Dict,
)  #  , Self, Any,Callable, Literal, Tuple, cast
from .rbac import api

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
        if self.args == ["rbac", "api", "run"]:
            return api.main(*self.args, **self.opts)
        return None, f"Invalid command: {self.args}", 1

    def __call__(self):
        return self.run()
