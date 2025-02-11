from . import main as sut


def test_main():
    assert sut.f() is True
