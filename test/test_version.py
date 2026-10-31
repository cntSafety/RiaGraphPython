def test_version() -> None:
    import riag as lb

    assert lb.version != ""
    assert lb.storage_version > 0
    assert lb.version == lb.__version__
