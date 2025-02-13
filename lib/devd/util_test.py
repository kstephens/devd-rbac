from . import util as sut


def test_pairs():
    items = (1, 2, 3)
    assert sut.pairs(items) == [(1, 2), (1, 3), (2, 3)]
    assert sut.pairs(items, 0) == [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (3, 3)]
