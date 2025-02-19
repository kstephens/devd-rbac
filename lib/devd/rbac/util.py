# Cribbed from:
# devdriven/path.py
# devdriven/glob.py

from typing import Any, Callable, Iterable, List
import re

Composable = Callable[..., Any]
Composable1 = Callable[[Any], Any]


def find(pred: Callable[[Any], bool], seq: Iterable, default: Any = None) -> Any:
    for item in seq:
        if pred(item):
            return item
    return default


def getter(name: str) -> Composable1:
    return lambda obj: getattr(obj, name)


def mapcat(func: Callable[[Any], Iterable], seq: Iterable) -> Iterable:
    result: List = []
    for item in seq:
        result.extend(func(item))
    return result


def cartesian_product(dims: Iterable[Iterable[Any]]) -> Iterable[Iterable[Any]]:
    def collect(dims, rows):
        if not dims:
            return rows
        new = []
        for row in rows:
            for val in dims[0]:
                new.append(append_one(row, val))
        return collect(dims[1:], new)

    dims = tuple(dims)
    return collect(dims[1:], [[val] for val in dims[0]])


def append_one(x: list, y: Any) -> list:
    x = x.copy()
    x.append(y)
    return x


def comp1(f: Composable1, g: Composable1) -> Composable1:
    return lambda x: f(g(x))


def comp(f: Composable1, g: Composable) -> Composable:
    return lambda *args: f(g(*args))


# See: devdriven/path.py


def clean_path(path: str) -> str:
    prev = None
    while path != prev:
        prev = path
        path = re.sub(r"//+", "/", path)
        path = re.sub(r"^\./", "", path)
        path = re.sub(r"^\.\.(?:$|/)", "", path, 1)
        path = re.sub(r"(:?^/)\./", "/", path)
        path = re.sub(r"^/\.\.(?:$|/)", "/", path, 1)
        path = re.sub(r"^[^/]+/\.\.(?:$|/)", "", path, 1)
        path = re.sub(r"/[^/]+/\.\./", "/", path, 1)
    return path


# See: devdriven/glob.py

GLOB_RX = re.compile(
    r"(?P<dot>\.)|(?P<char>\?)|"  # +
    r"(?P<star_star>(?P<pre_star_star>^|/)\*\*)|"  # +
    r"(?P<begin_star>(?P<pre_star>^|/)\*)|(?P<star>\*)"  #
)


def glob_to_regex(glob: str, deep_matches_empty: bool = False) -> re.Pattern:
    def scan(m: re.Match):
        # print(repr(m.groupdict()))
        if m["dot"]:
            return r"\."
        if m["char"]:
            return r"[^/.]"
        if m["star_star"]:
            if deep_matches_empty:
                return m["pre_star_star"] + r".*?"
            return m["pre_star_star"] + r".+?"
        if m["begin_star"]:
            return m["pre_star"] + r"(?![./])[^/]*"
        if m["star"]:
            return r"(?:[^/]*)"
        assert not "here"
        return None

    return re.compile("^(?:" + re.sub(GLOB_RX, scan, glob) + ")$")
