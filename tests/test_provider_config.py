from datetime import datetime, timedelta

import pytest
from asgi_lifespan import LifespanManager
from demo_project.api.dependencies import azure_scheme
from demo_project.main import app
from httpx import AsyncClient
from tests.utils import build_access_token, build_openid_keys, openid_configuration

from fastapi_azure_auth.openid_config import OpenIdConfig


@pytest.mark.anyio
async def test_http_error_old_config_found(respx_mock, mock_config_timestamp):
    azure_scheme.openid_config._config_timestamp = datetime.now() - timedelta(weeks=1)
    respx_mock.get('https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration').respond(
        status_code=500
    )
    async with AsyncClient(
        app=app, base_url='http://test', headers={'Authorization': f'Bearer {build_access_token()}'}
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': 'Connection to Azure Entra ID is down. Unable to fetch provider configuration'}


@pytest.mark.anyio
async def test_http_error_no_config_cause_crash_on_startup(respx_mock):
    respx_mock.get('https://login.microsoftonline.com/vibber_tenant_id/v2.0/.well-known/openid-configuration').respond(
        status_code=500
    )
    with pytest.raises(RuntimeError):
        async with LifespanManager(app=app):
            async with AsyncClient(
                app=app, base_url='http://test', headers={'Authorization': f'Bearer {build_access_token()}'}
            ) as ac:
                await ac.get('api/v1/hello')


@pytest.mark.anyio
async def test_app_id_provided(respx_mock):
    openid_config = OpenIdConfig('vibber_tenant', multi_tenant=False, app_id='1234567890')
    respx_mock.get(
        'https://login.microsoftonline.com/vibber_tenant/v2.0/.well-known/openid-configuration?appid=1234567890'
    ).respond(json=openid_configuration())
    respx_mock.get('https://login.microsoftonline.com/vibber_tenant/discovery/v2.0/keys').respond(
        json=build_openid_keys()
    )
    await openid_config.load_config()
    assert len(openid_config.signing_keys) == 2


@pytest.mark.anyio
async def test_custom_config_id(respx_mock):
    openid_config = OpenIdConfig(
        'vibber_tenant',
        multi_tenant=False,
        config_url='https://login.microsoftonline.com/override_tenant/v2.0/.well-known/openid-configuration',
    )
    respx_mock.get('https://login.microsoftonline.com/override_tenant/v2.0/.well-known/openid-configuration').respond(
        json=openid_configuration()
    )
    respx_mock.get('https://login.microsoftonline.com/vibber_tenant/discovery/v2.0/keys').respond(
        json=build_openid_keys()
    )
    await openid_config.load_config()
    assert len(openid_config.signing_keys) == 2
