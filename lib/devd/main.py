from typing import Any, Self, Callable, List, Dict, Iterable
import re
import os
import sys
import json
from icecream import ic


def f() -> bool:
    print([Any, Self, Callable, List, Dict, Iterable])
    print(re)
    print(os)
    print(json)
    ic("HERE")
    return True


def main(argv):
    prog, *args = argv
    ic(prog)
    ic(args)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
