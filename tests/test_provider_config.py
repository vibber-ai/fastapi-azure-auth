import logging
from datetime import datetime, timedelta

import pytest
from asgi_lifespan import LifespanManager
from httpx2 import ASGITransport, AsyncClient

from demo_project.api.dependencies import azure_scheme
from demo_project.main import app
from fastapi_azure_auth import HttpClientConfig, SingleTenantAzureAuthorizationCodeBearer
from fastapi_azure_auth.openid_config import OpenIdConfig
from tests.utils import build_access_token, build_openid_keys, openid_configuration


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


def _capture_client_kwargs(mocker):
    """Patch the AsyncClient used for config fetching so the kwargs it receives can be asserted."""
    import fastapi_azure_auth.openid_config as openid_config_module

    captured = {}
    real_client = openid_config_module.AsyncClient

    def capture(**kwargs):
        captured.update(kwargs)
        return real_client(**kwargs)

    mocker.patch.object(openid_config_module, 'AsyncClient', side_effect=capture)
    return captured


@pytest.mark.anyio
async def test_http_client_config_passed_to_client(httpx2_mock, mocker):
    captured = _capture_client_kwargs(mocker)
    openid_config = OpenIdConfig('vibber_tenant', http_client_config={'trust_env': False, 'timeout': 30})
    httpx2_mock.get('https://login.microsoftonline.com/vibber_tenant/v2.0/.well-known/openid-configuration').respond(
        json=openid_configuration()
    )
    httpx2_mock.get('https://login.microsoftonline.com/vibber_tenant/discovery/v2.0/keys').respond(
        json=build_openid_keys()
    )
    await openid_config.load_config()
    assert captured == {'timeout': 30, 'trust_env': False}
    assert len(openid_config.signing_keys) == 2


@pytest.mark.anyio
async def test_http_client_config_defaults_to_ten_second_timeout(httpx2_mock, mocker):
    captured = _capture_client_kwargs(mocker)
    openid_config = OpenIdConfig('vibber_tenant')
    httpx2_mock.get('https://login.microsoftonline.com/vibber_tenant/v2.0/.well-known/openid-configuration').respond(
        json=openid_configuration()
    )
    httpx2_mock.get('https://login.microsoftonline.com/vibber_tenant/discovery/v2.0/keys').respond(
        json=build_openid_keys()
    )
    await openid_config.load_config()
    assert captured == {'timeout': 10}


def test_http_client_config_unknown_key_raises_at_construction():
    with pytest.raises(ValueError, match='Unsupported http_client_config key'):
        OpenIdConfig('vibber_tenant', http_client_config={'proxy': 'http://localhost:8080'})


def test_http_client_config_verify_false_warns(caplog):
    with caplog.at_level(logging.WARNING, logger='fastapi_azure_auth'):
        OpenIdConfig('vibber_tenant', http_client_config={'verify': False})
    assert 'TLS certificate verification is disabled' in caplog.text


def test_http_client_config_is_copied_at_construction():
    config: HttpClientConfig = {'trust_env': False}
    openid_config = OpenIdConfig('vibber_tenant', http_client_config=config)
    config['trust_env'] = True
    assert openid_config.http_client_config == {'trust_env': False}


def test_http_client_config_passed_through_scheme():
    scheme = SingleTenantAzureAuthorizationCodeBearer(
        app_client_id='client-id',
        tenant_id='vibber_tenant',
        http_client_config={'trust_env': False},
    )
    assert scheme.openid_config.http_client_config == {'trust_env': False}
