import cads_catalogue


def test_version() -> None:
    assert cads_catalogue.__version__ != "999"
