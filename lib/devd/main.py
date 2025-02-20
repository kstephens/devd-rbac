"""
devd.main - basic command line interface
"""

from typing import Any, List, Dict
from pathlib import Path
import os
import icecream
from . import app
from . import util
from .util import (
    setup_logging,
    with_log_collection,
    with_timing,
    parse_args,
    process_result,
    output_response,
    Args,
    Opts,
)

icecream.install()
icecream.ic.configureOutput(includeContext=True)

defaults = {
    "log_format": "json",
    "output_format": "json",  # "yaml", "none"
    "capture_logs": True,
}


class Main:
    argv: Args
    args: Args
    opts: Opts

    def __init__(self, argv: Args, opts: Opts):
        opts = (
            defaults
            | {
                "argv": argv,
                "argv0": argv[0],
                "pid": os.getpid(),
                "uid": os.getuid(),
                "gid": os.getgid(),
                "prog_name": Path(argv[0]).name,
            }
            | opts
        )
        self.argv, self.opts = argv, opts
        self.progname, *self.args = argv
        self.log_records: List[Any] = []

    def run(self) -> int:
        util.lib_dir = Path(self.opts.get("lib_dir") or ".").absolute()
        response = self.run_app()
        # !!! TypeError: Object of type PosixPath is not JSON serializable
        # response["main_opts"] = self.opts
        output_response(response, self.opts["output_format"])
        return response["exit_code"]

    def make_app(self):
        args, opts = parse_args(self.args, {})
        return app.App(args=args, opts=opts, main_opts=self.opts)

    def run_app(self):
        setup_logging(formatter=self.opts["log_format"])

        def execute_app():
            return process_result(with_timing(self.make_app().run))

        if self.opts["capture_logs"]:
            log_records = []

            def execute_app_and_logs():
                response = execute_app()
                response["logs"] = log_records
                return response

            return with_log_collection(log_records.append, execute_app_and_logs)

        return execute_app()


def main(argv: List[str], opts: Dict[str, Any]) -> int:
    return Main(argv, opts).run()
