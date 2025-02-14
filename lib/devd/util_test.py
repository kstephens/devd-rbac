from time import sleep
from datetime import datetime
from . import util as sut


def test_pairs():
    items = (1, 2, 3)
    assert sut.pairs(items) == [(1, 2), (1, 3), (2, 3)]
    assert sut.pairs(items, 0) == [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (3, 3)]


def test_with_timing():
    def f():
        sleep(0.5)
        return 2

    result, exc, t0, t1, dt_sec = sut.with_timing(f)
    assert result == 2
    assert exc is None
    assert isinstance(t0, datetime)
    assert isinstance(t1, datetime)
    assert t1 > t0
    assert dt_sec > 0.4

    def g():
        sleep(0.5)
        raise ValueError("nope")

    result, exc, t0, t1, dt_sec = sut.with_timing(g)
    assert result is None
    assert isinstance(exc, ValueError)
