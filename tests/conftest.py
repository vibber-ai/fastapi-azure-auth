import pytest

from demo_project.api.dependencies import azure_scheme
from demo_project.main import app


@pytest.fixture(autouse=True)
def mock_config_timestamp():
    """
    Make sure the timestamp and any dependency overrides are reset between every test,
    so the order tests run in can't leak configuration between them.
    """
    azure_scheme.openid_config._config_timestamp = None
    yield
    app.dependency_overrides = {}
