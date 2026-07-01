import httpx
import pytest

from demo_project.api.dependencies import azure_scheme
from demo_project.core.config import settings
from demo_project.main import app
from fastapi_azure_auth import B2CMultiTenantAuthorizationCodeBearer
from tests.utils import build_openid_keys, keys_url, openid_config_url, openid_configuration


@pytest.fixture
def multi_tenant_app():
    azure_scheme_overrides = generate_azure_scheme_multi_tenant_b2c_object()
    app.dependency_overrides[azure_scheme] = azure_scheme_overrides
    yield


@pytest.fixture
def mock_openid(respx_mock):
    respx_mock.get(openid_config_url(multi_tenant=True)).respond(json=openid_configuration())
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
    openid_route = respx_mock.get(openid_config_url(multi_tenant=True))
    openid_route.side_effect = [
        httpx.Response(json=openid_configuration(), status_code=200),
        httpx.Response(json=openid_configuration(), status_code=200),
    ]
    yield


@pytest.fixture
def mock_openid_and_no_valid_keys(respx_mock, mock_openid):
    respx_mock.get(keys_url()).respond(json=build_openid_keys(no_valid_keys=True))
    yield


def generate_azure_scheme_multi_tenant_b2c_object(issuer=None):
    """
    This method is used just to generate the Multi Tenant B2C Obj
    """

    async def issuer_fetcher(tid):
        tids = {'vibber_tenant_id': 'https://login.microsoftonline.com/vibber_tenant/v2.0'}
        return tids[tid]

    current_issuer = issuer_fetcher
    if issuer:
        current_issuer = issuer
    return B2CMultiTenantAuthorizationCodeBearer(
        app_client_id=settings.APP_CLIENT_ID,
        openapi_authorization_url=str(settings.AUTH_URL),
        openapi_token_url=str(settings.TOKEN_URL),
        # The value below is used only for testing purpose you should use:
        # https://login.microsoftonline.com/common/v2.0/oauth2/token
        openid_config_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
        scopes={
            f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'User impersonation',
        },
        validate_iss=True,
        iss_callable=current_issuer,
    )
