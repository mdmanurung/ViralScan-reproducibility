import pytest


def pytest_addoption(parser):
    parser.addoption("--stage", type=int, default=0, help="run target-state tests for stages <= N (they must be green); default 0 = regression only")
    parser.addoption("--slow", action="store_true", help="also run the package and repro suites (minutes)")


def pytest_configure(config):
    config.addinivalue_line("markers", "stage(n): target-state test that turns green when stage n is done")
    config.addinivalue_line("markers", "slow: runs a full suite")


def pytest_collection_modifyitems(config, items):
    n = config.getoption("--stage")
    skip_slow = pytest.mark.skip(reason="needs --slow")
    for it in items:
        m = it.get_closest_marker("stage")
        if m is not None and m.args[0] > n:
            it.add_marker(pytest.mark.skip(reason=f"stage {m.args[0]} > --stage {n}"))
        if it.get_closest_marker("slow") and not config.getoption("--slow"):
            it.add_marker(skip_slow)
