import httpx
import pytest

from demo_project.api.dependencies import azure_scheme
from demo_project.core.config import settings
from demo_project.main import app
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from tests.utils import build_openid_keys, keys_url, openid_config_url, openid_configuration


@pytest.fixture
def single_tenant_app():
    """
    Single tenant app fixture
    """
    azure_scheme_overrides = SingleTenantAzureAuthorizationCodeBearer(
        app_client_id=settings.APP_CLIENT_ID,
        scopes={
            f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'User impersonation',
        },
        tenant_id=settings.TENANT_ID,
    )
    app.dependency_overrides[azure_scheme] = azure_scheme_overrides
    yield


@pytest.fixture
def mock_openid(respx_mock):
    respx_mock.get(openid_config_url()).respond(json=openid_configuration())
    yield


@pytest.fixture
def mock_openid_and_keys(respx_mock, mock_openid):
    respx_mock.get(keys_url()).respond(json=build_openid_keys())
    yield


@pytest.fixture
def mock_openid_and_empty_keys(respx_mock, mock_openid):
    respx_mock.get(keys_url()).respond(json=build_openid_keys(empty_keys=True))
    yield


@pytest.fixture
def mock_openid_ok_then_empty(respx_mock, mock_openid):
    keys_route = respx_mock.get(keys_url())
    keys_route.side_effect = [
        httpx.Response(json=build_openid_keys(), status_code=200),
        httpx.Response(json=build_openid_keys(empty_keys=True), status_code=200),
    ]
    openid_route = respx_mock.get(openid_config_url())
    openid_route.side_effect = [
        httpx.Response(json=openid_configuration(), status_code=200),
        httpx.Response(json=openid_configuration(), status_code=200),
    ]
    yield


@pytest.fixture
def mock_openid_and_no_valid_keys(respx_mock, mock_openid):
    respx_mock.get(keys_url()).respond(json=build_openid_keys(no_valid_keys=True))
    yield
