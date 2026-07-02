import pytest

from demo_project.api.dependencies import azure_scheme
from demo_project.main import app


def pytest_collection_modifyitems(items):
    """
    Shared mock fixtures register routes (e.g. the keys endpoint) that not every
    test calls, so don't require all mocked routes to have been hit on teardown.
    """
    for item in items:
        item.add_marker(pytest.mark.httpx2(assert_all_called=False))


@pytest.fixture(autouse=True)
def mock_config_timestamp():
    """
    Make sure the timestamp and any dependency overrides are reset between every test,
    so the order tests run in can't leak configuration between them.
    """
    azure_scheme.openid_config._config_timestamp = None
    yield
    app.dependency_overrides = {}
