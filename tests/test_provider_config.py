from datetime import datetime, timedelta

import anyio
import httpx
import pytest
from asgi_lifespan import LifespanManager
from httpx2 import ASGITransport, AsyncClient

from demo_project.api.dependencies import azure_scheme
from demo_project.main import app
from fastapi_azure_auth.openid_config import OpenIdConfig
from tests.utils import build_access_token, build_openid_keys, keys_url, openid_config_url, openid_configuration


@pytest.mark.anyio
async def test_http_error_old_config_found(httpx2_mock, mock_config_timestamp):
    azure_scheme.openid_config._config_timestamp = datetime.now() - timedelta(weeks=1)
    httpx2_mock.get('https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration').respond(
        status_code=500
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': f'Bearer {build_access_token()}'},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': 'Connection to Azure Entra ID is down. Unable to fetch provider configuration'}


@pytest.mark.anyio
async def test_http_error_no_config_cause_crash_on_startup(httpx2_mock):
    httpx2_mock.get('https://login.microsoftonline.com/vibber_tenant_id/v2.0/.well-known/openid-configuration').respond(
        status_code=500
    )
    with pytest.raises(RuntimeError):
        async with LifespanManager(app=app):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url='http://test',
                headers={'Authorization': f'Bearer {build_access_token()}'},
            ) as ac:
                await ac.get('api/v1/hello')


@pytest.mark.anyio
async def test_app_id_provided(httpx2_mock):
    openid_config = OpenIdConfig('vibber_tenant', multi_tenant=False, app_id='1234567890')
    httpx2_mock.get(
        'https://login.microsoftonline.com/vibber_tenant/v2.0/.well-known/openid-configuration?appid=1234567890'
    ).respond(json=openid_configuration())
    httpx2_mock.get('https://login.microsoftonline.com/vibber_tenant/discovery/v2.0/keys').respond(
        json=build_openid_keys()
    )
    await openid_config.load_config()
    assert len(openid_config.signing_keys) == 2


@pytest.mark.anyio
async def test_custom_config_id(httpx2_mock):
    openid_config = OpenIdConfig(
        'vibber_tenant',
        multi_tenant=False,
        config_url='https://login.microsoftonline.com/override_tenant/v2.0/.well-known/openid-configuration',
    )
    httpx2_mock.get('https://login.microsoftonline.com/override_tenant/v2.0/.well-known/openid-configuration').respond(
        json=openid_configuration()
    )
    httpx2_mock.get('https://login.microsoftonline.com/vibber_tenant/discovery/v2.0/keys').respond(
        json=build_openid_keys()
    )
    await openid_config.load_config()
    assert len(openid_config.signing_keys) == 2


@pytest.mark.anyio
async def test_concurrent_refresh_requests(httpx2_mock):
    """Concurrent refreshes of a stale config should result in exactly one fetch."""

    # respx requires classic httpx.Response objects from side_effect callables (lundberg/respx#324)
    async def slow_config_response(*args, **kwargs):
        await anyio.sleep(0.2)
        return httpx.Response(200, json=openid_configuration())

    async def slow_keys_response(*args, **kwargs):
        await anyio.sleep(0.2)
        return httpx.Response(200, json=build_openid_keys())

    config_route = httpx2_mock.get(openid_config_url()).mock(side_effect=slow_config_response)
    keys_route = httpx2_mock.get(keys_url()).mock(side_effect=slow_keys_response)

    openid_config = OpenIdConfig('vibber_tenant_id')
    async with anyio.create_task_group() as task_group:
        for _ in range(5):
            task_group.start_soon(openid_config.load_config)

    assert len(config_route.calls) == 1, 'Config endpoint called multiple times'
    assert len(keys_route.calls) == 1, 'Keys endpoint called multiple times'
    assert len(openid_config.signing_keys) == 2
